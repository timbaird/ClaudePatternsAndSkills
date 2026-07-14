# schedule-social

The **deterministic engine** for scheduling ONE social post via **GHL (GoHighLevel) Social Planner** —
channel- and platform-agnostic. Same args → same request (no LLM in the loop). It resolves the
destination from the **channel's allowlist** (the composite-key guard, built in), uploads the media,
builds the correct per-platform `create-post` payload, and schedules the post.

> **This file is the single source of truth for GHL's per-platform field mechanics** — so no session
> ever has to re-probe GHL to rediscover field names. Fuller context:
> [docs/ghl-social-integration.md](../../docs/ghl-social-integration.md).

## Setup (per-skill venv — see [docs/skill-dependencies.md](../../docs/skill-dependencies.md))

```bash
python3 -m venv .claude/skills/schedule-social/.venv
.claude/skills/schedule-social/.venv/bin/pip install -r .claude/skills/schedule-social/requirements.txt
```
`.venv/` is gitignored. Run tests offline (no network/API):
```bash
.claude/skills/schedule-social/.venv/bin/python .claude/skills/schedule-social/tests.py
```

## Wiring (config + secrets)

Non-secret config lives in two committed YAML files; secrets (the Private Integration Tokens) live in
`.env`. See [`distribution.example.yaml`](distribution.example.yaml) for the full schema:

- **repo-root `distribution.yaml`** — shared GHL settings (`location_id`, the MCP endpoint, and which
  `.env` var holds each PIT).
- **`channels/<slug>/distribution.yaml`** — the channel's **allowlist**: one `destinations` entry per
  `(platform + account)`, each pinned to a durable **`native_id`** (never a GHL display name).

## Use

```bash
PY=.claude/skills/schedule-social/.venv/bin/python
S=.claude/skills/schedule-social/schedule_social.py

# YouTube Short
$PY $S --channel my-channel --platform youtube --media path/short.mp4 \
      --date 2026-07-26T00:00:00Z --title "my short title #shorts" \
      --desc "Description with the full-video link: https://youtu.be/VIDEO_ID"

# TikTok (caption only — no clickable link)
$PY $S --channel my-channel --platform tiktok --media path/short.mp4 \
      --date 2026-07-26T00:00:00Z --desc "Caption text #tags"

# Pinterest pin (link + board)
$PY $S --channel my-channel --platform pinterest --media path/pin.jpg \
      --date 2026-07-26T00:00:00Z --title "Pin Title" --link https://youtu.be/VIDEO_ID \
      --board "My Board" --desc "Pin description ..."

# Instagram Reel / Facebook Reel (caption only — no clickable link; CTA goes in the bio link)
$PY $S --channel my-channel --platform instagram --media path/short.mp4 \
      --date 2026-07-26T00:00:00Z --desc "Caption #tags"
```
`--dry-run` resolves the account + builds the payload **without** uploading or posting (preview + guard check).
Prints `RESULT {json}`.

## The composite-key guard (built in — cannot be bypassed by args)

You pass a **channel slug**, never a GHL display name. The engine:
1. finds the channel's allowlisted destination for `--platform` in `channels/<slug>/distribution.yaml`
   (refuses if the platform isn't allowlisted, or if >1 is);
2. calls `get-account` and resolves that allowlisted **native_id** to the live GHL account id;
3. **refuses** if no connected account carries the allowlisted native id (never falls through to a
   same-platform sibling — e.g. it will not post *channel A's* Short to *channel B*).

So the account is data the caller can't widen. Secrets (PITs) come from `.env`; ids/config from the
committed `distribution.yaml` files. **Why this matters:** one GHL location can front many same-platform
accounts across projects, so "platform" alone is not a safe destination — the guard pins each post to a
specific `(platform + native_id)`.

## Per-platform field map (the captured knowledge)

| platform | media mime | required extras | `create-post` detail block | link in caption? |
|---|---|---|---|---|
| **youtube** | `video/mp4` | `--title` | `youtubePostDetails{ type:"short"\|"video", title }` | **yes** (keep it) |
| **tiktok** | `video/mp4` | — | `tiktokPostDetails{ privacyLevel:"PUBLIC_TO_EVERYONE" }` | no (not clickable) |
| **pinterest** | `image/jpeg` | `--link`, `--board` | `pinterestPostDetails{ link, title, boardIds:{ <accountId>:[boardId] } }` | via `link` (destination) |
| **instagram** | `video/mp4` | — | *(none)* — a professional IG account publishes any video as a **Reel** | no (not clickable) |
| **facebook** | `video/mp4` | — | *(none)* — a single video to a Page publishes as a **Reel** | **Reels only** (never link posts) |

**Hard-won gotchas** (encoded in the builders; don't relearn):
- YouTube: the field is **`youtubePostDetails`** (lowercase-t); `type` is **required** and must be
  `short`/`video`. A top-level `title` and capital `youTubePostDetails` are **rejected**.
- Pinterest: top-level `link` is **rejected** — it lives at `pinterestPostDetails.link`. `boardIds` is an
  **object keyed by the full account id** → array of board ids (not `boardId`, not a bare array). Board
  **names** in the channel allowlist resolve to ids via `--board`.
- Instagram/Facebook: **no detail block, no clickable link.** A professional IG account and a FB Page
  both auto-publish a single (vertical, <90s) video as a **Reel**. FB is Reels-only by policy (it throttles
  off-platform links); the destination CTA lives in the IG/FB bio link, not the caption. Reel-vs-feed is
  decided at Meta's publish time — the stored post record carries no reel discriminator, so don't look for
  one; the GHL Social Planner UI shows it.
- **Encoding red herring:** the MCP `execute_operation` *echo* mangles UTF-8 in its return (em-dash → `â`,
  emoji garbled). Storage is correct — verify by a direct-REST read-back (`GET .../posts/{id}`). Don't
  "fix" captions because the create response looks garbled; it's the return channel, not the data.
- All: `type:"post"` + `userId` required; dates ISO 8601 (not epoch); media is URL-only so it's uploaded
  first (copy Drive files to a local temp before upload — File Stream lazy-loads otherwise).

## Scope

One post per call (schedule only). Loop it for a batch. `dryRun`/verify/delete against GHL are separate
`execute_operation` ops (`get-posts`, `bulk-delete-social-planner-posts`) — add as modes if needed.
