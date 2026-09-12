# 고용24 클론 (비공식 학습용)

[work24.go.kr](https://www.work24.go.kr/cm/main.do) 메인페이지의 정보 구조·레이아웃·인터랙션을 참고해 만든
**비공식 학습용 프런트엔드 클론**입니다. 실제 고용24 서비스와 무관하며, 로그인·검색·API는 모두 로컬 mock
데이터로 동작합니다. 정부 로고·사진·원본 아이콘은 사용하지 않고 대체 SVG/텍스트 마크로 표현했습니다.

## 기술 스택

- Vite + React + TypeScript
- Tailwind CSS v4 (CSS 변수 기반 디자인 토큰)
- lucide-react 아이콘
- 상태관리는 React 기본 기능(useState/Context)만 사용
- Playwright(E2E), tsc(타입 체크)

## 실행

```bash
npm install
npm run dev       # http://localhost:5173
npm run build     # 타입 체크 + 프로덕션 빌드
npm run preview   # 빌드 결과 미리보기
npm run test:e2e  # Playwright E2E 테스트 (데스크톱/태블릿/모바일)
```

## 폴더 구조

```
src/
  components/ui/        공통 UI 프리미티브 (Container, Logo, Toast, Carousel controls ...)
  components/sections/  페이지 섹션 컴포넌트 (Header, HeroSearch, ServiceTabs, Footer ...)
  data/                  타입이 지정된 mock 데이터
  hooks/                 useCarousel, usePrefersReducedMotion 등 커스텀 훅
  types/                 공용 타입 정의
e2e/                     Playwright 테스트
```

## 접근성 메모

- 시맨틱 랜드마크(header/nav/main/footer)와 heading 계층을 사용합니다.
- 탭(`role="tablist"`), 드롭다운, 캐러셀, 모바일 메뉴는 키보드로 조작할 수 있습니다.
- `prefers-reduced-motion`을 존중해 자동재생 캐러셀과 스크롤 애니메이션을 비활성화합니다.
- 아이콘 전용 버튼에는 `aria-label`을 제공합니다.
