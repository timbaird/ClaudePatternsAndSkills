---
description: Coding principles — applied automatically when editing code (any language, any repo)
paths:
  - "**/*.{py,js,mjs,cjs,jsx,ts,tsx,astro,vue,svelte,go,rs,java,c,cpp,h,hpp,rb,php,cs,sh,bash,sql}"
---

# Coding principles

> Adapted from the *andrej-karpathy-skills* coding guidelines.

Behavioural guidelines to reduce common LLM coding mistakes. These bias toward **caution over
speed** — for trivial tasks, use judgement. Merge with repo-specific instructions as needed.

## 1. Think before coding
Don't assume. Don't hide confusion. Surface tradeoffs. *Before* implementing:
- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't silently pick one.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop, name what's confusing, and ask.

## 2. Simplicity first
Minimum code that solves the problem. Nothing speculative.
- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility"/configurability that wasn't requested.
- No error handling for impossible scenarios.
- If 200 lines could be 50, rewrite it.

Ask yourself: *"Would a senior engineer call this overcomplicated?"* If yes, simplify.

## 3. Surgical changes
Touch only what you must. Clean up only your own mess.
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor what isn't broken. Match existing style even if you'd do it differently.
- Notice unrelated dead code? Mention it — don't delete it.
- Remove imports/variables/functions that *your* changes orphaned; leave pre-existing dead
  code unless asked.

Test: every changed line should trace directly to the request.

## 4. Goal-driven execution
Define success criteria, then loop until verified.
- "Add validation" → write tests for invalid inputs, then make them pass.
- "Fix the bug" → write a test that reproduces it, then make it pass.
- "Refactor X" → ensure tests pass before and after.

For multi-step tasks, state a brief plan with a verify check per step.

---
*Working if:* fewer unnecessary changes in diffs, fewer rewrites from overcomplication, and
clarifying questions come **before** implementation rather than after mistakes.
