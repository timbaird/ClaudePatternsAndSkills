# skill-packs — skills deployed as a group

A **skill-pack** is a bundle of related skills that **must be deployed together as a single unit** —
not cherry-picked. The skills in a pack **share dependencies** (typically a common `scripts/`
engine), so installing only some of them would leave the rest broken.

## Deploying a pack

**Copy the pack's *entire* contents into `<project>/.claude/skills/`.** The individual skill folders
land as siblings and the shared `scripts/` folder lands at `.claude/skills/scripts/` — which is the
path the skills' engines are hardcoded to expect. Do **not** deploy a subset of a pack.

> Single, independently-deployable skills live in [`../skills/`](../skills/) instead. The rule of
> thumb: if removing one file would break another skill, they belong in a pack together.

## Catalogue

| Pack | Skills | Summary |
|---|---|---|
| [vet-uoc-development](vet-uoc-development/) | 6 + shared engine | VET/TAFE unit-of-competency & cluster assessment toolkit — transcribe UoCs, consolidate them, and validate transcription / consolidation / AT-traceability / cluster-coverage. Shares a `scripts/` engine. |

See each pack's own `README.md` for its contents, prerequisites, and deployment notes.
