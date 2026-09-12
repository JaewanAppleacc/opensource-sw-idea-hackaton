# Manual posting intake guide (Parallel task D1)

This is the currently-active real-data acquisition path: a team member who
can personally confirm they are authorized to share a posting (their own
screen view of a real listing) copies the text into the template below.
This is **not** a scraping tool and does not replace the 고용24/워크넷 Open
API path — see `docs/acquisition/WORK24_API_NOTES.md` for why that path is
still blocked on a human credential step. `사람인`/`잡코리아`/`잡플래닛`
postings must not be collected this way either — see
`data/sources/source_inventory.yaml` ("excluded_by_policy").

## Sampling rule (read this before collecting anything)

Fix the rule before picking any postings, so the resulting comparison is
not biased toward postings that merely look "richer":

1. Pick one search site/query per region (고용24 preferred if reachable),
   the same occupation keyword, the same employment type filter.
2. Sort results by most recent first.
3. Take postings from the top of that sorted list, in order, until you
   reach the target count for each region. Do not skip a posting because it
   looks vague or incomplete, and do not skip ahead to a posting because it
   looks unusually detailed.
4. If a posting must be skipped (duplicate company/listing, wrong
   employment type, wrong occupation, posting text no longer available),
   record it with `status: excluded` and a one-line factual
   `excluded_reason` — never a reason like "정보가 부족해서" or an inference
   about why Jeonbuk has fewer postings.

Recommended batch sizes (per `TASK_REAL_DATA_ACQUISITION.md`):

| Purpose | Metro | Jeonbuk |
|---|---|---|
| Demo only | 1 | 2 |
| Minimal case validation | 5 | 5 |
| Meets the documented design minimum | 10 | 10 |
| Target | 20 | 20 |

## Template — one posting per file

```text
posting_id: JB-01
region_group: jeonbuk
municipality: 전주시
source_name: 고용24
source_url: https://...
collection_date: 2026-09-12
occupation: 생산직(제조 조립원)
employment_type: 정규직
company_name: 실제 회사명
redistribution_permission: unknown
--- FULL TEXT ---
여기에 화면에서 확인되는 채용공고 본문을 그대로 붙여넣기
```

Use `MET-01`, `MET-02`, … for metropolitan postings and `JB-01`, `JB-02`, …
for Jeonbuk postings.

## Template — multiple postings in one file

```text
===== JB-01 =====
posting_id: JB-01
region_group: jeonbuk
municipality: 전주시
source_name: 고용24
source_url: https://...
collection_date: 2026-09-12
occupation: 생산직(제조 조립원)
employment_type: 정규직
company_name: 실제 회사명
redistribution_permission: unknown
--- FULL TEXT ---
공고 내용...

===== MET-01 =====
posting_id: MET-01
region_group: metro
...
--- FULL TEXT ---
공고 내용...
```

## Excluding a candidate instead of collecting it

```text
===== SKIPPED-01 =====
status: excluded
excluded_reason: 중복 공고 (JB-01과 동일 채용ID)
```

`excluded_reason` must be a factual, observable reason (중복, 계약직, 직종
불일치, 원문 삭제됨 등) — never an interpretation of *why* a region has
fewer postings.

## Field notes

- `redistribution_permission`: `yes` / `no` / `unknown`. Default to
  `unknown` unless you have specifically confirmed the posting may be
  redistributed (e.g. a public-API field vs. a private site's full text).
  `unknown` and `no` both keep the full text out of the public JSONL —
  see below.
- Screenshots are discouraged; plain text is required so evidence offsets
  for the six-field audit can be computed exactly.
- You may remove phone numbers, emails, and the named contact person before
  pasting — the intake tool also best-effort redacts phone numbers and
  emails automatically. Company name should be preserved for the analysis
  step; it can be anonymized later for a public demo.
- Copy the posting text verbatim. Do not summarize or paraphrase it.
- Always record the real `source_url` and `collection_date`.
- Real posting text never goes directly into a Git-tracked public path.
  Ingestion writes the full text to `data/private/intake_raw/<posting_id>.json`
  (gitignored) always, and to the public `data/intake/real_postings.jsonl`
  only when `redistribution_permission: yes` — otherwise the public record
  keeps only `source_id_url`, derived metadata, and a SHA-256 checksum of
  the text, per `TASK_REAL_DATA_ACQUISITION.md` section 3.

## Running the ingestion

```bash
python scripts/acquisition/manual_intake.py --in path/to/your_file.txt --dry-run   # validate first
python scripts/acquisition/manual_intake.py --in path/to/your_file.txt             # writes real records
python scripts/acquisition/pair_postings.py                                        # pairs jeonbuk <-> metro
python scripts/acquisition/measure_feasibility.py                                  # raw-count feasibility report
```

`manual_intake.py` refuses to write anything if any block in the file fails
validation (missing field, bad date, duplicate `posting_id`, empty full
text) — fix every reported error and re-run.
