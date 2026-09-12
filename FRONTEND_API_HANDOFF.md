# Frontend API handoff

## 시작점

- Base URL: `http://127.0.0.1:8000/api/v1`
- 실행: 저장소 루트에서 `python -m uvicorn backend.app.main:app --reload --port 8000`
- Swagger: `http://127.0.0.1:8000/docs`
- 기계 판독 계약: `contracts/openapi.json`, `contracts/schema.json`
- 기본 CORS: localhost/127.0.0.1의 3000·5173 포트. 다른 origin은 `CORS_ORIGINS`로 지정합니다.

## 엔드포인트

| Method | Path | 용도 |
|---|---|---|
| GET | `/health` | 서버·provider·데이터·루브릭 상태 |
| POST | `/postings/analyze` | 원문 1건의 6필드 실사와 확인 질문 |
| POST | `/postings/match` | 동일 직종 중심의 전북 후보 최대 3건 |
| POST | `/finance/compare` | 사용자 입력 기반 현금 축적 시나리오 |
| GET | `/data/gap-stats` | 오직 사람 조정 gold 기반 탐색 통계 |

## 화면 상태 규칙

- loading: 기존 결과를 지우지 말고 해당 카드에 진행 상태를 표시합니다.
- empty match: `404 no_match_found`를 “현재 유한 데이터셋에서 일치 공고를 찾지 못했습니다”로 표시합니다. 전북에 일자리가 없다는 뜻으로 표현하지 않습니다.
- gap stats not ready: HTTP 200 + `ready:false`가 정상 상태입니다. 차트 대신 “실제 2인 검수가 완료되면 공개”를 표시합니다.
- provider unavailable: 이전 결과를 유지하고 재시도 버튼을 제공합니다. 공고 필드를 absent로 바꾸면 안 됩니다.
- validation error: 필드 가까이에 422 메시지를 표시하되 서버의 `details` 전체를 일반 사용자에게 그대로 노출하지 않습니다.
- `is_synthetic:true`: 후보 카드와 데모 전체에 `합성 데모 데이터` 배지를 항상 표시합니다.

## 폐쇄형 enum과 권장 라벨

공고 상태는 정확히 세 개뿐입니다.

| API | 화면 라벨 | 의미 |
|---|---|---|
| `confirmed` | `공고에서 확인됨` | 지원자가 판단할 만큼 구체적이며 원문 근거가 있음 |
| `vague` | `표현은 있으나 확인 필요` | 관련 표현은 있지만 의사결정에 부족함 |
| `absent` | `공고에서 확인되지 않음` | 원문에 관련 내용을 찾지 못함 |

오류 code 전체 목록: `invalid_input`, `analysis_failed`, `provider_unavailable`, `no_match_found`, `data_not_ready`.

오류 body는 항상 다음 envelope입니다.

```json
{"error":{"code":"no_match_found","message":"...","details":{}}}
```

`external_verified`는 상태가 아닙니다. 외부 정보가 향후 추가돼도 공고 원문 상태를 승격시키지 않습니다.

## 출처·근거 표시 요구사항

- confirmed/vague는 `evidence.text`를 인용하고 원문의 `[start:end]` 위치를 강조합니다.
- absent에는 근거 인용을 만들지 말고 `evidence:null`을 유지합니다.
- 후보에는 `company_name`, `municipality`, `source_url`을 표시하되 null을 허용합니다.
- 모든 match 화면에 `dataset_description`을 노출합니다. “추천”, “최적”, “우수기업”, “승자”라는 표현은 사용하지 않습니다.
- 합성 데이터의 가상 회사명을 실제 회사처럼 보이게 하지 않습니다.

## 핵심 요청/응답

### 공고 실사

```json
{
  "posting_id": "JB-003",
  "source_text": "(예시) 가상산업 전주3호에서 생산직(제조 조립원)을 채용합니다. 생산 관련 업무 전반을 수행합니다. 관련 경험자 우대합니다. 채용형태는 면접 후 결정합니다.",
  "expected_occupation": "생산직(제조 조립원)"
}
```

응답의 `fields`는 여섯 key를 모두 가집니다. 이 데모에서는 salary/tools/training/probation이 absent, duties/employment_type이 vague이며 여섯 개의 `verification_actions`가 생성됩니다. 근거가 있는 항목은 `source_text.slice(start,end) === evidence.text`입니다.

### 전북 후보 탐색

```json
{"occupation":"생산직(제조 조립원)","employment_type":"정규직"}
```

현재 합성 데이터에서는 `JB-001`, `JB-002`, `JB-003` 순으로 반환됩니다. 각 candidate는 `source_text`, `company_name`, `is_synthetic:true`, `matching_fields`, `mismatch_fields`를 포함합니다. 사용자가 후보를 선택하면 candidate의 `source_text`를 `/postings/analyze`에 그대로 보낼 수 있습니다.

### 현금 시나리오 비교

```json
{
  "metropolitan": {
    "label": "수도권 시나리오",
    "monthly_income_after_tax": 2400000,
    "monthly_housing_cost": 900000,
    "monthly_other_living_cost": 1000000,
    "deposit": 10000000
  },
  "jeonbuk": {
    "label": "전북 시나리오",
    "monthly_income_after_tax": 2150000,
    "monthly_housing_cost": 450000,
    "monthly_other_living_cost": 900000,
    "deposit": 5000000
  },
  "assumptions": {
    "annual_income_growth_rate": 0.0,
    "annual_cost_growth_rate": 0.0,
    "rounding_unit_krw": 100000
  }
}
```

예상 핵심값:

```json
{
  "options": {
    "metropolitan": {"monthly_surplus":500000,"one_year_liquid_cash":6000000,"three_year_liquid_cash":18000000,"deposit_locked":10000000},
    "jeonbuk": {"monthly_surplus":800000,"one_year_liquid_cash":9600000,"three_year_liquid_cash":28800000,"deposit_locked":5000000}
  },
  "crossover": {"varied_option":"jeonbuk","varied_variable":"monthly_housing_cost","threshold_value":800000}
}
```

이 숫자는 공고의 세전 급여에서 자동 추정한 값이 아니라 사용자가 넣은 가상 세후 소득·비용입니다. 보증금은 `deposit_locked`로 유동 현금과 분리하고, 3년치는 예측이 아닌 입력 가정의 반복 시나리오로 표시합니다. UI는 어느 쪽도 승자로 선언하지 않습니다.

## 정확히 3개의 캐시된 공고

`demo/anchors.json`이 데모 source of truth입니다.

1. `MET-001`: 수도권 입력과 명확한 급여
2. `JB-001`: 전북 비교와 명확한 급여
3. `JB-003`: 결손 실사

셋 모두 `synthetic`입니다. 실데이터 확보 전에는 이 데모에서 나온 비율·성능·지역 차이를 발표 근거로 쓰지 마십시오.

## 권장 프론트 흐름

```text
수도권 공고 입력 → /postings/analyze
                 → 직종 확인 → /postings/match
                              → 전북 후보 선택 → /postings/analyze
                              → 사용자가 세후소득·주거비 입력 → /finance/compare
```

`/data/gap-stats`는 `ready:true`일 때만 차트를 렌더링합니다. 현재 저장소에는 실제 human gold가 없으므로 `ready:false`가 올바른 결과입니다.
