# 전북 커리어 실사 에이전트 MVP

수도권 채용공고를 검토하는 청년에게 같은 직종·고용형태의 전북 공고를 함께 보여주고, 공고에 적혀 있지 않거나 모호한 조건을 질문으로 바꾸며, 사용자가 입력한 소득·주거비로 현금 축적 시나리오를 비교하는 오픈소스 MVP입니다.

이 서비스는 기업을 평가하거나 전북 취업을 권고하지 않습니다. 목표는 전북 일자리가 비교 대상에조차 오르지 않는 `회피 가능한 미검토`를 줄이는 것입니다.

이 저장소는 Python/FastAPI 백엔드(`backend/`)와, [work24.go.kr](https://www.work24.go.kr/cm/main.do)의 정보 구조를 참고해 만든 **비공식 학습용** React 프런트엔드(저장소 루트의 `src/`, `e2e/` 등)를 함께 담고 있습니다. **실제 고용24 서비스가 아니며, 해커톤 시연용 프로토타입입니다.**

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

1. `/ai-job-recommend`에서 **데모 모드 · 사전 검증된 분석 결과** 배지와 "본 서비스는 고용24 공식 서비스가 아닌 해커톤 시연용 프로토타입입니다." 문구 확인
2. **데모 공고 불러오기** 클릭 → 관심 직종/본문이 채워짐 → **공고 분석하기** 클릭
3. **전북 비교 후보**가 나타남 (최대 3건, 직무·지역·고용형태·비교 가능한 이유·출처 표시) → 후보 하나 선택
4. **6개 항목 분석**: 수도권/전북 패널이 각각 독립적으로 로딩 후 결과 표시 — 상태 배지(`구체적으로 확인됨` / `언급됐지만 판단하기 어려움` / `공고에서 확인되지 않음`), 근거 인용문, vague/absent 항목의 확인 질문
5. 아래 **지역 결손 통계** 패널이 "아직 준비되지 않았습니다"를 정직하게 표시 (human gold 없음)
6. **자금축적 비교**에 수도권/전북 소득·주거비·생활비·보증금 입력 → 월/1년/3년 가용자금, 보증금(묶인 자산), 주거비 교차점 표시 — 승자 표시 없음

### 3. 장애 발생 시 데모 복구법

- **프런트에 "백엔드 서버에 연결할 수 없습니다" 배너가 뜸** → 터미널 1에서 백엔드가 살아있는지 확인 (`curl http://localhost:8000/api/v1/health`), 죽었으면 위 실행 명령으로 재시작. 프런트는 새로고침 없이 다음 액션에서 자동으로 재시도합니다.
- **전북 후보가 안 뜸** → "관심 직종"이 정확히 `생산직(제조 조립원)`인지 확인 (데모 공고 불러오기가 이 값을 자동으로 채웁니다). 그 외 직종은 현재 큐레이션 데이터셋에 없어 "현재 검증된 전북 비교 후보가 없습니다."가 정상 동작입니다.
- **분석이 멈춤/느림** → mock provider는 네트워크를 쓰지 않으므로 수 초 내 응답해야 합니다. 20초 이상 걸리면 프런트가 자체적으로 타임아웃 오류를 표시합니다 — 백엔드 터미널 로그를 확인하세요.
- **완전히 막히면** → 두 터미널을 모두 종료하고 실행 순서(1번)를 처음부터 다시 수행하세요. 모든 데모 데이터는 로컬 synthetic fixture(`demo/anchors.json`, `data/postings/postings.jsonl`)라 재시작해도 상태가 깨지지 않습니다.

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

따라서 현 단계는 "제품 흐름과 안전장치가 동작하는 MVP"이지 "전북 청년 유출 감소 효과가 입증된 서비스"가 아닙니다. 실제 데이터 작업 순서는 `DATA_HANDOFF.md`에 있습니다.
