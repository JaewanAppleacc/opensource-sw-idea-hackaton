# Parallel task D2: 2인 독립 라벨링 운영 준비

이 작업은 `TASK_REAL_DATA_ACQUISITION.md`와 동시에 진행할 수 있습니다. 실제 공고를 판정하거나 gold를 만드는 작업이 아니라, 실제 데이터가 도착하는 즉시 두 사람이 독립적으로 검수할 수 있는 도구와 절차를 완성하는 작업입니다.

먼저 `CLAUDE.md`, `DATA_HANDOFF.md`, `data/rubric/rubric.yaml`, `data/rubric/rubric.md`, `data/annotation/schema.md`, `scripts/data/generate_annotation_templates.py`, `scripts/data/adjudicate.py`, `scripts/data/validate_dataset.py`를 전부 읽으십시오.

## 브랜치와 소유 범위

- 브랜치: `feature/annotation-workflow-prep`
- 수정 가능: `scripts/annotation_ops/**`, `tests/annotation_ops/**`, `docs/annotation/**`, `ANNOTATION_WORKFLOW_HANDOFF.md`
- 필요한 경우 기존 `scripts/data/generate_annotation_templates.py`, `scripts/data/adjudicate.py`, `scripts/data/validate_dataset.py`에는 최소 변경만 허용
- 수정 금지: `frontend/**`, `backend/**`, `contracts/**`, `data/postings/**`, `data/intake/**`, 실제 annotator 결과 파일

## 절대 원칙

- Claude/LLM 두 개를 돌린 결과는 “두 명의 사람” 라벨이 아닙니다.
- annotator A와 B는 서로의 결과 및 `ai_suggestions.jsonl`을 보지 않습니다.
- confirmed/vague 근거는 원문 exact substring과 `[start,end)` offset이 필수입니다.
- absent는 evidence와 offsets가 모두 null이어야 합니다.
- 텍스트가 있다는 사실과 지원자가 판단 가능한 정보가 있다는 사실을 구분합니다.
- 실제 사람 입력 전에는 gold, 사람 일치율, 모델 정확도를 만들거나 주장하지 않습니다.

## 구현할 기능

### 1. 입력 경로를 받는 packet 생성기

현재 hard-coded 경로에 의존하지 않는 CLI를 추가합니다.

예시 인터페이스:

```bash
python scripts/annotation_ops/build_packets.py \
  --postings /path/to/real_postings.jsonl \
  --rubric data/rubric/rubric.yaml \
  --out-dir data/private/annotation_run_001
```

요구사항:

- A/B packet을 별도 디렉터리에 생성
- 같은 posting/field 순서지만 annotator ID 분리
- AI suggestion을 포함하지 않음
- `rubric_version`, `synthetic_test_fixture` provenance 전달
- 원문 재배포가 불가한 경우에도 로컬 경로에서 작동
- 실행 manifest에 입력 checksum, 생성시간, posting 수, cell 수 기록

### 2. 사람 검수 보조 CLI

간단한 로컬 CLI로 충분합니다. 각 cell마다 다음을 지원합니다.

- 원문과 현재 field 기준 표시
- `confirmed | vague | absent` 선택
- 원문 일부를 선택하거나 정확한 evidence를 입력하면 offset을 자동 탐색
- substring이 여러 번 나오면 위치를 사람이 선택
- reason code와 선택적 note 입력
- 중간 저장 및 재개
- 다른 annotator 파일이나 AI suggestion을 절대 표시하지 않음

자동 판정이나 추천 status를 넣지 마십시오. 이 도구는 입력 편의만 제공합니다.

### 3. 완료도·격리 검증

- 6필드 누락 및 중복
- null status 수
- exact evidence/offset
- annotator ID 혼입
- A와 B의 파일 경로 및 checksum이 서로 다른지
- A/B 파일에 AI suggestion 전용 key가 없는지
- synthetic flag 누락 시 실패

### 4. adjudication 준비

- A/B 둘 다 완성·검증되기 전에는 adjudication 실행 거부
- provenance 불일치 시 실패
- agreement raw count와 percent만 우선 출력
- disagreement는 별도 review queue로 출력
- disagreement를 LLM이 자동 해결하지 않음
- 합의 셀 자동 복사는 가능하지만, 불일치 셀에는 사람 adjudicator 결정과 note가 필수

## 문서 산출물

`docs/annotation/HUMAN_ANNOTATION_GUIDE.md`에 다음을 포함합니다.

- annotator A와 B가 각각 실행할 명령
- 서로 결과를 공유하지 않는 방법
- 여섯 필드의 핵심 경계 사례
- evidence 선택 예시
- 완료 후 파일을 담당자에게 전달하는 방법
- 개인정보나 API 키를 기록하지 말라는 안내

`ANNOTATION_WORKFLOW_HANDOFF.md`에는 사용법, 테스트 결과, 남은 human action을 기록합니다.

## 테스트 및 완료 기준

- synthetic fixture로 packet → 입력 simulation → validation → adjudication queue 전체가 동작
- 테스트 산출물은 명확히 `synthetic_test_fixture:true`, `is_gold:false`
- `python -m pytest tests/annotation_ops tests/backend tests/data -q`
- 실제 사람 라벨을 생성하거나 gold라고 표시하지 않음
- 커밋·push 완료

## Claude Code 시작 프롬프트

```text
저장소의 CLAUDE.md, DATA_HANDOFF.md, TASK_ANNOTATION_WORKFLOW_PREP.md를 전부 읽고 feature/annotation-workflow-prep 브랜치에서 작업해. 이 작업은 실제 라벨을 대신 만드는 일이 아니라 두 사람이 독립적으로 라벨링할 packet/CLI/검증 절차를 준비하는 일이다. AI 제안이나 상대 annotator 결과를 노출하지 말고, 실제 사람 작업 전에는 어떤 결과도 gold로 표시하지 마. 소유 경로를 지키고 테스트·ANNOTATION_WORKFLOW_HANDOFF.md·커밋·push까지 완료해줘.
```
