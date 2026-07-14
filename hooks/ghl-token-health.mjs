#!/usr/bin/env node
// ghl-token-health.mjs
// -----------------------------------------------------------------------------
// SessionStart hook: a read-only sweep of the GHL social accounts' token expiries.
// Prints ONE concise status line highlighting the next token to expire and any that
// need a reconnect, so scheduled posts always fire onto live tokens.
//     node .claude/hooks/ghl-token-health.mjs
//
// - Never blocks the session and never prints the token.
// - Config from repo-root distribution.yaml (location_id / read_pit_env / mcp_endpoint);
//   the PIT itself from .env. Any missing piece -> SKIP (quiet, exit 0).
// - No dependencies (Node stdlib + global fetch).
//
// Expiry interpretation (see docs/ghl-social-integration.md): a token < 1 day out is
// treated as a short-lived AUTO-REFRESHING access token (e.g. Google/YouTube ~1h) and
// counted healthy; hard tokens (Meta/Pinterest ~60d) count down and are flagged within
// 30 days. isExpired => reconnect now.
// -----------------------------------------------------------------------------
import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import process from 'node:process';

function repoRoot() {
  try {
    const out = execFileSync('git', ['rev-parse', '--show-toplevel'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
    if (out) return resolve(out);
  } catch { /* not a git repo — fall back to cwd */ }
  return resolve(process.cwd());
}

const yamlField = (text, key) => {
  const m = text.match(new RegExp('^\\s*' + key + '\\s*:\\s*(.+?)\\s*(?:#.*)?$', 'm'));
  return m ? m[1].replace(/^["']|["']$/g, '') : '';
};
const envField = (text, key) => {
  const m = text.match(new RegExp('^\\s*(?:export\\s+)?' + key + '\\s*=\\s*(.+?)\\s*$', 'm'));
  return m ? m[1].replace(/^["']|["']$/g, '') : '';
};

async function main() {
  const root = repoRoot();
  const distPath = join(root, 'distribution.yaml');
  if (!existsSync(distPath)) { console.log('SKIP: GHL token check — no distribution.yaml'); return; }
  const dist = readFileSync(distPath, 'utf8');
  const locationId = yamlField(dist, 'location_id');
  const pitEnv = yamlField(dist, 'read_pit_env') || 'GHL_SOCIAL_READ_PIT';
  const endpoint = yamlField(dist, 'mcp_endpoint') || 'https://services.leadconnectorhq.com/mcp/anthropic/v2';
  if (!locationId) { console.log('SKIP: GHL token check — no location_id'); return; }

  const envPath = join(root, '.env');
  if (!existsSync(envPath)) { console.log('SKIP: GHL token check — no .env'); return; }
  const pit = envField(readFileSync(envPath, 'utf8'), pitEnv);
  if (!pit) { console.log(`SKIP: GHL token check — ${pitEnv} not set`); return; }

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 8000);
  let accounts;
  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      signal: ctrl.signal,
      headers: {
        Authorization: `Bearer ${pit}`,
        'Content-Type': 'application/json',
        Accept: 'application/json, text/event-stream',
      },
      body: JSON.stringify({
        jsonrpc: '2.0', id: 1, method: 'tools/call',
        params: { name: 'execute_operation', arguments: { operationId: 'get-account', params: { locationId }, reason: 'SessionStart token-health check' } },
      }),
    });
    const text = await res.text();
    const dataLine = text.split('\n').find((l) => l.startsWith('data: '));
    if (!dataLine) { console.log('SKIP: GHL token check — empty response'); return; }
    const inner = JSON.parse(JSON.parse(dataLine.slice(6)).result.content[0].text);
    accounts = inner?.data?.results?.accounts || [];
  } catch {
    console.log('SKIP: GHL token check — unavailable (offline?)');
    return;
  } finally {
    clearTimeout(timer);
  }

  if (!accounts.length) { console.log('OK: GHL — no social accounts connected'); return; }

  const now = Date.now();
  const DAY = 86400000;
  const rows = accounts.map((a) => {
    const exp = a.expire ? Date.parse(a.expire) : NaN;
    return { label: `${a.platform} "${a.name}"`, isExpired: !!a.isExpired, days: Number.isFinite(exp) ? Math.floor((exp - now) / DAY) : null };
  });

  const dead = rows.filter((r) => r.isExpired);
  const hard = rows.filter((r) => !r.isExpired && r.days !== null && r.days >= 1).sort((a, b) => a.days - b.days);
  const soon = hard.filter((r) => r.days <= 30);

  const parts = [];
  if (dead.length) parts.push(`⚠ RECONNECT NOW: ${dead.map((r) => r.label).join(', ')}`);
  if (soon.length) parts.push(`⚠ expiring ≤30d: ${soon.map((r) => `${r.label} in ${r.days}d`).join(', ')}`);
  if (!dead.length && !soon.length) {
    const next = hard[0];
    parts.push(next
      ? `OK: GHL social tokens healthy — ${accounts.length} live, next expiry ${next.label} in ${next.days}d`
      : `OK: GHL social tokens healthy — ${accounts.length} live`);
  }
  console.log(parts.join(' | '));
}

main().catch(() => { console.log('SKIP: GHL token check errored'); process.exit(0); });
