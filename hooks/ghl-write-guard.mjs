#!/usr/bin/env node
// ghl-write-guard.mjs
// -----------------------------------------------------------------------------
// PreToolUse guard for GHL social WRITES. Enforces the composite-key isolation
// rule (docs/ghl-social-integration.md): a post may only target accounts on the
// working channel's allowlist, identified by (platform + native id) — never by
// platform. Blocks any write whose target account id is not authorised.
//
// Wired in settings.json for matcher `mcp__ghl-social-write__.*`, so it fires
// only on calls to the write MCP server (dormant until that server is added).
//
// FAIL CLOSED. Claude Code hooks fail OPEN by default (bad output / exit 1 /
// timeout => the tool proceeds). This guard therefore:
//   - blocks a policy violation with exit 0 + deny JSON (clean reason to Claude);
//   - blocks on ANY error/uncertainty with exit 2 (the hard block);
//   - stays SILENT (exit 0, no output) only when a call is provably authorised,
//     so it never auto-approves — your normal permission prompt still applies.
//
// Scope: enforces on calls that carry target account ids (create/schedule posts).
// Calls without account targets (search/describe) pass through. Delete-by-postId
// ops are out of scope for now [TBD when a delete path is built].
// No dependencies (Node stdlib).
// -----------------------------------------------------------------------------
import { execFileSync } from 'node:child_process';
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import process from 'node:process';

const die = (msg) => { console.error(`ghl-write-guard: ${msg}`); process.exit(2); }; // fail closed
const deny = (reason) => {
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: { hookEventName: 'PreToolUse', permissionDecision: 'deny', permissionDecisionReason: reason },
  }));
  process.exit(0);
};
const allow = () => process.exit(0); // silent — no decision, normal permission flow proceeds

function repoRoot() {
  try {
    const out = execFileSync('git', ['rev-parse', '--show-toplevel'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
    if (out) return resolve(out);
  } catch { /* fall back */ }
  return resolve(process.cwd());
}

// Collect target account ids anywhere in the tool input (grouped or flat).
function collectTargets(node, out) {
  if (Array.isArray(node)) { for (const x of node) collectTargets(x, out); return; }
  if (node && typeof node === 'object') {
    for (const [k, v] of Object.entries(node)) {
      if (k === 'accountIds' && Array.isArray(v)) v.forEach((id) => typeof id === 'string' && out.add(id));
      else if (k === 'accountId' && typeof v === 'string') out.add(v);
      else collectTargets(v, out);
    }
  }
}

// Authorised native ids from a single channel's distribution.yaml (comment lines skipped).
function nativeIdsFromChannel(file) {
  const ids = new Set();
  for (const line of readFileSync(file, 'utf8').split('\n')) {
    if (/^\s*#/.test(line)) continue;
    const m = line.match(/\bnative_id\s*:\s*["']?([^"'\s#]+)/);
    if (m) ids.add(m[1]);
  }
  return ids;
}

function main() {
  let payload;
  try { payload = JSON.parse(readFileSync(0, 'utf8')); }
  catch { die('could not parse hook stdin'); }

  const toolInput = payload?.tool_input ?? {};
  const targets = new Set();
  try { collectTargets(toolInput, targets); } catch { die('could not read tool input'); }

  // No account-targeted write => nothing to authorise (search/describe/etc.).
  if (targets.size === 0) allow();

  // Load channel allowlists. Missing/unreadable => fail closed.
  const root = repoRoot();
  const channelsDir = join(root, 'channels');
  let channelFiles;
  try {
    channelFiles = existsSync(channelsDir)
      ? readdirSync(channelsDir).map((d) => join(channelsDir, d, 'distribution.yaml')).filter(existsSync)
      : [];
  } catch { die('could not enumerate channels'); }

  if (channelFiles.length === 0) die('no channel distribution.yaml allowlist found');
  if (channelFiles.length > 1) {
    // Multi-channel active-selection isn't built yet; refuse rather than risk cross-channel posting.
    deny('Write blocked: multiple channels present but no per-channel active-selection is implemented yet. '
      + 'Refusing to avoid posting to another channel\'s accounts. Build the active-channel selector before multi-channel writes.');
  }

  let authorised;
  try { authorised = nativeIdsFromChannel(channelFiles[0]); } catch { die('could not read channel allowlist'); }
  if (authorised.size === 0) die('channel allowlist has no native_id entries');

  const bad = [...targets].filter((t) => ![...authorised].some((nid) => t.includes(nid)));
  if (bad.length > 0) {
    deny(`Write blocked by the composite-key guard: target account id(s) not on this channel's allowlist — ${bad.join(', ')}. `
      + 'A GHL destination is identified by (platform + specific native id), NEVER by platform. '
      + `Authorise the intended account in ${channelFiles[0].replace(root + '/', '')} (and confirm it is the right one), or select the correct account id. `
      + 'See docs/ghl-social-integration.md.');
  }

  allow(); // all targets authorised — stay silent, let normal permission flow proceed
}

try { main(); } catch (e) { die(`unexpected error: ${e && e.message}`); }
