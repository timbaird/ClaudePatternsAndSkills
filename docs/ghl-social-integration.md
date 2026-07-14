# GHL Social Integration (MCP) — reference & safety rules

> **⛔ COMPULSORY READ before doing ANY work on the GHL social integration / MCP.**
> This document defines a safety invariant that prevents publishing a channel's content to the **wrong
> account** (e.g. a different business's YouTube). Do not write, schedule, or design any GHL posting
> workflow without following the composite-key rule below.

## What this is

GoHighLevel (GHL) exposes an official MCP server that lets an agent query and drive the connected social
accounts programmatically. We use it to read connected-account status and (later, gated) to schedule a
channel's shorts/pins across TikTok / Instagram-Reels / Pinterest / YouTube-Shorts.

- **Endpoint:** `https://services.leadconnectorhq.com/mcp/anthropic/v2`
- **Auth:** a Private Integration Token (PIT), `Authorization: Bearer <pit>`, scoped by capability
  (e.g. `socialplanner/account.readonly`). The secret PIT lives in `.env` (gitignored) and is read from
  there at connect time by a `headersHelper` — see **How the PIT reaches the MCP** below. **Never** put a
  `${GHL_SOCIAL_*_PIT}` substitution in `.mcp.json` `headers`.
- **Tool shape:** 5 generic verbs — `search`, `fetch`, `search_operations`, `describe_operation`,
  `execute_operation` — over 40+ GHL domains. Social posting lives in the `social-planner` domain.
- **Account binding:** shared coords (location id, pit env var, endpoint) in repo-root
  `distribution.yaml`; per-channel authorised destinations in `channels/<slug>/distribution.yaml`.

## How the PIT reaches the MCP (`headersHelper`, not `${VAR}`)

**The rule: the MCP Authorization header is produced by a `headersHelper` script that reads `.env`
directly. Do NOT use a `${GHL_SOCIAL_*_PIT}` substitution in `.mcp.json`.** Config:

```json
"ghl-social-read": {
  "type": "http",
  "url": "https://services.leadconnectorhq.com/mcp/anthropic/v2",
  "headersHelper": "node .claude/hooks/ghl-mcp-headers.mjs"
}
```

The helper (`.claude/hooks/ghl-mcp-headers.mjs`) reads the repo-root `.env`, picks the read vs write PIT
from `CLAUDE_CODE_MCP_SERVER_NAME` (so the **one** helper serves both the read and the future write
server), and writes `{"Authorization":"Bearer <pit>"}` to stdout. Claude Code runs it on every
connect/reconnect and re-runs it automatically on a 401/403 (v2.1.193+). Requires Claude Code ≥ v2.1.195.

**Why it must be the helper, not `${VAR}` (so this is never re-diagnosed):** Claude Code expands `${VAR}`
in `.mcp.json` from the **process environment only** — it does **not** load the project `.env` for that
substitution (verified: the PIT is absent from the process env at launch *and* after a full restart, so
`Bearer ${GHL_SOCIAL_READ_PIT}` resolves to an empty token → **`Invalid JWT`**). Every other secret
consumer in this repo (the image/music/video skills' `load_api_key`, the `ghl-token-health` hook) already
reads `.env` directly and so never depended on the environment; the MCP header was the lone hold-out. The
`headersHelper` brings it into line — one `.env`, no duplicated token, no reliance on the launching
shell, and it survives `/compact` (a compact reconnects the MCP server, which re-runs the helper).
Editing `.mcp.json` or the helper needs a **window reload** to take effect (and a one-time workspace-trust
prompt, because `headersHelper` runs a shell command).

## THE COMPOSITE-KEY RULE (the load-bearing invariant)

**A GHL account's identity is a composite of `platform` + the specific account — never `platform`
alone.** One GHL location fronts *many* businesses/channels, and **you must assume every platform will
eventually have more than one connected account** (if one channel uses TikTok and Pinterest, other
channels and future projects almost certainly will too). "The YouTube account" / "the Pinterest account"
is therefore **meaningless and dangerous** — it silently resolves to whichever same-platform account
GHL happens to return first.

To identify the correct destination you must **deliberately check BOTH the platform AND the account
identity together**:

- **Human-facing composite key:** `(platform, account name/handle)` — e.g. *"Channel A · youtube"* —
  used for reasoning and eyeball verification.
- **Machine-safe composite key:** `(platform, native_id)` — the durable selector used at execution
  time. Native ids: YouTube channel `UC…`, Pinterest profile id, TikTok originId.

**Never select a destination by platform.** Always resolve to a pinned `(platform, native_id)` from the
working channel's allowlist, and confirm the account name matches what you expect before acting.

### Why native id, not GHL's full account id

`get-account` returns a full account id shaped `oauthId_locationId_nativeId_type`. The leading `oauthId`
is per-connection and likely churns if the account is disconnected/reconnected — staling any allowlist
pinned to it. Pin on the **native id** (durable, and human-verifiable against the real channel/profile).
Treat the full account id as a runtime lookup result, not a stored key.

## Worked example — this is not theoretical

A live `get-account` on the shared location returned **two YouTube channels**:

| Platform | Account name | native_id |
|---|---|---|
| youtube | **Channel A** | `UC_CHANNEL_A_YT` |
| youtube | **Channel B** | `UC_CHANNEL_B_YT` |

A workflow selecting by `platform == "youtube"` would publish Channel A's content to **Channel B**
roughly half the time. Only the composite `(youtube, UC_CHANNEL_A_YT)` names the right one.

## How scheduling works — GHL is the queue, not a hand-off

**GHL holds scheduled posts on its side and publishes them to the platform via API at the scheduled
time. It does NOT queue anything into the platform's own native scheduler.** A `create-post` is stored
with `status: "scheduled"` + a `scheduleDate`; at that moment GHL calls the platform API (using the
stored OAuth token) and publishes. Nothing appears on TikTok/Pinterest/YouTube until GHL fires it.
(Proof: if a social account's OAuth token expires between scheduling and go-time, the post *fails* and
GHL prompts a reconnect — only possible because GHL makes the live call at publish time.)

Implications:

- **Native horizon caps don't apply.** Because GHL publishes via API at go-time (not into the native
  scheduler), TikTok's ~10-day / Pinterest's ~2-week *native* limits are irrelevant. GHL itself has **no
  publicly documented maximum** future date (recurring posts go months/years out).
- **The only real constraint: the account connection must be live at PUSH time (not now).** GHL makes
  the live API call at publish time, so what matters is token validity *then*. Only push-time validity
  matters — you can schedule past the current `expire` date **provided the connection is kept alive to
  the push time**. Two cases:
  - **Auto-refreshing platforms** — GHL silently rotates the token via a refresh token; the connection
    stays alive indefinitely and the `expire` date keeps rolling forward. Safe to schedule arbitrarily
    far out.
  - **Manual-reconnect platforms** (Meta/Facebook is the classic) — the platform forces periodic
    re-auth; the token genuinely dies on its date unless the human reconnects. A post scheduled past
    that **fails** if not reconnected in time; GHL's ~day-50 pre-expiry notice is the reconnect nudge.
  Determine which per account **empirically & for free** via the read integration: re-poll
  `get-account` over time — if `expire` advances on its own it auto-refreshes (schedule far); if it
  counts down to a fixed date it needs a manual reconnect first. A **monthly batch (~4–5 weeks) is safe
  on every platform** regardless. When write scope exists, `dryRun` a far-future `create-post` to
  confirm any hard GHL ceiling empirically.
- **Media is fetched by URL** — `create-post` `media[]` requires a `url`; GHL pulls the asset by link.
  Local files (our Drive assets) are **uploaded first** via the REST media endpoint (Step 1 in the
  recipe below), which returns a GHL-hosted CDN URL. **Solved.**

## Scheduling a post — the proven per-platform recipe

**Proven end-to-end for TikTok, YouTube Shorts, and Pinterest** (each created, verified, and deleted).

> **⭐ Use the `schedule-social` skill instead of hand-rolling this.** `.claude/skills/schedule-social/`
> is the deterministic engine that encapsulates the whole recipe below — the allowlist guard, media
> upload, the per-platform payload builders, and every gotcha — behind
> `schedule_social.py --channel <slug> --platform <youtube|tiktok|pinterest> --media … --date … [--title/--link/--board]`.
> Its `SKILL.md` is the live per-platform field map. The manual procedure below is the reference for what
> the skill does (and for adding a new platform).

**Auth & scopes.** The write PIT (`GHL_SOCIAL_WRITE_PIT`) needs **all** of: `socialplanner/post.write`,
`socialplanner/post.readonly`, `medias.write`, `medias.readonly`, `socialplanner/oauth.readonly`. Reads
may use the read PIT. A `userId` is **required** for every non-draft post — it's stable, non-secret, and
stored in `channels/<slug>/distribution.yaml` (`ghl.user_id`); `users.readonly` scope is **not** needed
once it's stored. (`search-users` needs `users.readonly` and returns 401 without it — hence store the id.)

**Guard.** Route writes through the `ghl-social-write` MCP server so the PreToolUse guard
(`ghl-write-guard.mjs`) fires automatically. If you drive by raw `curl` (guard bypassed), you MUST
manually verify every target account id is on the channel allowlist first.

**Two universal gotchas:**
- **Build request bodies with `jq`, never by shell string-concatenation** — a malformed body returns
  `400 "Expected ',' or '}' after property value"`. (`jq -n --arg … '{…}'` guarantees valid JSON.)
- **Responses are SSE.** Parse the `data:` line → `.result.content[].text` → parse *that* JSON again.
  (`sed -n 's/^data: //p' | jq -r '.result.content[]?.text' | jq …`)

### Step 1 — Upload the media (REST, NOT in the MCP)

```
curl -X POST "https://services.leadconnectorhq.com/medias/upload-file?locationId=<LOC>" \
  -H "Authorization: Bearer $GHL_SOCIAL_WRITE_PIT" -H "Version: 2021-07-28" -H "Accept: application/json" \
  -F "file=@<path>;type=video/mp4" -F "hosted=false" -F "name=<name>"
# → 201 { "fileId": "...", "url": "https://assets.cdn.filesafe.space/<LOC>/media/<uuid>.mp4" }
```
Use `type=image/jpeg` for pin images. The returned `url` is what goes into `media[].url` in Step 3.

### Step 2 — Pinterest ONLY: fetch board ids (REST, undocumented, NOT in the MCP)

```
curl "https://services.leadconnectorhq.com/social-media-posting/oauth/<LOC>/pinterest/boards/<oauthId>" \
  -H "Authorization: Bearer $GHL_SOCIAL_READ_PIT" -H "Version: 2021-07-28" -H "Accept: application/json"
# → { results: { boards: [ { id, name, privacy, ... }, ... ] } }
```
`<oauthId>` = the **leading segment** of the account id, before the first `_`
(e.g. account `6a4d7a69…_Q854…_1124…_profile` → oauthId `6a4d7a69528a1b5635dde2b7`). This is the only
known way to get Pinterest board ids — there is **no** board-list operation in the MCP registry, and no
public docs for this endpoint. The board **names** returned map 1:1 to the boards in `pins.txt`.

### Step 3 — create-post (MCP `execute_operation`, `operationId: "create-post"`)

Common `params.body` (all platforms):
```
accountIds:   [ "<full account id from the channel allowlist>" ]
summary:      "<caption / description>"
type:         "post"
userId:       "<ghl.user_id>"
media:        [ { url: "<cdn url from Step 1>", type: "<mime>" } ]
status:       "scheduled"
scheduleDate: "2026-07-13T10:00:00Z"          # ISO 8601 — NOT epoch millis (epoch → "Invalid Date")
```
Plus, as siblings of `params.body`, the `execute_operation` args need
`idempotencyKey: "<unique>"` and a `reason: "<text>"` (writes require an idempotency key).

Add the **per-platform block** inside `body`:

| Platform | `media[].type` | Extra `body` block | Caption / link rule |
|---|---|---|---|
| **TikTok** | `video/mp4` | `tiktokPostDetails: { privacyLevel: "PUBLIC_TO_EVERYONE" }` | caption in `summary`; **no link** (TikTok captions aren't clickable) |
| **YouTube Shorts** | `video/mp4` | `youtubePostDetails: { type: "short", title: "<title>" }` — `type` is **required** (`short`\|`video`); this is what makes it publish as a Short | `summary` (description) **keeps** the YouTube link |
| **Pinterest** | `image/jpeg` | `pinterestPostDetails: { link: "<destination URL>", boardIds: { "<full account id>": [ "<board id>" ] } }` | **`link`** is the pin's clickable destination (the YouTube URL); `summary` = description |

**Pinterest field rules (hard-won):** a top-level `link` is **rejected** (`property link should not
exist`) — the destination link lives at `pinterestPostDetails.link`. The board is
`pinterestPostDetails.boardIds`, an **object keyed by the full account id** whose value is an **array**
of board ids — not `boardId`, not a bare array.

**YouTube field rules (hard-won):** the block is **`youtubePostDetails`** (lowercase-t) and its `type`
is **required** — `"short"` (vertical Short) or `"video"`. A top-level `title`, a top-level `link`, and
the capital `youTubePostDetails` are all **rejected** (`property … should not exist`). The title goes in
`youtubePostDetails.title`; the YouTube link stays in the `summary` (description).

### Step 4 — verify

Read the `create-post` response's `.data.results.post` (it echoes the stored object incl.
`tiktokPostDetails` / `pinterestPostDetails`), or list with `get-posts`
(`operationId: "get-posts"`, `POST …/posts/list`; requires `idempotencyKey`, ISO `fromDate`/`toDate`,
and `skip`/`limit` as **strings**). Note: `platform` in the create response always reads `"google"` — a
cosmetic default; trust `accountIds`, not that field.

### Step 5 — delete (for tests, or to remove a scheduled post)

`operationId: "bulk-delete-social-planner-posts"`, body `{ postIds: [ "<_id>" ] }` + `idempotencyKey`.
Returns `deletedCount`. (There's no cancel-in-place; delete + recreate to reschedule, or use `edit-post`.)

### Worked example — Pinterest (the hardest; TikTok/YT are the same minus the pinterest block)

```bash
jq -n --arg loc "$LOC" --arg acct "$FULL_ACCOUNT_ID" --arg uid "$GHL_USER_ID" \
      --arg img "$CDN_IMAGE_URL" --arg yt "$YT_URL" --arg when "$ISO_DATE" --arg board "$BOARD_ID" '
{jsonrpc:"2.0",id:1,method:"tools/call",params:{name:"execute_operation",arguments:{
  operationId:"create-post", idempotencyKey:"pin-2026-07-15-v001", reason:"schedule v001 pin",
  params:{locationId:$loc, body:{
    accountIds:[$acct], summary:"<description>", type:"post", userId:$uid,
    media:[{url:$img, type:"image/jpeg"}], status:"scheduled", scheduleDate:$when,
    pinterestPostDetails:{ link:$yt, boardIds:{ ($acct):[$board] } }
  }}}}}' \
| curl -sS -X POST "https://services.leadconnectorhq.com/mcp/anthropic/v2" \
    -H "Authorization: Bearer $GHL_SOCIAL_WRITE_PIT" -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" -d @- \
| sed -n 's/^data: //p' | jq -r '.result.content[]?.text' | jq '.data.results.post'
```

**Caveat — publish vs schedule.** All of the above is proven at the *scheduling* layer (post lands in
GHL's queue with the right fields). Whether a board-less/title-less post publishes cleanly, and TikTok's
audited-publish behaviour, should be **confirmed on the first real (undeleted) publish** and monitored.

## Token health check — automated at every session start

Because a scheduled post only needs its token live **at push time**, the sole ongoing maintenance is
keeping connections alive. This runs **automatically**: the SessionStart hook
`.claude/hooks/ghl-token-health.mjs` does a read-only `get-account` sweep on every session start and
prints one line — highlighting the next token to expire and shouting `⚠ RECONNECT NOW` /
`⚠ expiring ≤30d` if action is needed. When it flags something, reconnect that account in GHL before
scheduling past its date. (The hook degrades to a quiet `SKIP:` line where no read PIT is present.)
**`expire` alone is a misleading signal** — the hook (and you) read it this way:

| Signal | Meaning | Action |
|---|---|---|
| `isExpired: true` | Connection actually broken | Reconnect now |
| `expire` **advances** on re-poll | Auto-refreshing (e.g. Google/YouTube issues ~1h access tokens GHL rotates) | None — safe to schedule far ahead |
| `expire` a **fixed date counting down** within the next window | Hard token (e.g. Meta/Pinterest ~60d) | Reconnect before that date if scheduling past it |

So a near-term `expire` is not itself a problem: YouTube's reads ~1 hour out **and is the healthiest**
(constantly refreshed); the ones to watch are fixed-date tokens nearing their day. Example snapshot
(2026-07-07): TikTok ~364d, YouTube ~0d (auto-refresh — fine), Pinterest fixed 2026-09-05 (~60d — the
one to watch). A normal monthly batch (~4–5 weeks) is inside every window regardless; the check only
matters if scheduling further out or if an account shows `isExpired`.

## Isolation model — the three enforcement layers

A shared login is **not** a boundary: a location-scoped token can post to *any* account in the
location, so the credential does not isolate one channel from another. Isolation is enforced in the
workflow layer (deterministic-first — instructions alone are insufficient):

1. **Data** — each channel pins an allowlist of `(platform, native_id, handle)` in
   `channels/<slug>/distribution.yaml`. Accounts belonging to other projects are excluded (and noted).
2. **Instruction (soft)** — the posting agent is told: post only to your channel's allowlist, select by
   native id, never by platform, confirm the name.
3. **Guard (hard)** — a deterministic pre-write check rejects any write whose target account id is not on
   the working channel's allowlist. **Built & verified:** the PreToolUse hook
   `.claude/hooks/ghl-write-guard.mjs` (matcher `mcp__ghl-social-write__.*`) matches each target account
   id against the channel's `native_id`s (substring) and **fails closed** — it blocks any policy
   violation (exit 0 + deny JSON) and blocks on any parse/allowlist error (exit 2), never auto-approving
   (so your normal permission prompt still applies). With >1 channel and no active-selection it refuses
   rather than risk cross-channel posting. Dormant until `ghl-social-write` is added to `.mcp.json`. The
   agent cannot self-authorise; the allowlist is data it can't widen.

**An agent/session may post ONLY to accounts authorised in the channel it is working from.**

## Reading connected accounts (read PoC — proven)

The `get-account` operation (`GET /social-media-posting/{locationId}/accounts`, scope
`socialplanner/account.readonly`) lists connected accounts and live-mirrors them as they are added in
GHL. Call it via `execute_operation` with `params:{locationId}`. Use it to build/verify a channel's
allowlist — match each pinned native id against the returned accounts and confirm the name.

## Status

- **Read PoC: proven.** Read-only PIT authenticates; `get-account` returns connected accounts and their
  status in real time.
- **Write recipe: proven** (2026-07-08) end-to-end for **TikTok, YouTube Shorts, and Pinterest** —
  upload → schedule → verify → delete, each with full fidelity (see the recipe above). Media-by-URL is
  solved (REST upload). Pinterest link + board are solved (`pinterestPostDetails` + the boards endpoint).
  The write-guard is built and verified.
- **Remaining to go live:**
  1. Wire the `ghl-social-write` MCP server into `.mcp.json` using `"headersHelper": "node
     .claude/hooks/ghl-mcp-headers.mjs"` (the same helper — it returns the **write** PIT when
     `CLAUDE_CODE_MCP_SERVER_NAME` is `ghl-social-write`). This routes writes through the PreToolUse guard
     instead of raw `curl` + manual allowlist checks. (Needs a window reload + trust prompt.)
  2. Build the publisher (video folder → upload → schedule per platform on drip dates).
  3. Confirm real *publish* behaviour on the first undeleted post (title/privacy/board at go-time).
  4. Reels waits on an Instagram account being connected in GHL.
- **Verdict correction:** an earlier read concluded pins couldn't carry their link/board via the API.
  That was wrong — it hadn't sent `pinterestPostDetails.link` / `.boardIds`. **Pinterest is fully
  supported.** Whether to migrate pins is now a workload choice (1/week), not a capability limit.
