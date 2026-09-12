# Parallel task D1: 실제 채용공고 확보·출처 검증

이 작업은 `TASK_ANNOTATION_WORKFLOW_PREP.md`와 동시에 진행할 수 있습니다. 먼저 `CLAUDE.md`, `DATA_HANDOFF.md`, `data/sources/source_inventory.yaml`, `data/postings/README.md`를 전부 읽으십시오.

## 목표

동일 출처·수집기간·직종·고용형태 기준으로 전북과 수도권 채용공고를 최소 10:10, 목표 20:20 확보하고, 각 레코드의 출처와 재배포 가능 범위를 기록합니다. 실제 표본을 확인한 뒤에만 직종을 확정합니다.

이 작업은 웹 스크래핑 작업이 아닙니다. 허용 경로는 다음 둘뿐입니다.

1. 승인된 고용24/워크넷 등 공공 API
2. 팀원이 공유 권한을 확인해 직접 제공한 공고

사람인·잡코리아·잡플래닛 등 민간 플랫폼을 자동 수집하지 마십시오.

## 브랜치와 소유 범위

- 브랜치: `feature/real-data-acquisition`
- 수정 가능: `scripts/acquisition/**`, `tests/acquisition/**`, `docs/acquisition/**`, `data/intake/**`, `data/sources/source_inventory.yaml`, `data/occupation_selection.md`, `REAL_DATA_ACQUISITION_HANDOFF.md`
- 수정 금지: `frontend/**`, `backend/**`, `contracts/**`, `data/annotation/**`, 기존 `data/postings/postings.jsonl`
- 실제 데이터가 검증되기 전에는 합성 corpus를 덮어쓰지 마십시오.

## 비밀정보 규칙

- API 키는 `WORK24_SERVICE_KEY` 같은 환경변수로만 읽습니다.
- 키, 요청 헤더, 키가 포함된 URL을 로그·테스트 fixture·handoff·Git에 기록하지 마십시오.
- `.env`를 커밋하지 마십시오.
- 권리가 확인되지 않은 원문은 Git에 넣지 말고 `.gitignore`의 `data/private/**`에 저장합니다.

## 작업 순서

### 0. 접근 가능성 확인

공식 문서에서 다음을 당일 기준으로 다시 확인하고 URL·확인일을 기록합니다.

- API 이름과 운영기관
- 인증 방식과 승인 상태
- 호출 제한
- 지역·직종·고용형태 필드
- 원문 또는 상세 직무내용 제공 여부
- 각 필드의 저장·가공·재배포 가능 여부

문서에서 확인되지 않은 권리를 추정하지 마십시오. 키가 없으면 수집에 성공한 척하지 말고, 재현 가능한 클라이언트와 정확한 차단 사유까지만 완성합니다.

### 1. 재현 가능한 수집기

공식 응답을 작은 내부 모델로 정규화하는 CLI를 만듭니다. endpoint와 파라미터 이름은 실제 공식 문서를 확인한 뒤 사용하고 임의로 만들지 마십시오.

필수 기능:

- 전북과 수도권을 같은 기간 기준으로 조회
- 원본 응답은 `data/private/**`에 저장 가능
- 공개 가능한 정규화 결과는 JSONL로 생성
- pagination, timeout, rate limit, 중복 ID 처리
- 네트워크 실패와 인증 실패를 구분한 안전한 오류
- 키가 로그에 나오지 않는 테스트
- `--dry-run` 또는 fixture 기반 오프라인 테스트

### 2. 직종 feasibility를 먼저 측정

`생산직(제조 조립원)`을 확정값으로 가정하지 마십시오. 팀이 판정 가능한 후보 직종별로 다음 raw count를 기록합니다.

- 전북 유효 공고 수
- 수도권 유효 공고 수
- 정규직 등 동일 고용형태 수
- 6필드 실사에 쓸 수 있을 만큼 원문이 있는 공고 수
- 동일 수집기간 조건을 만족한 수

선정 조건은 둘 다 충족해야 합니다.

1. 최소 10:10, 가능하면 20:20 실제 표본 확보
2. 팀이 해당 직종의 `tools_or_skills`, `duties` 경계를 사람 검수할 수 있음

충족하지 않으면 후보별 실제 count와 탈락 사유를 남기고 직종을 바꿉니다.

### 3. 정규화 및 페어링

공개 가능할 때만 `data/intake/real_postings.jsonl`과 `data/intake/real_matched_pairs.jsonl`을 만듭니다. 스키마는 `data/postings/README.md`를 따르고 다음을 추가로 보장합니다.

- `synthetic_test_fixture: false`
- 실수집일 `collection_date`
- `source_name`, 안정적인 `source_id_url`
- `redistributable`을 레코드별로 명시
- 공고 ID, 기업명, 원문의 PII/민감정보 점검
- pair는 같은 직종·고용형태·유사 수집기간
- unmatched는 관찰 사실만 기록하고 “전북 일자리 부족 때문” 같은 해석 금지

원문 재배포가 불가하면 public JSONL에는 원문을 넣지 말고 source ID/URL, 파생 메타데이터, checksum만 둡니다. 라벨링용 원문은 `data/private/**`에서만 사용합니다.

### 4. 검증

- 중복, 빈 원문, 지역 오류, pair 역참조 오류 테스트
- 표본 수와 기간 분포를 raw count로 출력
- `python -m pytest tests/acquisition -q`
- 기존 `python -m pytest tests/backend tests/data -q` 회귀 통과
- 비밀정보 검색 및 `git diff --check`

## 산출물

1. 수집기와 오프라인 fixture 테스트
2. `data/intake/source_terms_snapshot.yaml`
3. `data/intake/occupation_feasibility.json`
4. 권리가 확인된 경우에만 real postings/pairs JSONL
5. `REAL_DATA_ACQUISITION_HANDOFF.md`

handoff에는 반드시 다음 판정을 하나 명시합니다.

- `READY_FOR_HUMAN_ANNOTATION`
- `BLOCKED_NO_CREDENTIAL`
- `BLOCKED_INSUFFICIENT_SAMPLE`
- `BLOCKED_LICENSE_OR_MISSING_TEXT`

## 완료 기준

코드 작성만으로 `READY_FOR_HUMAN_ANNOTATION`을 선언하지 마십시오. 실제 10:10 공고, 동일 조건, 원문 접근, 출처·권리 기록이 모두 존재해야 합니다. 그렇지 않으면 정확한 blocker와 사람이 해야 할 다음 행동을 남기는 것이 올바른 완료입니다.

## Claude Code 시작 프롬프트

```text
저장소의 CLAUDE.md, DATA_HANDOFF.md, TASK_REAL_DATA_ACQUISITION.md를 전부 읽고 feature/real-data-acquisition 브랜치에서 작업해. 허용된 공공 API 또는 사용자가 공유 권한을 확인한 입력만 사용하고 민간 채용사이트를 스크래핑하지 마. API 키는 환경변수로만 읽고 키나 권리 미확인 원문을 Git에 넣지 마. 실제 표본을 얻기 전에는 합성 data/postings를 덮어쓰지 말고, 완료 시 REAL_DATA_ACQUISITION_HANDOFF.md에 READY 또는 정확한 BLOCKED 상태를 기록한 뒤 테스트·커밋·push까지 해줘.
```
