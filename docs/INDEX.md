# docs — index

The technical / knowledge wiki for **ClaudePatternsAndSkills**. One focused topic per file; this is
the entry point. Start with `doco-structure.md` to understand where each kind of content belongs.

## Documents

| Document | Summary |
|---|---|
| [doco-structure.md](doco-structure.md) | The four documentation surfaces (`README` / `CLAUDE.md` / `MEMORY` / `docs/`) — what belongs where, the `CLAUDE.md`⇄`MEMORY` split, and the conventions that keep them coherent. |
| [skill-dependencies.md](skill-dependencies.md) | How a skill that needs a third-party package declares + installs it (per-skill gitignored `.venv/`, `requirements.txt`, import guard, venv-python invocation) + the Python-3 runtime preflight. The standing convention, vendored into every project alongside `doco-structure.md`. |
| [ghl-social-integration.md](ghl-social-integration.md) | Reference + safety rules for the **GHL (GoHighLevel) Social Planner** integration — the **composite-key rule** (a destination is `platform + native_id`, never platform alone, since one GHL location fronts many same-platform accounts), MCP PIT auth via the `headersHelper` hook, and how scheduling works. Pairs with the [`schedule-social`](../skills/schedule-social/) skill + the three `ghl-*` [hooks](../hooks/). |
