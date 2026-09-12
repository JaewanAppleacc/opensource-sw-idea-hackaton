# 전북 커리어 실사 에이전트 MVP

> 로그인 사용자가 수도권 채용공고를 검토할 때, 자신의 관심 생활권에 있는 비교 가능한 일자리를 자동으로 발견하고, 채용정보의 결손과 주거비를 포함한 현실적인 차이를 함께 검토하도록 돕는 **지역권(region pack) 기반 커리어 비교 에이전트**입니다.
>
> **전북 시연 버전:** 전북 청년이 수도권 일자리만 검토한 채 이동을 결정하기 전에, 비교 가능한 전북 일자리도 같은 화면에서 공정하게 검토하도록 돕습니다.

이 서비스는 기업을 평가하거나 전북 취업을 권고하지 않습니다. 목표는 전북 일자리가 비교 대상에조차 오르지 않는 `회피 가능한 미검토`를 줄이는 것입니다. **전국 모든 지방공고를 무작위로 추천하는 시스템이 아닙니다** — 로그인 사용자의 관심 생활권을 하나의 region pack으로 고정하고, 수도권 공고와 그 생활권의 공고만 비교합니다 (해커톤 인스턴스: `home_region = JEONBUK`). 자세한 정책은 아래 "지역권 기반 매칭 정책" 절과 `docs/architecture/EXPANSION_TECH_ASSESSMENT.md` 9절을 참고하세요.

이 저장소는 Python/FastAPI 백엔드(`backend/`)와, [work24.go.kr](https://www.work24.go.kr/cm/main.do)의 정보 구조를 참고해 만든 **비공식 학습용** React 프런트엔드(저장소 루트의 `src/`, `e2e/` 등)를 함께 담고 있습니다. **실제 고용24 서비스가 아니며, 해커톤 시연용 프로토타입입니다.**

## 지역권 기반 매칭 정책

- 로그인 사용자 프로필의 관심 생활권(정착 희망 지역) 하나만을 기준으로, 수도권 공고와 그 생활권 공고만 비교합니다. 전북 사용자에게 경북·전남·경남 일자리를 자동으로 추천하지 않습니다.
- 해커톤 시연에서는 **시연용 로그인 프로필을 가정한 구현**입니다 — 실제 고용24 인증이 아니며, 실제 주민등록 주소·전화번호·이메일을 수집하거나 저장하지 않습니다. 시연 프로필(`전북 청년 데모 사용자`, 관심 생활권 `전북특별자치도`)은 브라우저 `localStorage`에만 저장됩니다.
- 지역 제한은 프론트 표시만이 아니라 **백엔드에서도 강제**됩니다: `DEMO_HOME_REGION`(기본값 `jeonbuk`)이 실제로 로드되는 데이터셋을 결정하며, 클라이언트가 요청 값을 조작해도 활성 region pack 밖의 후보는 반환되지 않습니다 (`backend/app/datasets/loader.py::home_region()`, `backend/app/services/real_postings.py`).
- 사용자가 자기 생활권 외 공고를 직접 검색·선택하는 것은 막지 않습니다. 다만 에이전트가 먼저 제안하는 비교 후보는 자기 생활권으로 제한됩니다.
- 향후 우선순위(문서화된 권장 원칙, 이번 MVP에서 구현하지 않음): 1) 사용자가 직접 설정한 정착 희망 지역, 2) 사용자가 동의한 경우에만 현재 생활권, 3) 주민등록 주소 자동 수집은 기본 사용 안 함.

## 성공지표 (시연 및 후속 실험)

총 청년 유출 감소를 직접 성과로 주장하지 않습니다. 대신 다음을 측정 대상으로 삼습니다.

- 수도권 공고 대비 전북 공고 열람률
- 전북 비교 후보 클릭률
- 비교 전후 전북 공고 지원 고려율
- 6개 정보 항목 확인률
- 기업에 전달할 확인 질문 생성률
- 자금 축적 비교 완료율

**핵심 지표:** 지역 비교 기능을 보지 않은 사용자보다, 본 사용자가 전북 공고를 실제 선택지로 검토하는 비율이 증가했는가?

## 심사위원 질문 대응

**Q. 다른 지역이 이 시스템을 가져가면 전북 청년의 타 지역 유출을 오히려 유도하지 않나요?**

A. 이 시스템은 전국 지방공고를 무작위로 추천하지 않습니다. 로그인 사용자의 관심 생활권을 하나의 region pack으로 설정하고, 수도권 공고와 그 생활권의 공고만 비교합니다. 전북 시연 인스턴스에서는 전북 공고만 비교 후보로 노출됩니다. 다른 지역이 엔진을 도입하더라도 각 지역 사용자는 자신의 생활권 공고를 검토하게 되므로, 지역 간 이동을 새로 유도하는 엔진이 아니라 각 지역에서 수도권 편향을 보정하는 공통 인프라입니다. (해커톤 시연에서는 실제 로그인 연동이 아닌, 로그인 프로필을 가정한 시연용 구현임을 분명히 합니다.)

## 현재 구현됨

- 6개 항목 공고 실사: 급여, 업무, 도구·기술, 교육·멘토링, 수습조건, 고용형태
- 원문 substring/offset 검증과 `confirmed | vague | absent` 폐쇄형 판정
- vague/absent 항목별 확인 질문 생성
- 같은 직종·고용형태의 전북 공고 최대 3건 탐색
- 사용자가 입력한 값만 사용하는 월 잉여금·1년·3년·주거비 교차점 계산
- 사람 gold가 없으면 통계를 내지 않는 지역 결손 통계 API
- FastAPI/OpenAPI 계약, 로컬 프론트엔드 CORS, 오프라인 mock 실행
- 고용24 스타일 프런트엔드에서 위 흐름을 시연하는 화면 (데모/mock 배지 표시)

## 캐시된 데모

`demo/anchors.json`의 정확히 3개 공고를 사용합니다. 전부 가상 기업의 합성 데이터이며 실제 기업이나 전북 노동시장에 대한 근거가 아닙니다.

- `MET-001`: 급여가 명확한 수도권 공고
- `JB-001`: 급여가 명확한 전북 비교 공고
- `JB-003`: 여러 정보 결손을 질문으로 전환하는 전북 공고

데이터 파이프라인 결과도 현재는 합성 fixture 검증 결과입니다. `data/reports/demo_*` 수치를 실제 지역 통계나 모델 성능으로 발표하면 안 됩니다.

## 백엔드 실행

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload --port 8000
```

API 문서: `http://127.0.0.1:8000/docs`
프론트 연동 문서: `FRONTEND_API_HANDOFF.md`

```bash
source .venv/bin/activate
python -m pytest tests/backend tests/data -q
```

기본값은 API 키와 네트워크가 필요 없는 deterministic mock입니다. 실제 Anthropic 호출은 `.env.example`을 참고하되 키를 저장소에 커밋하지 마십시오.

## 프런트엔드 실행 (고용24 스타일 클론, 비공식 학습용)

- Vite + React + TypeScript, Tailwind CSS v4, lucide-react 아이콘, 상태관리는 React 기본 기능(useState/Context)만 사용
- Playwright(E2E), tsc(타입 체크)

```bash
npm install
npm run dev       # http://localhost:5173, VITE_API_BASE_URL로 백엔드 주소 지정 (기본 http://localhost:8000)
npm run build     # 타입 체크 + 프로덕션 빌드
npm run preview   # 빌드 결과 미리보기
npm run test:e2e  # Playwright E2E 테스트 (데스크톱/태블릿/모바일)
```

백엔드(`8000`)와 프런트엔드(`5173`)를 각각 실행해야 전체 시연 흐름이 동작합니다. 프런트는 항상 `LLM_PROVIDER=mock` 백엔드를 시연 기준으로 삼습니다 — 화면에 "데모 모드" 배지가 표시됩니다.

### 폴더 구조 (프런트엔드)

```
src/
  components/ui/        공통 UI 프리미티브 (Container, Logo, Toast, Carousel controls ...)
  components/sections/  페이지 섹션 컴포넌트 (Header, HeroSearch, ServiceTabs, Footer ...)
  data/                  타입이 지정된 mock 데이터
  hooks/                 useCarousel, usePrefersReducedMotion 등 커스텀 훅
  lib/                   백엔드 API 클라이언트, 에러 코드 매핑
  types/                 공용 타입 정의
e2e/                     Playwright 테스트
```

### 접근성 메모

- 시맨틱 랜드마크(header/nav/main/footer)와 heading 계층을 사용합니다.
- 탭(`role="tablist"`), 드롭다운, 캐러셀, 모바일 메뉴는 키보드로 조작할 수 있습니다.
- `prefers-reduced-motion`을 존중해 자동재생 캐러셀과 스크롤 애니메이션을 비활성화합니다.
- 아이콘 전용 버튼에는 `aria-label`을 제공합니다.

## 시연 가이드 (해커톤 데모)

### 1. 실행 순서

```bash
# 터미널 1 — 백엔드 (mock, 8000번 포트)
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
LLM_PROVIDER=mock python -m uvicorn app.main:app --app-dir backend --port 8000

# 터미널 2 — 프런트엔드 (5173번 포트)
npm install
npm run dev
```

- 백엔드 헬스체크: `curl http://localhost:8000/api/v1/health` → `{"status":"ok","provider_mode":"mock",...}`
- 프런트: `http://localhost:5173/ai-job-recommend`
- 프런트가 다른 백엔드 주소를 봐야 하면 `VITE_API_BASE_URL`을 설정한 뒤 `npm run dev`를 실행합니다 (기본값 `http://localhost:8000`).
- **실시간 Anthropic/NVIDIA 호출은 사용하지 않습니다.** `LLM_PROVIDER=mock`만 시연 기준입니다 — 실제 provider 실행 방법과 현재 한계는 `docs/validation/LIVE_LLM_SMOKE.md`를 참고하세요 (두 provider 모두 현재 계정/모델 문제로 실시간 검증이 차단된 상태입니다).

### 2. 시연 순서 (화면에서 실제로 확인할 흐름)

기본 시연 동선은 **AI추천 목록 → 수도권 공고 선택 → 전북 유사 공고 자동 매칭 → 6개 항목 비교 → 확인 질문 → 선택적 자금 축적 비교**입니다. 수동 붙여넣기는 더 이상 기본 화면이 아니며 보조 경로(`/manual-analysis`)로만 남아 있습니다.

1. `/ai-job-recommend`에서 **데모 모드 · 사전 검증된 분석 결과** 배지, "본 서비스는 고용24 공식 서비스가 아닌 해커톤 시연용 프로토타입입니다." 문구, 그리고 로그인 전 안내("로그인하면 관심 생활권의 유사 일자리와 비교할 수 있습니다.") 확인
2. **데모 로그인 (전북 청년 프로필)** 클릭 → "로그인 사용자: 전북 청년 데모 사용자" / "내 관심 생활권: 전북특별자치도" / "현재 전북특별자치도를 기준으로 비교하고 있습니다." 표시 확인 (실제 인증이 아닌 로그인 프로필을 가정한 시연용 구현)
3. 실제 수도권 채용공고 목록(회사명, 근무지역, 고용형태, 출처·원문 링크, 수집 기준일)이 표시됨 → 원하는 공고 카드에서 **내 지역 유사 일자리 보기 (전북특별자치도 기준)** 클릭
4. 카드 안에서 바로 **전북 일자리 비교 에이전트가 찾은 전북 일자리**가 펼쳐짐 (최대 3건, "동일한 직무"/"동일한 고용형태" 같은 사실 기반 이유만 표시 — 추천 점수 없음) → 후보 하나 선택
5. 같은 카드 안에서 **6개 항목 비교**: 수도권/전북 패널이 각각 독립적으로 로딩 후 결과 표시 — 상태 배지(`구체적으로 확인됨` / `언급됐지만 판단하기 어려움` / `공고에서 확인되지 않음`), 근거 인용문, vague/absent 항목의 확인 질문. 이 단계는 실제 비공개 원문을 `posting_id`로 백엔드에서 서버 측 조회해 분석하며, 원문 자체는 프론트에 전달되지 않습니다.
6. 아래 **지역 결손 통계** 패널이 "아직 준비되지 않았습니다"를 정직하게 표시 (human gold 없음)
7. **자금 축적 비교 펼치기 (선택)** 클릭 → 수도권/전북 소득·주거비·생활비·보증금 입력 → 월/1년/3년 가용자금, 보증금(묶인 자산), 주거비 교차점 표시 — 승자 표시 없음

### 3. 장애 발생 시 데모 복구법

- **프런트에 "백엔드 서버에 연결할 수 없습니다" 배너가 뜸** → 터미널 1에서 백엔드가 살아있는지 확인 (`curl http://localhost:8000/api/v1/health`), 죽었으면 위 실행 명령으로 재시작. 프런트는 새로고침 없이 다음 액션에서 자동으로 재시도합니다.
- **수도권 공고 목록이 비어 있음** → `data/intake/real_postings.jsonl`이 존재하는지 확인하세요. 이 파일은 tracked이므로 항상 존재해야 합니다.
- **"실제 원문 데이터가 연결되지 않은 데모 환경입니다" 오류** → `data/private/intake_raw/<posting_id>.json`이 이 머신에 없다는 뜻입니다 (의도된 fail-closed 동작 — `REAL_DATA_ACQUISITION_HANDOFF.md`/`docs/data/HUMAN_ANNOTATION_RUNBOOK.md` 참고). private 데이터는 gitignored이므로 시연 머신에 별도로 준비해야 합니다.
- **전북 후보가 안 뜸** → 현재 실제 배치는 10:10 매칭 쌍만 존재합니다(`data/intake/real_matched_pairs.jsonl`). 매칭 쌍이 없는 수도권 공고는 "현재 검증된 전북 비교 후보가 없습니다."가 정상 동작입니다.
- **분석이 멈춤/느림** → mock provider는 네트워크를 쓰지 않으므로 수 초 내 응답해야 합니다. 20초 이상 걸리면 프런트가 자체적으로 타임아웃 오류를 표시합니다 — 백엔드 터미널 로그를 확인하세요.
- **완전히 막히면** → 두 터미널을 모두 종료하고 실행 순서(1번)를 처음부터 다시 수행하세요. `/manual-analysis`의 합성 fixture(`demo/anchors.json`, `data/postings/postings.jsonl`) 경로는 private 데이터 없이도 항상 동작하는 대체 시연 경로입니다.

### 4. AI-A/B consensus에 대한 정확한 설명 (시연 중 질문 대비)

실제 채용공고 20건의 120개 필드에 대해 두 독립 AI 검수 결과 120개 셀 중 113개가 일치했다. 이는 정확도가 아니라
일치도이며, 7개 경계 사례는 팀 리드가 원문과 rubric을 검토해 조정한 뒤 평가에서 최종 해결로 표시했다. **사람
Gold 검증(2명의 독립적인 사람 라벨링)은 아직 수행되지 않았다.** 자세한 내용과 selection-bias 한계는
`docs/data/AI_CONSENSUS_REVIEW.md`를 참고하세요. 이 수치를 "모델 정확도"나 "AI 성능"으로 인용하지 마십시오.

### 5. 알려진 한계 (시연 중 정직하게 답할 내용)

- 위 AI consensus는 human gold가 아님 — `docs/data/AI_CONSENSUS_REVIEW.md`
- 실제 20건 표본은 확보했으나 재배포 권리는 건별 미확인 — `REAL_DATA_ACQUISITION_HANDOFF.md`
- `GET /data/gap-stats`는 human gold가 없어 항상 `ready: false` (정상 동작, 화면에도 그대로 표시)
- 실시간 Anthropic/NVIDIA 호출 미검증 (계정 크레딧/모델 프로비저닝 문제) — `docs/validation/LIVE_LLM_SMOKE.md`
- 프런트엔드는 고용24 공식 서비스가 아닌 비공식 학습용 클론이며, 전북 비교 후보는 합성 데모 데이터셋(`data/postings/postings.jsonl`)에서만 가져옵니다 — 실제 비공개 원문(`data/private/**`)은 절대 프런트에 노출하지 않습니다.

## 아직 구현·검증되지 않음

- 실제 고용24/워크넷 공고 수집 및 재배포 허가 확인 (실제 10:10 표본은 확보했으나 재배포 권리는 건별 미확인 — `REAL_DATA_ACQUISITION_HANDOFF.md`)
- 2명의 독립적인 사람이 라벨링한 human gold (현재는 AI-A/B consensus + 사람 조정 reference set만 존재 — `docs/data/AI_CONSENSUS_REVIEW.md`)
- 고정된 holdout에서의 실제 LLM 평가
- 실제 사용자 대상 전북 공고 검토율 A/B 실험
- 전북 청년 순유출 감소라는 장기 인과효과
- 브라우저 확장프로그램, 라이브 채용사이트 연동, 운영 배포
- **"전북 채용공고 정보 개선 리포트" 집계 화면** (실제 표본 6개 축별 confirmed/vague/absent 분포 시각화). 시간 부족으로 이번 브랜치에서는 구현하지 않음 — 데이터는 이미 존재하므로(`data/private/ai_reviews/ai_consensus_adjudicated.jsonl`), 구현 시 새 화면과 "실제 전북 공고 10건을 대상으로 한 해커톤 시범 분석이며 전북 전체 채용시장을 대표하지 않습니다." 문구만 추가하면 됨.

따라서 현 단계는 "제품 흐름과 안전장치가 동작하는 MVP"이지 "전북 청년 유출 감소 효과가 입증된 서비스"가 아닙니다. 실제 데이터 작업 순서는 `DATA_HANDOFF.md`에 있습니다.
