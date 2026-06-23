#!/usr/bin/env node
// ensure-python.mjs
// -----------------------------------------------------------------------------
// SessionStart preflight: confirm a usable Python 3 is on PATH, since this
// project's Python skills depend on it. Intended as a SessionStart hook command:
//     node .claude/hooks/ensure-python.mjs
//
// The check itself must NOT depend on Python (chicken-and-egg), so it is written
// in Node (Claude Code's runtime) and probes the common launchers.
//
// Quiet on success (a usable Python 3 is present -> no output). On a problem it
// prints one line that surfaces into the session so Claude can offer to help the
// user install Python. Always exits 0 (advisory, never blocks the session).
//
// Cross-platform, Node stdlib only.
// -----------------------------------------------------------------------------
import { spawnSync } from 'node:child_process';
import process from 'node:process';

const MIN = [3, 9]; // minimum Python version this project's skills need
const minStr = MIN.join('.');

// Candidate launchers, best-first per platform.
const candidates = process.platform === 'win32'
  ? [['py', ['-3', '--version']], ['python', ['--version']], ['python3', ['--version']]]
  : [['python3', ['--version']], ['python', ['--version']]];

function probe() {
  for (const [cmd, args] of candidates) {
    try {
      const r = spawnSync(cmd, args, { encoding: 'utf8' });
      const out = `${r.stdout || ''}${r.stderr || ''}`;
      const m = out.match(/Python (\d+)\.(\d+)\.(\d+)/);
      if (m) {
        const invoke = args.length > 1 ? `${cmd} ${args[0]}` : cmd;
        return { v: [Number(m[1]), Number(m[2]), Number(m[3])], invoke, raw: m[0] };
      }
    } catch { /* try the next launcher */ }
  }
  return null;
}

const gte = (v, min) => v[0] > min[0] || (v[0] === min[0] && v[1] >= min[1]);

const found = probe();

// Success: a usable Python 3 -> stay quiet, as intended.
if (found && found.v[0] === 3 && gte(found.v, MIN)) {
  process.exit(0);
}

const install = process.platform === 'win32'
  ? "Install Python from https://www.python.org/downloads/ and tick 'Add python.exe to PATH', or run `winget install Python.Python.3.12`."
  : process.platform === 'darwin'
    ? 'Install Python via `brew install python@3.12` (or from python.org).'
    : 'Install Python via your package manager, e.g. `sudo apt install python3 python3-venv python3-pip`.';

const problem = found
  ? `found ${found.raw} (via \`${found.invoke}\`), but this project needs Python ${minStr}+`
  : 'no Python 3 was found on PATH';

console.log(
  `PYTHON PREFLIGHT — ${problem}. This project's Python skills ` +
  `will not run until a usable Python ${minStr}+ is on PATH. ${install} Then restart the session. ` +
  `Claude: offer to help the user get Python installed and on PATH.`,
);
process.exit(0);
