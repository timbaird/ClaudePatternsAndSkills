# bro · v1.0.0 (updated 2026-08-15)

## Purpose
Re-explain the **previous assistant message** in much plainer language — for when a reply came out
too dense, too jargon-heavy, or too formal and you just want it said simply. Triggered by `/bro`.
**Internally created.** Pure instruction — no script, no dependencies.

## Prerequisites
- None. It's a single `SKILL.md` (no engine, no runtime, no third-party package).

## Inputs & outputs
- **In:** the `/bro` invocation (no arguments). It operates on the most recent assistant message
  already in the conversation.
- **Out:** a simpler re-statement of that same message. Facts (paths, commands, filenames, numbers,
  URLs, names, decisions) are preserved **verbatim**; only the explanation around them is simplified.

## How it works
The user types `/bro`. The skill re-expresses the last assistant message — it does **not** re-answer,
add information, or use tools. It flattens headers/tables into plain sentences, keeps the same
language as the original (English stays English; PT-BR stays PT-BR), and preserves every fact exactly.
If there's no previous assistant message, it says there's nothing to simplify yet.

## Version history
- **v1.0.0 (2026-08-15)** — initial documented version (centralised into the library).
