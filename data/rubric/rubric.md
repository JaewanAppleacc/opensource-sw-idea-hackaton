# Six-field audit rubric (human-readable) — v1.0.0-draft

Machine-readable source of truth: `data/rubric/rubric.yaml`. If the two ever
disagree, the YAML wins and this file should be regenerated/updated to match.

## Controlling principle

> Distinguish wording being present from decision-useful information being
> present.

A posting can mention a topic in passing ("복지 우수") without giving the
applicant anything they could act on. That is `vague`, not `confirmed`, even
though words exist.

## Statuses (exactly three — no others)

| Status | Meaning |
|---|---|
| `confirmed` | Specific enough that the applicant could use it to decide. |
| `vague` | Related wording exists, but it isn't specific enough to decide. |
| `absent` | No relevant wording at all. |

`external_verified` is **not** a status. External context (e.g. public pay
statistics, National Pension enrollment counts) never changes a field from
`vague`/`absent` to `confirmed` — it lives in a separate `ExternalContext`
object, not in the audited field.

System failures (`analysis_failed`, `invalid_input`, `provider_unavailable`,
`schema_validation_failed`, …) are not posting statuses either. They belong
in a typed error, never in a field's `status`.

## The six fields

### 1. `salary`
- **confirmed**: a number or range plus a unit (원/만원/연봉/월급/시급) — enough
  to estimate take-home pay.
  - e.g. "월급 260만원(세전) 지급", "연봉 3,200만원 수준"
- **vague**: pay is mentioned but no number is recoverable ("회사 내규에 따라
  지급", "협의 후 결정").
- **absent**: no compensation wording at all.
- Deterministic check: a `confirmed` evidence span must contain at least one
  digit **and** one unit token. A span with a unit but no digit (or vice
  versa) should not pass as `confirmed` — send it back to `vague`.

### 2. `duties`
- **confirmed**: a concrete task or process ("완성차 부품 조립 및 품질 검사
  업무").
- **vague**: a job family with no concrete task ("생산 관련 업무 전반").
- **absent**: no description of the work.

### 3. `tools_or_skills`
- **confirmed**: names a specific tool, machine, certification, or skill
  (지게차 면허, PLC, 캘리퍼스, 도면 해독).
- **vague**: "관련 경험자 우대" with nothing named.
- **absent**: nothing at all.
- Occupation mapping for 생산직(제조 조립원): personality traits ("성실함",
  "책임감") are never `tools_or_skills`.

### 4. `training_or_mentoring`
- **confirmed**: a named structure with duration/cadence ("입사 후 2주간
  사수와 1:1 현장 OJT", "매월 1회 정기 안전교육").
- **vague**: training is claimed with no structure ("체계적인 교육 시스템
  운영").
- **absent**: no mention.

### 5. `probation_terms`
- **confirmed**: duration **and** pay/condition detail together ("수습기간 3
  개월, 수습기간 중 급여는 본급의 90% 지급"). Duration alone is not enough.
- **vague**: duration only, or "수습기간 있음" with no duration/pay detail.
- **absent**: no mention of probation.
- This is the field most likely to be mis-coded as `confirmed` from duration
  alone — the deterministic check specifically requires both a duration
  token (개월/주) and a pay/condition token (%, 급여, 지급, 동일) in the same
  evidence span.

### 6. `employment_type`
- **confirmed**: names an actual type ("정규직", "계약직(1년, 이후 정규직 전환
  가능)").
- **vague**: "면접 후 결정" with nothing named.
- **absent**: no mention.

## Occupation-specific field mapping

The rubric's language above is written for the MVP occupation, **생산직
(제조 조립원)**. If the occupation changes (see
`data/occupation_selection.md`), re-derive this mapping before annotating —
do not assume the same keyword list transfers. In particular:

- `tools_or_skills` must be re-scoped to whatever tools/certifications are
  actually relevant to the new occupation (e.g. for a call-center role this
  might be CRM software or a language certificate instead of 지게차/PLC).
- `training_or_mentoring` structures differ by occupation (a shift-based
  factory OJT looks different from a service-role shadowing period).
- If a field genuinely has no applicable concept for an occupation (rare),
  do not silently code it `absent` — flag it in the rubric note for that
  occupation instead, so annotators don't conflate "not applicable" with
  "the poster left it out."

## Versioning

Bump `rubric_version` (semver-ish, e.g. `1.0.0-draft` → `1.1.0`) whenever
criteria, examples, or deterministic checks change. Every annotation,
adjudication, split manifest, and report must record the rubric version it
was produced under — see `scripts/data/validate_dataset.py`.
