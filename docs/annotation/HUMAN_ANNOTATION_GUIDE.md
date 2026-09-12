# Human annotation guide — annotator A / annotator B

Read this together with `data/rubric/rubric.md` (the criteria) and
`data/annotation/schema.md` (the exact record shape). This guide is only
about *how to run the tools and stay isolated from each other* — the rubric
document is the source of truth for what `confirmed` / `vague` / `absent`
mean.

**This guide describes a process. It does not itself produce gold labels.**
Per `DATA_HANDOFF.md`, nothing is gold until two humans have independently
labeled real postings and a human adjudicator has resolved every
disagreement.

## 0. Before you start

- You need: Python 3 with this repo's dependencies (`pyyaml` at minimum —
  already used elsewhere in the repo), a terminal, and the rubric
  (`data/rubric/rubric.md`).
- You do **not** need: the other annotator's file, `ai_suggestions.jsonl`,
  or any AI/LLM tool. Do not open `data/annotation/ai_suggestions.jsonl` or
  ask a model to pre-fill your answers — that is explicitly disallowed
  (see `CLAUDE.md` and `TASK_ANNOTATION_WORKFLOW_PREP.md`: "Claude/LLM 두
  개를 돌린 결과는 '두 명의 사람' 라벨이 아닙니다").
- Someone (the run coordinator) must have already run `build_packets.py`
  once and given you the path to **your own** packet only. If you were
  handed both `annotator_A/packet.jsonl` and `annotator_B/packet.jsonl`,
  stop and tell the coordinator — you should only ever receive one.

## 1. Commands each annotator runs

Both annotators run the *same* command shape, pointed at their own packet.
Nothing here differs between A and B except the file path.

```bash
# Annotator A:
python scripts/annotation_ops/review_cli.py \
  --packet data/private/annotation_run_001/annotator_A/packet.jsonl \
  --postings /path/to/real_postings.jsonl

# Annotator B (separate terminal / separate machine, at any time):
python scripts/annotation_ops/review_cli.py \
  --packet data/private/annotation_run_001/annotator_B/packet.jsonl \
  --postings /path/to/real_postings.jsonl
```

For every cell the CLI shows the full posting text and the field you're
coding, then asks:

1. `status` — type `confirmed`, `vague`, or `absent` (or `skip` to leave it
   for later, or `quit` to stop the session).
2. `reason_code` — a short phrase naming which rubric criterion you applied
   (e.g. `amount_and_unit_present`, `duration_only_no_pay_detail`,
   `deferred_to_interview`, `no_relevant_text`). Free text, but make it
   specific enough that someone reading it later can trace your reasoning
   back to the rubric.
3. An optional note (blank is fine).
4. If you said `confirmed` or `vague`: paste the **exact** excerpt from the
   posting text shown above. The tool searches for it verbatim and computes
   the offsets for you — you never type numbers by hand. If your excerpt
   isn't found (typo, extra/missing space, different quote character), it
   asks again. If it appears more than once in the text, it shows you each
   occurrence with a bit of surrounding context and asks which one you
   meant.

The packet file is saved to disk after every single cell you answer, so you
can stop at any time (including `Ctrl+C`) and resume later by re-running the
exact same command — already-answered cells are skipped automatically. Use
`--redo` only if you want to revisit cells you already answered.

## 2. How A and B stay isolated

- You are only ever given your own packet file. Never open, request, or
  peek at the other annotator's `packet.jsonl`.
- Do not discuss specific cells with each other until *after* both files
  are complete and validated. Discussing "what did you put for JB-014
  salary?" mid-annotation defeats the point of independent labeling.
- `review_cli.py` structurally cannot show you the other file or AI
  suggestions — it only ever reads the one `--packet` path you give it and
  the shared (unlabeled) posting text. But the tool can't stop you from
  talking to your co-annotator, so don't.
- If you and your co-annotator are annotating on a shared machine or repo
  checkout, keep your two packet files in genuinely separate paths (e.g.
  `annotator_A/` vs `annotator_B/`, as `build_packets.py` already lays them
  out) and don't `cat`/copy one into the other.

## 3. Boundary cases per field (quick reference)

See `data/rubric/rubric.md` for full definitions and positive examples.
These are the cases annotators most often disagree on:

- **salary** — "회사 내규에 따라 지급" or "경력에 따라 협의" is `vague`
  (pay is mentioned, no number is recoverable), not `confirmed`. A number
  with no unit, or a unit with no number, is also not `confirmed` — the
  deterministic check requires both in the same span.
- **duties** — "생산 관련 업무 전반을 수행합니다" is `vague` (a job family,
  no concrete task). It becomes `confirmed` only once a specific
  process/product/line is named.
- **tools_or_skills** — personality traits ("성실한 분", "책임감 있는 분")
  are never `tools_or_skills`, no matter how specific-sounding the sentence
  is. "관련 경험자 우대" with no named tool/certification is `vague`.
- **training_or_mentoring** — "체계적인 교육 시스템 운영" is `vague` (claims
  training exists, no structure). It's `confirmed` only with a named
  duration or mentor structure (e.g. "2주간 사수와 1:1 OJT").
- **probation_terms** — this is the field most often mis-coded. A duration
  alone ("수습기간 3개월") is `vague`, **not** `confirmed`. `confirmed`
  requires both a duration **and** a pay/condition detail in the same span
  (e.g. "수습기간 3개월, 급여는 본급의 90% 지급").
- **employment_type** — "채용형태는 면접 후 결정" is `vague` (no type named
  yet). Any named type (정규직/계약직/인턴 등), even with conditions attached
  ("계약직 1년 후 정규직 전환 가능"), is `confirmed`.

General rule behind all of the above: **the presence of related words is not
the same as the presence of decision-useful information.** When in doubt,
ask "could an applicant use this specific text to make a decision?" — if
not, it's `vague`, not `confirmed`.

## 4. Evidence selection examples

- Prefer the smallest span that still contains everything the deterministic
  check needs. For `probation_terms confirmed`, "수습기간 3개월, 수습기간
  중 급여는 본급의 90% 지급" is a better evidence span than the whole
  paragraph around it — it's still an exact substring, but it makes review
  easier later.
- If the same phrase appears twice in a posting (e.g. "지게차" mentioned in
  both a duties sentence and a separate skills line), the tool will list
  both occurrences with context and ask you to pick the one that's actually
  relevant to the field you're coding.
- Do not paraphrase, translate, or fix typos in the evidence text you paste
  — it must match the source text byte-for-byte, because
  `scripts/data/validate_dataset.py` checks `full_text[start:end] ==
  evidence_text` exactly.

## 5. When you're done

1. Run the completion/isolation check on both files together (this is
   normally run by the run coordinator once both annotators report done,
   but you can run it yourself too):

   ```bash
   python scripts/annotation_ops/validate_packets.py \
     --packet-a data/private/annotation_run_001/annotator_A/packet.jsonl \
     --packet-b data/private/annotation_run_001/annotator_B/packet.jsonl \
     --postings /path/to/real_postings.jsonl
   ```

   Fix any `ERROR` lines it prints (usually a missed cell, a bad offset, or
   a missing `reason_code`) before handing your file off.

2. Hand your **own** packet file to the run coordinator (e.g. by committing
   it to the private/non-redistributed location it lives in, or however
   your team moves files) once it passes validation with no `--allow-incomplete`
   flag needed. Do not hand off a file you haven't run validation on.

3. The coordinator runs adjudication once *both* files are complete and
   validated:

   ```bash
   python scripts/annotation_ops/prepare_adjudication.py \
     --packet-a data/private/annotation_run_001/annotator_A/packet.jsonl \
     --packet-b data/private/annotation_run_001/annotator_B/packet.jsonl \
     --postings /path/to/real_postings.jsonl \
     --out data/private/annotation_run_001/adjudication_comparison.jsonl
   ```

   This refuses to run at all if either file is incomplete or fails
   validation. It writes the full comparison file (agreements auto-filled)
   plus a separate disagreement-only review queue for the human adjudicator.

## 6. Privacy / handling rules

- Never write your name, email, employee ID, or any other personal
  identifier into `reason_code`, `disagreement_note`, or `adjudicator_note`.
  These files may be shared beyond the immediate team.
- Never write an API key, service key, or credential into any annotation
  file, note, or commit message — including the `data.go.kr` key used to
  fetch postings. Keys belong in local environment variables / an untracked
  secrets file, never in `data/**` or a git commit.
- Do not copy real posting full text into a location outside where the run
  coordinator placed it (e.g. don't paste it into chat, a spreadsheet, or a
  public issue) unless you've confirmed redistribution rights for that
  source — see `data/README.md` and `data/sources/source_inventory.yaml`.
