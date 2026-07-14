# schedule-social

Deterministic engine to schedule **one social post** via **GHL (GoHighLevel) Social Planner** — YouTube
Shorts / TikTok / Pinterest / Instagram Reels / Facebook Reels. Same args → same request. It resolves the
destination from the channel's **allowlist** (a built-in composite-key guard: `platform + native_id`,
never a display name — so it can't post channel A's content to channel B), uploads the media, builds the
correct per-platform `create-post` payload, and schedules it.

**Internally created** (from yt-music-factory). **Dependency-carrying** — `requests` + `PyYAML`
(per-skill gitignored `.venv/`, [skill-dependencies convention](../../docs/skill-dependencies.md)).

- `schedule_social.py` — the engine (pure per-platform builders + the guard + GHL HTTP).
- `tests.py` — every per-platform builder + the allowlist guard (offline, no network/API).
- `distribution.example.yaml` — the config schema (the two `distribution.yaml` files you provide).
- **Related infra** (in the library): the GHL MCP auth/guard/health hooks in
  [`hooks/`](../../hooks/) and the integration guide [`docs/ghl-social-integration.md`](../../docs/ghl-social-integration.md).

See [SKILL.md](SKILL.md) for the per-platform field map, the guard, and wiring.
