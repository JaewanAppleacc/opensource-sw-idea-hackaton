# ⚠️ NOT GOLD — synthetic/demo data, pipeline-verification report

**This report is generated from a non-gold, synthetic/demo adjudicated file.** It exists only to prove the statistics and reporting code runs correctly end to end. It is not a claim about real Jeonbuk or metropolitan postings. See `DATA_HANDOFF.md` for what real annotation work remains.

**exploratory sample; not population-generalizable**

## Sample
- Sample size: 22 postings (132 audited cells)
- Posting count by region: {'jeonbuk': 11, 'metro': 11}
- Data source: synthetic_fixture_v1 (see data/sources/source_inventory.yaml)
- Collection period: n/a (synthetic fixtures; no real collection period)
- Occupation(s): 생산직(제조 조립원)
- Employment type(s): 계약직, 정규직
- Rubric version: 1.0.0-draft

## Status proportions by region and field

| Region | Field | confirmed | vague | absent | n |
|---|---|---|---|---|---|
| jeonbuk | duties | 64% | 18% | 18% | 11 |
| jeonbuk | employment_type | 73% | 18% | 9% | 11 |
| jeonbuk | probation_terms | 18% | 36% | 45% | 11 |
| jeonbuk | salary | 45% | 36% | 18% | 11 |
| jeonbuk | tools_or_skills | 36% | 27% | 36% | 11 |
| jeonbuk | training_or_mentoring | 27% | 9% | 64% | 11 |
| metro | duties | 82% | 9% | 9% | 11 |
| metro | employment_type | 91% | 9% | 0% | 11 |
| metro | probation_terms | 64% | 18% | 18% | 11 |
| metro | salary | 82% | 18% | 0% | 11 |
| metro | tools_or_skills | 55% | 27% | 18% | 11 |
| metro | training_or_mentoring | 55% | 18% | 27% | 11 |

## Matched-pair descriptive differences (per field, share of pairs where the two postings' statuses differ)

| Field | Pairs compared | Differ rate |
|---|---|---|
| salary | 10 | 60% |
| duties | 10 | 40% |
| tools_or_skills | 10 | 70% |
| training_or_mentoring | 10 | 80% |
| probation_terms | 10 | 90% |
| employment_type | 10 | 20% |

These are descriptive differences within this specific matched sample only. They are not a statement about typical postings in either region.

## Unmatched records
- Unmatched count: 2
  - JB-011 (jeonbuk): no candidate found under recorded query (occupation=농산물 가공 생산직, employment_type=계약직 combination has no metropolitan fixture in this build)
  - MET-011 (metro): no candidate found under recorded query (employment_type=계약직 has no Jeonbuk 생산직 fixture in this build; the Jeonbuk contract-type pool used a different sub-occupation, see JB-011)
- Unmatched records are observations only. They must not be interpreted as evidence of regional job scarcity.

## Status
- is_gold=false: these statistics are computed from a NON-GOLD synthetic/demo adjudicated file and exist only to prove the statistics code path works. They are not a claim about real Jeonbuk or metropolitan postings.
