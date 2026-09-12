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

## 아직 구현·검증되지 않음

- 실제 고용24/워크넷 공고 수집 및 재배포 허가 확인 (실제 10:10 표본은 확보했으나 재배포 권리는 건별 미확인 — `REAL_DATA_ACQUISITION_HANDOFF.md`)
- 2명의 독립적인 사람이 라벨링한 human gold (현재는 AI-A/B consensus + 사람 조정 reference set만 존재 — `docs/data/AI_CONSENSUS_REVIEW.md`)
- 고정된 holdout에서의 실제 LLM 평가
- 실제 사용자 대상 전북 공고 검토율 A/B 실험
- 전북 청년 순유출 감소라는 장기 인과효과
- 브라우저 확장프로그램, 라이브 채용사이트 연동, 운영 배포

따라서 현 단계는 "제품 흐름과 안전장치가 동작하는 MVP"이지 "전북 청년 유출 감소 효과가 입증된 서비스"가 아닙니다. 실제 데이터 작업 순서는 `DATA_HANDOFF.md`에 있습니다.
