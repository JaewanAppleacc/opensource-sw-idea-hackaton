# Region Pack / Job Posting Ontology

## 전제: 지금 있는 것과 없는 것

`CURRENT_SYSTEM_FLOW.md` §1, §4에서 확인한 대로, 오늘 코드에는 **region pack이라는 타입/설정이
존재하지 않습니다.**

- `contracts/schema.json`의 `region` 필드는 enum이 아니라 자유 문자열(665-668, 784-787행).
- `home_region`, `comparison_regions`, `region_pack`, `JEONBUK`/`CAPITAL_AREA` 같은 이름은
  코드/계약 어디에도 없음.
- 실제로 쓰이는 값은 하드코딩된 리터럴 문자열 `"jeonbuk"` / `"metropolitan"` 두 개뿐이며,
  `backend/app/datasets/loader.py:35,51,82`와 `backend/app/services/finance.py:67-71` 두 파일
  세 지점에 흩어져 있습니다.
- 지역별 주거비 baseline 조회 기능 없음 — `FinancialOption.monthly_housing_cost`는 사용자가 직접
  입력하는 숫자(schema.json:922-927).

이 문서는 따라서 "기존 구조를 문서화"하는 문서가 아니라, **과제 지시서 §10이 제시한 온톨로지
구조를 목표(target)로 두고, 그 목표에 얼마나 근접해 있는지, 어떤 최소 변경으로 도달할 수 있는지를
평가**하는 문서입니다. 그래프 DB/RDF 엔진은 추가하지 않습니다.

---

## 목표 온톨로지 구조 (과제 지시서 §10 그대로)

```
UserProfile
 └─ hasHomeRegion → RegionPack

RegionPack
 ├─ contains → LocalPosting
 ├─ hasHousingBaseline → RegionalCostBaseline
 └─ allowsComparisonWith → CapitalArea

JobPosting
 ├─ locatedIn → Region
 ├─ hasField → Compensation
 ├─ hasField → Duties
 ├─ hasField → Skills
 ├─ hasField → Training
 ├─ hasField → Probation
 └─ hasField → EmploymentType

PostingField
 ├─ hasDisclosureStatus → confirmed | vague | absent
 ├─ supportedBy → Evidence
 └─ missingOrVagueCreates → VerificationAction

Comparison
 ├─ compares → CapitalAreaPosting
 ├─ compares → LocalPosting
 ├─ scopedBy → UserProfile.homeRegion
 └─ contains → FieldComparison
```

## 현재 구현과의 대응표

| 온톨로지 노드 | 현재 구현 상태 | 근거 |
|---|---|---|
| `PostingField.hasDisclosureStatus` | **완전 구현.** `AuditedField.status` enum `confirmed\|vague\|absent` | `contracts/schema.json:71-76`, `AI_HARNESS.md` §전체 |
| `PostingField.supportedBy → Evidence` | **완전 구현.** `EvidenceSpan(text, start, end)`, 정확 일치 검증 | `services/evidence.py:15-24` |
| `PostingField.missingOrVagueCreates → VerificationAction` | **완전 구현.** 고정 템플릿 매핑 | `audit_pipeline.py:96-97`, `services/verification.py` |
| `JobPosting.hasField → {Compensation, Duties, Skills, Training, Probation, EmploymentType}` | **완전 구현.** `salary, duties, tools_or_skills, training_or_mentoring, probation_terms, employment_type` 6필드 고정 | CLAUDE.md:30-36 |
| `JobPosting.locatedIn → Region` | **부분 구현.** 값은 존재(자유 문자열)하나 타입/enum 없음 | `datasets/loader.py:35,51,82` |
| `Comparison.compares / scopedBy / contains → FieldComparison` | **암묵적 구현.** `/postings/match` + `/postings/analyze` 조합으로 동등 기능 제공하나, 이를 하나의 `Comparison` 타입으로 묶는 모델은 없음 | `contracts/openapi.json` |
| `RegionPack` (전체) | **미구현.** | §전제 |
| `RegionPack.hasHousingBaseline → RegionalCostBaseline` | **미구현.** 사용자 직접 입력으로 대체 중 | `finance.py`, `schema.json:922-927` |
| `UserProfile.hasHomeRegion` | **미구현.** 사용자 프로필/세션 개념 자체가 없음 | `CURRENT_SYSTEM_FLOW.md` §1 |
| `RegionPack.allowsComparisonWith → CapitalArea` | **미구현**(정책이 코드가 아니라 하드코딩된 매칭 로직으로 암묵 존재) | `matching.py:22-71` |

## 판정: 지금 단계에서 YAML + Pydantic + 문서로 충분한가

**충분합니다, 단 지금 `field_rules.yaml`/`rubric.yaml`이 채우는 부분(PostingField 서브그래프)에
한해서입니다.** `PostingField`/`Evidence`/`VerificationAction` 서브그래프는 이미 Pydantic 모델 +
YAML 룹릭으로 완전히 표현되어 있고, 그래프 순회나 추론이 필요한 질의가 하나도 없습니다(모든 판정이
단일 필드 로컬 규칙). 그래프 DB 도입은 정당화되지 않습니다.

**`RegionPack` 서브그래프는 존재 자체가 없으므로 "충분한가"를 판정할 대상이 없습니다.** 이 부분은
NEXT_STAGE로, 최소 구현안은 아래와 같습니다 — 여기서도 그래프 DB는 불필요합니다. Pydantic 모델
하나(`RegionPack`)와 지역 코드 enum 하나면 충분합니다.

### 최소 구현안 (NEXT_STAGE, 코드 미작성 — 설계만)

```python
class RegionCode(str, Enum):
    JEONBUK = "jeonbuk"
    CAPITAL_AREA = "metropolitan"  # 현재 리터럴과 1:1 매핑, breaking change 없음

class RegionalCostBaseline(StrictModel):
    region: RegionCode
    median_monthly_housing_cost: int
    source: str          # 출처 표기 필수 (§MCP 평가의 "응답 출처" 원칙과 동일)
    as_of: date

class RegionPack(StrictModel):
    region: RegionCode
    postings: list[str]              # posting_id 목록, datasets/loader.py 출력을 감싸기만 함
    housing_baseline: RegionalCostBaseline | None
    allowed_comparison_regions: list[RegionCode]
```

이 설계의 핵심은 **엔진(matching.py, finance.py, audit_pipeline.py)을 건드리지 않고, 현재
하드코딩된 3곳의 문자열 리터럴만 `RegionCode` 참조로 교체**한다는 점입니다. 전국 확장 시에도
엔진 코드는 그대로 두고 `RegionPack` 인스턴스(=region_code + 데이터 파일 경로 + baseline)만
사용자별/지역별로 늘리면 됩니다 — 이는 과제 지시서가 요구한 "엔진 유지, region pack만 변경" 원칙과
정확히 일치합니다.

### 평가 방법 (도입 시)

- `RegionCode` enum 추가 후 기존 20건 데이터셋으로 회귀 테스트: `matching.py`/`finance.py` 출력이
  리팩터링 전후 동일한지(golden test).
- 신규 지역(예: 강원) 추가 시 코드 변경 없이 `RegionPack` 데이터 파일 추가만으로 `/postings/match`가
  새 지역 후보를 반환하는지 통합 테스트.

### 도입을 재검토할 조건

- 지역이 3개 이상으로 늘어나거나, `allowsComparisonWith`처럼 지역 간 관계에 조건부 로직(예: 생활권
  인접성, 통근권)이 붙기 시작하면 → 이때부터 `RegionPack` 간 관계 그래프가 단순 enum을 넘어서므로
  재검토.
- 현재는 지역이 2개, 관계가 1개(전북→수도권 단방향 비교)뿐이라 이 조건에 해당하지 않음.

---

## 심사위원 설명 한 문장

"Region은 아직 데이터 타입이 아니라 문자열 리터럴이며, 이 문서는 그것을 그래프 DB가 아니라
enum 하나와 Pydantic 모델 하나로 승격시키는 최소 설계도다."
