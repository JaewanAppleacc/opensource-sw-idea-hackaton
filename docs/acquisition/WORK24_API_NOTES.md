# 고용24/워크넷 채용정보 Open API — research notes (checked 2026-09-12)

This documents what was re-confirmed today about the public API path named
in `TASK_REAL_DATA_ACQUISITION.md` as allowed access route #1, and exactly
why it is still not usable without a human completing a signup step. Nothing
below is inferred — each claim is what a fetched public page states.

## What changed since the previous check

The earlier `data/sources/source_inventory.yaml` entry (2026-09-12, prior
pass) named the API only as "고용24 / 워크넷 채용정보 Open API". Fetching
`http://openapi.work.go.kr/opiMain.do` today shows:

> "워크넷 OPEN-API서비스가 종료되었습니다" (the WorkNet Open API service has
> ended) — "워크넷 OPEN-API서비스가 고용24 OPEN-API로 통합되었습니다" (it has
> been merged into the 고용24 (Work24) Open API).

The successor portal is `https://www.work24.go.kr/cm/e/a/0110/selectOpenApiIntro.do`.

## What is confirmed from official public pages

- Work24 publicly documents the 채용정보 list endpoint as
  `https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210L01.do`
  and the detail endpoint as
  `https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210D01.do`.
- The list's required core parameters include `authKey`, `callTp=L`,
  `returnType=XML`, `startPage`, and `display`; public filters include
  `region` and `occupation`.
- The detail request requires `authKey`, `wantedAuthNo`, `callTp=D`,
  `returnType=XML`, and `infoSvc=VALIDATION` for WorkNet-validated postings.
- XML is the required response format. The detail documentation lists fields
  including `wantedAuthNo`, `corpNm`, `wantedTitle`, `jobsNm`, `jobCont`,
  `empTpNm`, `salTpNm`, `certificate`, `compAbl`, `pfCond`, `etcPfCond`,
  `workRegion`, `workdayWorkhrCont`, and `etcWelfare`.
- The official detail-service page requires a link back to the Work24 detail
  page and Work24 attribution, and says unauthorized copying/distribution is
  prohibited. Therefore this repository must default full posting text to
  non-redistributable unless approved-use terms explicitly permit publishing it.

## What is still NOT confirmed (and must not be guessed)

- The complete list-filter code values and their behavior for the team's exact
  occupation/employment-type sampling rule.
- The precise XML nesting/pagination behavior observed with an approved key.
- The final mapping from every live XML tag to the project's normalized schema.
- The specific approved-use terms attached to the team's issued key.

The public specification is sufficient to identify the service, but not to
claim that this repository's adapter has been validated end-to-end.
`scripts/acquisition/work24_endpoint_config.yaml` records the public facts and
keeps `verified: false`; live mode remains locked until a human supplies an
approved key, captures a small response, completes the field mapping, and
tests it. The manual-intake path remains the active hackathon route.

## What to do once a key is issued

1. Confirm the approved service includes 채용정보목록 and 채용정보상세.
2. Capture one list and one detail XML response, then fill only the still-null
   filters and `response_field_map` values from observed tags.
3. Re-read the approved-use terms and update this file
   and `data/sources/source_inventory.yaml` with the confirmed text.
4. Set `WORK24_SERVICE_KEY` as an environment variable only (never commit
   it, never put it in a fixture, log line, or this documentation).
5. Run `python scripts/acquisition/work24_client.py --region jeonbuk ...`
   (see the script's module docstring for full usage) for a small page
   first, and sanity-check normalized output before a full pull.

## Current status

`BLOCKED_NO_CREDENTIAL` for live collection specifically. The team has instead
chosen the manual-intake path (`docs/acquisition/MANUAL_INTAKE_GUIDE.md`)
for this pass — see `REAL_DATA_ACQUISITION_HANDOFF.md` for the overall
acquisition decision.
