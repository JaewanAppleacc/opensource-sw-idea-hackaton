# Sequential task D3: 실제 2인 라벨링·조정·gold 동결

이 작업은 D1과 D2가 끝난 뒤 진행합니다. `REAL_DATA_ACQUISITION_HANDOFF.md`가 `READY_FOR_HUMAN_ANNOTATION`이 아니면 시작하지 마십시오.

## 선행 조건

- 동일 출처·기간·직종·고용형태의 실제 공고 최소 전북 10건, 수도권 10건
- 각 레코드의 `synthetic_test_fixture:false`
- 원문 접근과 사용 범위 확인
- D2 packet/검증 도구 통과
- 사람 annotator A와 B 두 명 확보

Claude Code나 두 개의 LLM 세션을 사람 두 명으로 세지 마십시오.

## 사람 작업 — 병렬 진행 가능

### Annotator A

- A packet만 열기
- B 파일과 AI suggestion을 보지 않기
- 모든 공고 × 6필드 판정
- confirmed/vague에는 exact evidence와 offset 입력
- absent에는 evidence/offset null
- 완료 후 validator 통과

### Annotator B

- B packet만 열기
- A 파일과 AI suggestion을 보지 않기
- A와 동일한 기준으로 독립 판정
- 완료 후 validator 통과

두 사람은 같은 시간에 작업할 수 있지만 결과를 상의하면 안 됩니다. 질문은 공통 rubric 관리자에게 보내고, 기준이 바뀌면 두 사람 모두에게 같은 공지와 새 rubric version을 적용합니다.

## 조정 담당자 작업

1. A/B 파일의 완성도, rubric version, input checksum 확인
2. `scripts/data/adjudicate.py` 또는 D2 도구로 비교 파일 생성
3. raw agreement count, percent agreement, 가능한 경우에만 Cohen’s kappa 기록
4. agreement 셀 확인
5. disagreement 셀을 원문과 rubric으로 사람이 판정
6. 모든 disagreement에 `adjudicator_note` 작성
7. 모든 row가 `adjudicated_status`를 갖는지 검증
8. 합성 flag가 모두 false인지 검증

표본이 작으므로 필드별 F1을 과장하지 말고 raw count를 함께 제시합니다. 사람 간 불일치는 모델 오류가 아닙니다.

## canonical 데이터로 승격

재배포 권리가 확인된 데이터만 Git의 public layer로 옮깁니다. 원문 공개가 불가하면 원문은 `data/private/**`에 유지하고 public layer에는 ID/URL, 파생 label, checksum, 집계만 둡니다.

승격 후:

1. 실제 adjudicated 파일을 `data/gold/adjudicated_labels.jsonl`로 준비
2. backend `/data/gap-stats`가 `ready:true`를 반환하는지 확인
3. `generate_splits.py --is-gold true`로 dev/holdout 생성
4. holdout ID와 checksum 동결
5. holdout을 열어보거나 prompt 조정에 사용하지 않기
6. dev에서만 prompt/rule 수정
7. prompt/config hash와 rubric version 기록
8. holdout 평가는 한 번만 실행
9. 재실행이 필요하면 software bug와 사유를 문서화
10. exploratory report에 표본 수, 수집기간, source, 한계 표시

## 금지 주장

- “전북 기업 공고는 전반적으로 부실하다”
- “전북 취업이 수도권보다 유리하다”
- “이 서비스가 청년 유출을 감소시켰다”
- 작은 표본을 전북 전체 모집단으로 일반화한 비율
- 합성 데모 결과를 실제 성능으로 제시

허용 표현은 “동일 조건으로 수집한 이 탐색 표본에서 관찰된 결과”입니다.

## 완료 산출물

- A와 B의 독립 원본 라벨 및 checksum
- 완성된 adjudication file
- agreement raw counts와 방법론 기록
- 동결된 dev/holdout manifest
- prompt/config hash
- 실제 holdout 평가 보고서
- `REAL_GOLD_HANDOFF.md`

## 완료 기준

사람 두 명의 독립 작업과 사람 조정이 실제로 끝나지 않았다면 이 task는 완료가 아닙니다. 그 경우 `HUMAN_ACTION_REQUIRED`로 보고하고 gold 파일·성능 수치·지역 통계를 만들지 마십시오.

## 통합 세션 시작 프롬프트

```text
CLAUDE.md, REAL_DATA_ACQUISITION_HANDOFF.md, ANNOTATION_WORKFLOW_HANDOFF.md, TASK_REAL_GOLD_INTEGRATION.md를 전부 읽어. D1이 READY_FOR_HUMAN_ANNOTATION인지 먼저 확인하고, 아니면 중단해 정확한 blocker를 보고해. 준비됐다면 실제 사람 annotator A/B용 packet을 생성하고 HUMAN_ACTION_REQUIRED 상태로 넘겨. 두 사람의 완성 파일이 제공된 뒤에만 검증·사람 조정·gold 승격·split 동결·holdout 1회 평가를 진행해. LLM을 사람 annotator로 대체하거나 합성/미완성 데이터를 gold로 표시하지 마.
```
