#!/usr/bin/env node
// ensure-repo-memory.mjs
// -----------------------------------------------------------------------------
// Idempotently point THIS repo's Claude auto-memory at <repo-root>/.claude/memory
// by setting `autoMemoryDirectory` in .claude/settings.local.json (machine-local,
// gitignored). Intended as a SessionStart hook command:
//     node .claude/hooks/ensure-repo-memory.mjs
//
// Cross-platform by design: `node <file>` is an identical command on Windows, macOS,
// and Linux — no shell/interpreter differences. No dependencies (Node stdlib only).
//
// Prints one STATUS line:
//   OK:    already configured
//   FIXED: path was (re)written -> a relaunch is required to load memory
//   SKIP:  not applicable here (no .claude folder)
// -----------------------------------------------------------------------------
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync, statSync } from 'node:fs';
import { join, resolve } from 'node:path';
import process from 'node:process';

function repoRoot() {
  try {
    const out = execFileSync('git', ['rev-parse', '--show-toplevel'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
    if (out) return resolve(out);
  } catch { /* not a git repo / git missing — fall back to cwd */ }
  return resolve(process.cwd());
}

const isDir = (p) => { try { return statSync(p).isDirectory(); } catch { return false; } };

const root = repoRoot();
const claudeDir = join(root, '.claude');
const memDir = resolve(join(claudeDir, 'memory'));
const settingsPath = join(claudeDir, 'settings.local.json');

if (!isDir(claudeDir)) {
  console.log(`SKIP: no .claude folder at ${root}`);
  process.exit(0);
}

// Load (or init) settings.local.json, preserving existing keys.
let cfg = {};
if (existsSync(settingsPath)) {
  try { cfg = JSON.parse(readFileSync(settingsPath, 'utf8')); } catch { cfg = {}; }
  if (cfg === null || typeof cfg !== 'object' || Array.isArray(cfg)) cfg = {};
}

// Compare (case-insensitive on Windows, path-normalised).
const norm = (p) => {
  if (!p) return '';
  const s = resolve(String(p));
  return process.platform === 'win32' ? s.toLowerCase() : s;
};

if (norm(cfg.autoMemoryDirectory) === norm(memDir)) {
  console.log(`OK: repo memory already configured -> ${memDir}`);
  process.exit(0);
}

// Fix: ensure the folder, set the property, write UTF-8 (no BOM).
if (!existsSync(memDir)) mkdirSync(memDir, { recursive: true });
if (!('$schema' in cfg)) cfg['$schema'] = 'https://json.schemastore.org/claude-code-settings.json';
cfg.autoMemoryDirectory = memDir;
writeFileSync(settingsPath, JSON.stringify(cfg, null, 2) + '\n', 'utf8');
console.log(`FIXED: set autoMemoryDirectory -> ${memDir} in settings.local.json. RELAUNCH REQUIRED so memory loads from the repo.`);
process.exit(0);
