#!/usr/bin/env node
// ghl-mcp-headers.mjs
// -----------------------------------------------------------------------------
// headersHelper for the GHL social MCP servers (see .mcp.json).
//
// WHY THIS EXISTS — the whole story, so no future session re-diagnoses it:
//   Claude Code expands `${VAR}` in .mcp.json from the PROCESS ENVIRONMENT only.
//   It does NOT load the project .env for that substitution (verified: absent from
//   the process env at launch AND after a full restart; a `${GHL_SOCIAL_READ_PIT}`
//   header therefore resolved to an empty Bearer -> "Invalid JWT"). Meanwhile every
//   OTHER secret consumer in this repo (the image/music/video skills' load_api_key,
//   the ghl-token-health hook) reads .env DIRECTLY and so never depended on the env.
//   The MCP header was the lone hold-out. This helper brings it into line: it reads
//   the ONE token source (.env) directly and hands Claude Code the header at connect
//   time. No second copy of the PIT, no reliance on the launching shell, compact-proof.
//
// CONTRACT (Claude Code docs, "Use dynamic headers for custom authentication"):
//   - Must write a JSON object of string->string to stdout, e.g.
//       {"Authorization":"Bearer <pit>"}
//   - Runs in a shell, 10s timeout; re-run on every connect/reconnect and on 401/403.
//   - Claude Code sets CLAUDE_CODE_MCP_SERVER_NAME so one helper serves both servers.
//
// The token is NEVER printed except inside the JSON header value on stdout.
// On any failure it emits `{}` (no header) — a clean, silent no-auth rather than a leak.
// -----------------------------------------------------------------------------
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';

// repo root = two levels up from .claude/hooks/<this file>
const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '..', '..');

// Pick the PIT by which server is connecting (read vs write). Default: read.
const server = process.env.CLAUDE_CODE_MCP_SERVER_NAME || '';
const pitEnv = server === 'ghl-social-write' ? 'GHL_SOCIAL_WRITE_PIT' : 'GHL_SOCIAL_READ_PIT';

const envField = (text, key) => {
  const m = text.match(new RegExp('^\\s*(?:export\\s+)?' + key + '\\s*=\\s*(.+?)\\s*$', 'm'));
  return m ? m[1].replace(/^["']|["']$/g, '') : '';
};

try {
  const envPath = join(root, '.env');
  if (!existsSync(envPath)) { process.stdout.write('{}'); process.exit(0); }
  const pit = envField(readFileSync(envPath, 'utf8'), pitEnv);
  if (!pit) { process.stdout.write('{}'); process.exit(0); }
  process.stdout.write(JSON.stringify({ Authorization: `Bearer ${pit}` }));
} catch {
  process.stdout.write('{}');
}
