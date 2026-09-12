import type { NavMenuItem } from '../types'

export const navigationMenu: NavMenuItem[] = [
  {
    id: 'recruit',
    label: '채용정보',
    href: '#recruit',
    children: [
      { id: 'recruit-search', label: '채용정보 검색', href: '#recruit-search', description: '전국 채용공고를 한 번에 검색해요' },
      { id: 'recruit-custom', label: '맞춤 채용정보', href: '#recruit-custom', description: '내 조건에 맞는 공고를 추천받아요' },
      { id: 'recruit-ai', label: 'AI 추천 채용정보', href: '#recruit-ai', description: 'AI가 분석한 나만의 공고 리스트' },
      { id: 'recruit-fair', label: '채용행사', href: '#recruit-fair', description: '채용박람회·설명회 일정을 확인해요' },
      { id: 'recruit-talent', label: '통합인재정보망', href: '#recruit-talent', description: '이력서를 등록하고 기업에 노출돼요' },
    ],
  },
  {
    id: 'support',
    label: '취업지원',
    href: '#support',
    children: [
      { id: 'support-personal', label: '개인별 취업지원 서비스', href: '#support-personal', description: '전담 상담사의 맞춤 취업 지원' },
      { id: 'support-national', label: '국민취업지원제도', href: '#support-national', description: '구직촉진수당과 취업지원을 함께' },
      { id: 'support-youth', label: '청년일자리 도약장려금', href: '#support-youth', description: '청년 채용 기업에 장려금을 지원해요' },
      { id: 'support-senior', label: '중장년 새출발카운슬링', href: '#support-senior', description: '중장년 재취업·전직을 상담해요' },
      { id: 'support-package', label: '취업성공패키지 안내', href: '#support-package', description: '단계별 취업 성공 프로그램' },
    ],
  },
  {
    id: 'unemployment',
    label: '실업급여',
    href: '#unemployment',
    children: [
      { id: 'unemployment-guide', label: '실업급여 안내', href: '#unemployment-guide', description: '실업급여 종류와 지급 조건 안내' },
      { id: 'unemployment-apply', label: '수급자격 신청', href: '#unemployment-apply', description: '온라인으로 수급자격을 신청해요' },
      { id: 'unemployment-recognition', label: '실업인정 인터넷 신청', href: '#unemployment-recognition', description: '실업인정을 인터넷으로 신청해요' },
      { id: 'unemployment-plan', label: '취업활동계획 수립', href: '#unemployment-plan', description: '나의 구직활동 계획을 세워요' },
      { id: 'unemployment-confirm', label: '이직확인서 처리 조회', href: '#unemployment-confirm', description: '이직확인서 처리 현황을 조회해요' },
    ],
  },
  {
    id: 'training',
    label: '직업 능력 개발',
    href: '#training',
    children: [
      { id: 'training-card', label: '국민내일배움카드', href: '#training-card', description: '훈련비를 지원받아 역량을 키워요' },
      { id: 'training-search', label: '훈련과정 찾기', href: '#training-search', description: '내게 맞는 훈련과정을 검색해요' },
      { id: 'training-remote', label: '원격훈련', href: '#training-remote', description: '온라인으로 언제든 학습해요' },
      { id: 'training-cert', label: '자격증 정보', href: '#training-cert', description: '국가자격·민간자격 정보를 확인해요' },
      { id: 'training-history', label: '훈련이력 조회', href: '#training-history', description: '지금까지의 훈련 이력을 확인해요' },
    ],
  },
  {
    id: 'leave',
    label: '출산휴가·육아휴직',
    href: '#leave',
    children: [
      { id: 'leave-birth', label: '출산전후휴가 급여', href: '#leave-birth', description: '출산전후휴가 급여를 신청해요' },
      { id: 'leave-parental', label: '육아휴직 급여', href: '#leave-parental', description: '육아휴직 급여를 신청해요' },
      { id: 'leave-reduced', label: '육아기 근로시간 단축', href: '#leave-reduced', description: '근로시간 단축급여를 신청해요' },
      { id: 'leave-bonus', label: '아빠육아휴직보너스제', href: '#leave-bonus', description: '두 번째 육아휴직자를 우대해요' },
      { id: 'leave-forms', label: '신청서식 다운로드', href: '#leave-forms', description: '필요한 서식을 내려받아요' },
    ],
  },
]
