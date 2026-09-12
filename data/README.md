# Data directory map

| Path | Contents | Status |
|---|---|---|
| `sources/source_inventory.yaml` | Phase 1 source feasibility scan | Real research, no real data obtained yet |
| `occupation_selection.md` | Phase 1 occupation choice | Provisional |
| `rubric/rubric.yaml`, `rubric/rubric.md` | Phase 2 versioned rubric | Complete, v1.0.0-draft |
| `postings/postings.jsonl`, `postings/matched_pairs.jsonl` | Phase 3 curated corpus | **Synthetic fixtures only** — see `postings/README.md` |
| `annotation/` | Phase 4 templates + AI suggestions | Templates blank; AI suggestions are rule-based, not gold |
| `demo_synthetic_annotations/` | Pipeline-testing only | **NOT GOLD** — see the warning in that directory |
| `splits/` | Phase 5 split manifests | Demo manifests only (`is_gold: false`); real ones must be regenerated after real gold exists |
| `reports/` | Phase 6 generated reports | Demo/pipeline-verification only |

## Internal/local layer vs. public repository layer

Per `TASK_DATA_EVALUATION.md`, this project keeps two layers in mind even
though, today, everything here happens to be publishable (because it is
either methodology/code or self-authored synthetic text):

- **Internal/local layer**: may contain full posting text when lawfully
  obtained for the hackathon workspace. If real postings are added later
  (e.g. via the 고용24/워크넷 Open API once a key is issued), their full text
  goes here first, and each source's license must be re-checked before any
  of it moves to the public layer.
- **Public repository layer**: rubric, annotation schema, source IDs/links,
  derived labels, aggregate statistics, synthetic examples, and collection
  methodology. This is what actually ends up committed in `data/` today.

**Do not assume public accessibility grants redistribution permission.**
When real postings are added, redistribution must be confirmed per source,
not assumed from the fact that a Jeonbuk/metropolitan posting is publicly
viewable on the web.

## What is and is not "gold" right now

Nothing in this repository is gold. Two independent human annotation passes
have not happened (see `DATA_HANDOFF.md`, "Remaining manual steps"). Every
file that could be mistaken for gold is explicitly labeled otherwise:

- `data/annotation/ai_suggestions.jsonl` — `ai_suggested: true` on every row.
- `data/annotation/annotator_A_template.jsonl` / `_B_template.jsonl` — blank,
  waiting for real humans.
- `data/demo_synthetic_annotations/**` — `synthetic_test_fixture: true` on
  every row, plus a module docstring and this README calling it out.
- `data/splits/manifest_demo.json` — `"is_gold": false`.
- `data/reports/demo_*` — `"is_gold": false` and a "NOT GOLD" banner in the
  Markdown report.
