# Electronics R&D demo pair (second active pair)

Checked and manually ingested from the public 고용24 detail pages on
2026-09-13. This is the second real research-job demo pair, added alongside
the representative food R&D pair (`P-REAL-011`, see
`RESEARCH_DEMO_PAIR.md`). It does not replace or expand the claims made from
the existing 10:10 production/assembly evaluation sample.

| | Metropolitan posting | Jeonbuk posting |
|---|---|---|
| Project ID | `MET-11` | `JB-11` |
| Matched pair ID | `P-REAL-012` | `P-REAL-012` |
| Company | 주식회사 파이온시스템즈 | 주식회사 모스터일렉 |
| Municipality | 경기도 성남시 수정구 달래내로 46, 성남글로벌융합센터 A동 807호 (시흥동) | 전북특별자치도 전주시 덕진구 가인로 16, 301호 (만성동) |
| Work24 모집직종 (primary) | 전자공학 기술자 및 연구원 | 전자공학 기술자 및 연구원 |
| Employment type | 기간의 정함이 없는 근로계약 | 기간의 정함이 없는 근로계약 |
| Pay | 연봉 5,000만원 이상 (협의가능) | 연봉 4,000만원~5,000만원 |
| Working time | 주 5일·주 40시간 | 주 5일·주 40시간 |
| Career/education | 경력 최소 3년 이상 필수, 대졸(2~3년)~석사 | 경력 무관, 고졸~박사 |
| Stated duties | FPGA RTL 로직 개발, 펌웨어·임베디드 SW 개발, RF회로 개발, 드론·안티드론 시스템 개발 (설계 및 구현) | 전자 관련 의료기기 제품 및 컨트롤러·헬스케어 제품 개발과 양산 관련 업무 |
| Source | [Work24 detail](https://www.work24.go.kr/wk/a/b/1500/empDetailAuthView.do?infoTypeCd=VALIDATION&infoTypeGroup=tb_workinfoworknet&wantedAuthNo=K170052607310023) | [Work24 detail](https://www.work24.go.kr/wk/a/b/1500/empDetailAuthView.do?infoTypeCd=VALIDATION&infoTypeGroup=tb_workinfoworknet&wantedAuthNo=K161132609080028) |

## Why this pair was accepted

- Both postings carry the **identical, official Work24 모집직종 (primary
  occupation classification) field** — "전자공학 기술자 및 연구원" — not
  merely a shared "관련 직종" (related-occupation) tag. This was verified by
  opening each posting's own 모집요강 table directly, not inferred from a
  keyword search match.
- Both use the same open-ended employment category ("기간의 정함이 없는
  근로계약" — normalized here to "정규직", matching the convention used for
  `P-REAL-011`).
- Both state real, verifiable R&D duty text meeting the task's evidence bar
  (설계·개발 / 기술 개발 / 제품 개발): FPGA·RTL/임베디드 회로 설계 on the
  metro side, medical-device/controller product development on the Jeonbuk
  side.
- Both are genuine, self-registered 고용24 postings (`infoTypeCd=VALIDATION`,
  `infoTypeGroup=tb_workinfoworknet`), the highest-priority source tier per
  the task's source rules — not a private-platform-linked listing.

## Rejected near-candidates (for transparency)

Several other postings surfaced under the same "전자공학 기술자 및 연구원"
keyword/category search were checked and **rejected** because their own
모집직종 field turned out to be a different, more specific classification
(with "전자공학 기술자 및 연구원" appearing only as a secondary "관련 직종"
tag, not the primary code) — a keyword or category search alone was not
sufficient evidence, and each candidate's own detail page had to be opened to
confirm the primary field:

- (주)비케이에너지 (서울, R&D 연구원) — primary 모집직종 was actually
  "전기공학 기술자 및 연구원".
- 주식회사 한성테크 (경기 김포, 연구소 엔지니어) — primary 모집직종 was also
  "전기공학 기술자 및 연구원".
- 카멜테크(주) (경기 부천, 부설연구소 SMPS 연구원) — primary 모집직종 was
  "전기기기·제품 개발 기술자 및 연구원".
- (주)태강전기 (경기 용인, 전력전자 시험·검증 엔지니어) — primary 모집직종
  was also "전기기기·제품 개발 기술자 및 연구원".
- 주식회사 코스테크 (전북 전주, PLC/자동제어 경력자) — primary 모집직종 was
  "전기계측 제어 기술자".

These were not discarded from the search log for being "worse" candidates;
they were excluded strictly because their own official occupation
classification did not match, per the task's deterministic-matching rule
("정규화된 직종명 + 고용형태가 동일" — normalized occupation name +
employment type identical). They remain a useful record of how granular
Work24's own occupation taxonomy is within the "연구 및 공학기술" family, and
why a same-primary-code match is genuinely hard to find at volume.

The full manually transcribed text remains only in the gitignored private
intake directory (`PRIVATE_INTAKE_RAW_DIR`) once staged; it has not been
staged on this machine, so `full_text_sha256` is `null` for both records
until that step happens. The public JSONL contains metadata and source links
only.
