# Human annotation runbook — real, private-source postings

Read alongside `CLAUDE.md`, `DATA_HANDOFF.md`, `REAL_DATA_ACQUISITION_HANDOFF.md`,
`ANNOTATION_WORKFLOW_HANDOFF.md`, and `data/annotation/schema.md`.

This document is for the two human annotators and whoever adjudicates their
work on the real 10 Jeonbuk + 10 metropolitan posting batch
(`data/intake/real_postings.jsonl` + `data/intake/real_matched_pairs.jsonl`,
real text privately in `data/private/intake_raw/*.json`). **No AI writes a
label here.** Every tool in this pipeline only prepares files, checks their
shape, and helps a human find/verify an offset faster — it never proposes,
infers, or fills in a `status`.

## Where the real text lives (do not confuse the two)

| File | What it has |
|---|---|
| `data/intake/real_postings.jsonl` | Public metadata (region, occupation, employment type, source URL, checksum). `full_text` is `null` for every non-redistributable record — this is correct, not a bug. |
| `data/private/intake_raw/<posting_id>.json` | The actual private posting text, keyed by its own `posting_id` field. **Gitignored. Never commit this.** |

Every tool below that needs the real text takes a `--private-dir` flag
pointing at `data/private/intake_raw/` and joins it to the public file by
`posting_id` in memory only — it never writes real text back into the
public JSONL, and it refuses to run (see "Fail-closed guarantees" below) if
any posting is missing its private text, if two private files claim the
same `posting_id`, or if the output directory isn't actually gitignored.

## 1. Files each annotator uses

| Annotator | Their own file (read + write) | Files they must never open |
|---|---|---|
| A | `data/private/annotation_packets/annotator_A/packet.jsonl` | `annotator_B/packet.jsonl`, `data/annotation/ai_suggestions.jsonl`, any adjudication/comparison file |
| B | `data/private/annotation_packets/annotator_B/packet.jsonl` | `annotator_A/packet.jsonl`, `ai_suggestions.jsonl`, any adjudication/comparison file |

Both packets are generated once by a team member (not either annotator) via:

```bash
python scripts/annotation_ops/build_packets.py \
  --postings data/intake/real_postings.jsonl \
  --rubric data/rubric/rubric.yaml \
  --private-dir data/private/intake_raw \
  --out-dir data/private/annotation_packets
```

This writes `annotator_A/packet.jsonl`, `annotator_B/packet.jsonl` (20
postings × 6 fields = 120 blank cells each, `status: null`), and a
`manifest.json` (run provenance only — not a label, confers no gold
status). Neither packet ever contains `full_text` or the other annotator's
answers; they reference `posting_id` + `field` only.

## 2. Working independently (structural isolation, not just an instruction)

- Each annotator runs `review_cli.py` against **only their own packet
  file**:

  ```bash
  python scripts/annotation_ops/review_cli.py \
    --packet data/private/annotation_packets/annotator_A/packet.jsonl \
    --postings data/intake/real_postings.jsonl \
    --private-dir data/private/intake_raw
  ```

  (Annotator B runs the same command with `annotator_B/packet.jsonl`.)
- The CLI opens exactly one packet and the joined postings text — it has no
  code path that reads the other annotator's file or `ai_suggestions.jsonl`.
- It saves after every answered cell, so a session can be interrupted and
  resumed by re-running the same command.
- Do not email, Slack, or otherwise share your in-progress packet with the
  other annotator before both are complete and validated.

## 3. Six-field judgment criteria

Full rubric: `data/rubric/rubric.yaml` / `data/rubric/rubric.md`. The six
fields (existing repository naming — kept as-is per project convention,
not renamed):

- `salary`, `duties`, `tools_or_skills`, `training_or_mentoring`,
  `probation_terms`, `employment_type`

Each gets exactly one status:

- **`confirmed`** — specific enough for an applicant to actually decide
  (e.g. an amount + unit for salary, a duration + pay/condition detail for
  probation).
- **`vague`** — related wording exists, but not specific enough to decide
  (e.g. "급여는 협의" — wording is present, decision-useful information is
  not). Distinguish "기재 있음" from "지원자가 판단할 수 있는 정보가 있음" —
  the former is not enough on its own.
- **`absent`** — no relevant wording at all.

Never write a company stability/growth/culture/risk opinion anywhere. Only
judge what the posting text actually says.

## 4. Writing evidence and offsets

- `evidence_text` must be an exact, verbatim, contiguous substring of the
  posting's real text — never paraphrased, never assembled from two
  separate spots.
- `offsets` is `[start, end]` such that `full_text[start:end] ==
  evidence_text` exactly (Python slicing: `end` is exclusive).
- `absent` rows must have `evidence_text: null` and `offsets: null`.
- `review_cli.py` does the offset lookup for you: paste the exact excerpt,
  it searches the source text and shows you the match (and every
  occurrence, with context, if the phrase repeats) — you only pick which
  one, never compute the numbers by hand.
- `reason_code` is required for every filled cell — a short phrase from the
  rubric criterion you applied (see `data/rubric/rubric.yaml`).
- `disagreement_note` (renamed `reviewer_note` in earlier task drafts — the
  existing schema's name is kept) is your own optional note on a boundary
  case, e.g. "unsure whether this counts as a named tool." It is not a gold
  decision by itself and is never read as one.

## 5. Validation command

Run this yourself before declaring your packet done, and again after any
edit:

```bash
python scripts/annotation_ops/validate_packets.py \
  --packet-a data/private/annotation_packets/annotator_A/packet.jsonl \
  --packet-b data/private/annotation_packets/annotator_B/packet.jsonl \
  --postings data/intake/real_postings.jsonl \
  --private-dir data/private/intake_raw \
  --expected-posting-count 20 \
  --allow-incomplete
```

(`--allow-incomplete` is fine while annotation is still in progress; drop
it once both packets are fully filled in — see the fail-closed table
below.) This checks, among other things: all 20 postings present, no
duplicate IDs, all six fields per posting, only the three allowed statuses,
every confirmed/vague evidence span matches the real text exactly, every
absent cell has null evidence, A and B are genuinely different files, no
AI-suggestion key leaked in, and (only relevant for this real-private-data
mode) that both packet files actually live at a gitignored path and that no
evidence text accidentally contains a phone number or email.

## 6. Producing the disagreement queue

Once **both** packets are 100% complete (`validate_packets.py` without
`--allow-incomplete` passes for both):

```bash
python scripts/annotation_ops/prepare_adjudication.py \
  --packet-a data/private/annotation_packets/annotator_A/packet.jsonl \
  --packet-b data/private/annotation_packets/annotator_B/packet.jsonl \
  --postings data/intake/real_postings.jsonl \
  --private-dir data/private/intake_raw \
  --out data/private/annotation_packets/adjudication_comparison.jsonl
```

This refuses to run (see fail-closed table) if either packet is incomplete
or fails validation. On success it writes:

- `adjudication_comparison.jsonl` — every cell, both raw labels, an
  `agreement` flag, agreement cells auto-filled into `adjudicated_*`.
- `adjudication_comparison_disagreements.jsonl` — only the rows where A and
  B disagree, so the adjudicator has a ready-made queue instead of
  filtering the full file by hand.

It also prints raw agreement count/percent (no Cohen's kappa here — that's
`scripts/data/adjudicate.py` / `scripts/data/aggregate_stats.py`'s job on a
finished gold set, once the sample size justifies it).

## 7. How the two people reconcile a disagreement

This step is **entirely human** — no script decides a disagreement.

1. A third person (or A and B together, whichever your team has agreed on)
   opens `adjudication_comparison.jsonl`, focusing on the rows listed in
   `..._disagreements.jsonl`.
2. For every disagreement row, fill in:
   - `adjudicated_status` (one of confirmed/vague/absent — the resolved
     answer)
   - `adjudicated_evidence_text` / `adjudicated_offsets` (required if
     confirmed/vague, both null if absent — same substring/offset rule as
     section 4)
   - `adjudicator_note` — **required, non-empty, and must not start with
     "auto-filled"** (that string is reserved for the agreement rows the
     tool already filled in; a real disagreement needs a real reason).
3. Agreement rows already have `adjudicated_*` auto-filled from the
   matching A/B answer — leave them alone unless you spot an error in both
   annotators' work, in which case treat it like a disagreement and leave a
   real note explaining the override.

## 8. Gold conditions (all must hold — a script checks the first, not the rest)

```bash
python scripts/annotation_ops/prepare_adjudication.py \
  --verify-final data/private/annotation_packets/adjudication_comparison.jsonl
```

This only checks: every row has a non-null `adjudicated_status` in the
allowed enum, every disagreement has a real (non-auto-filled)
`adjudicator_note`, and confirmed/vague rows carry evidence+offsets while
absent rows don't. Passing this is **necessary, not sufficient**, for
calling the batch gold. The remaining conditions are human judgment calls
that no script can verify:

- Both annotators actually worked independently (see section 2) —
  self-attested by whoever ran the sessions.
- The adjudicator actually looked at each disagreement rather than
  rubber-stamping one side.
- `human_boundary_review_completed` (see section 9) is `true`.

Only once **all** of the above hold may `data/intake/real_postings.jsonl`'s
labels be exported into `data/annotation/`-shaped gold files and fed to
`scripts/data/generate_splits.py --is-gold true` per `DATA_HANDOFF.md`'s
remaining-steps list.

## 9. `human_boundary_review_completed`

Lives in `data/intake/occupation_feasibility.json`, per candidate
(occupation, employment_type) group, and starts `null`. **No script in
this repository ever sets it to `true`.** It records a distinct,
non-count-based judgment from `TASK_REAL_DATA_ACQUISITION.md` Phase 2: that
a human has actually looked at the real batch and confirmed the
`tools_or_skills`/`duties` boundary is judgeable for this occupation in
practice (not just "10 postings exist").

Who/when: **the team lead or a designated reviewer, after at least a pilot
annotation pass on the real batch (not before)**, edits this field by hand
in `data/intake/occupation_feasibility.json` and records why in that same
review (e.g. a short note in a PR description or team log — this repo does
not prescribe where). This agent/tool session does not, and must not, flip
this field.

## 10. Never commit private text

- `data/private/**` is gitignored (`.gitignore` line `data/private/`).
  Verify before every commit:
  ```bash
  git ls-files data/private   # must print nothing
  ```
- Never `git add -f` anything under `data/private/**`.
- Every packet/validator/adjudication tool in this pipeline that touches
  real text (`--private-dir` mode) refuses to write its output anywhere
  that isn't actually gitignored — but that check is a safety net, not a
  substitute for checking `git status`/`git diff` yourself before every
  commit.
- If you ever need to share a real posting's text with a teammate for
  review, do it outside Git (a private message, a shared private doc you
  control access to) — never as a committed file, a public gist, or a code
  comment.

## 11. `is_gold: false` until labeling is actually finished

Any split/manifest file this pipeline produces before section 8's
conditions are fully met must carry `is_gold: false` (the default in every
existing script — `scripts/data/generate_splits.py` requires an explicit
`--is-gold true` to flip it, and nothing in this task changed that
default). Do not hand-edit a manifest to say `is_gold: true` to save a
step. If asked "is this gold yet," the honest answer is `data/intake/
occupation_feasibility.json`'s `human_boundary_review_completed` plus
whether `--verify-final` has passed on a real adjudicator-completed file —
not a feeling that "the numbers look done."

## Fail-closed guarantees (what the tools refuse, not just warn about)

| Situation | Tool | Behavior |
|---|---|---|
| A public posting has no matching private text file | `build_packets.py --private-dir`, `review_cli.py --private-dir`, `validate_packets.py --private-dir`, `prepare_adjudication.py --private-dir` | Raises `PrivateSourceError` naming every missing `posting_id`. Nothing is written. |
| Two private files claim the same `posting_id` | same four tools | Raises `PrivateSourceError`. Nothing is written. |
| A private file has no matching public posting (orphan) | same four tools | Raises `PrivateSourceError` by default; pass `--no-strict-private` to `build_packets.py` to downgrade to a printed warning instead (validators/adjudication always stay strict). |
| Packet output directory isn't actually gitignored | `build_packets.py --private-dir`, `validate_packets.py --private-dir` | Raises `PrivateSourceError` (checked via `git check-ignore`, not just the directory name). |
| `evidence_text`/`offsets` don't match the real text exactly | `validate_packets.py`, `prepare_adjudication.py` | Reported as a schema/evidence error; refuses to proceed to adjudication. |
| Either packet has any unanswered (`status: null`) cell | `prepare_adjudication.py` (queue-building mode) | Refuses with `REFUSED: ... has unanswered cells`. |
| A disagreement's `adjudicator_note` is empty or reuses the agreement auto-fill text | `prepare_adjudication.py --verify-final` | Reported as an error; not gold-ready. |
| Evidence text contains a phone number or email pattern | `validate_packets.py` | Reported as an error (defense in depth; the source intake step already best-effort redacts these, this catches anything that slipped through into a quoted excerpt). |
