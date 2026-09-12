import { Baby, Briefcase, GraduationCap, Search, Wallet } from 'lucide-react'
import type {
  GuideCard,
  LinkListGroup,
  NewsItem,
  NoticeItem,
  PolicyCard,
  PromotionSlide,
  SearchScope,
  StatItem,
} from '../types'

export const searchScopes: SearchScope[] = [
  { id: 'all', label: '전체' },
  { id: 'recruit', label: '채용정보' },
  { id: 'policy', label: '고용정책' },
  { id: 'training', label: '훈련정보' },
  { id: 'notice', label: '공지사항' },
]

export const popularKeywords: string[] = [
  '국민취업지원제도',
  '실업급여 신청',
  '국민내일배움카드',
  '육아휴직 급여',
  '이력서 첨삭',
]

export const statItems: StatItem[] = [
  {
    id: 'recruit-count',
    label: '채용공고 수',
    value: '144,607',
    unit: '건',
    links: [
      { id: 'by-region', label: '지역별 일자리 정보 찾기', href: '#by-region' },
      { id: 'by-job', label: '직종별 일자리 정보 찾기', href: '#by-job' },
      { id: 'by-theme', label: '테마별 일자리 정보 찾기', href: '#by-theme' },
    ],
  },
  {
    id: 'training-count',
    label: '교육·훈련 수',
    value: '22,040',
    unit: '건',
    links: [
      { id: 'card-training', label: '국민내일배움카드 훈련과정', href: '#card-training' },
      { id: 'k-digital', label: 'K-디지털 아카데미 훈련과정', href: '#k-digital' },
      { id: 'gov-training', label: '정부부처별 훈련과정', href: '#gov-training' },
    ],
  },
]

export const policyCards: PolicyCard[] = [
  {
    id: 'prepare',
    title: '취업준비',
    description: '취업은 하고 싶은데, 어떻게 해야 할지 모르겠어요',
    href: '#policy-prepare',
    icon: Briefcase,
  },
  {
    id: 'find-job',
    title: '일자리 찾기',
    description: '내게 맞는 일자리를 찾고 싶어요',
    href: '#policy-find',
    icon: Search,
  },
  {
    id: 'training',
    title: '교육훈련',
    description: '취업하기 위해 공부하거나 자격증을 따고 싶어요',
    href: '#policy-training',
    icon: GraduationCap,
  },
  {
    id: 'unemployment',
    title: '실업급여',
    description: '최근에 어쩔 수 없이 퇴사했어요. 조만간 퇴사할 것 같아요',
    href: '#policy-unemployment',
    icon: Wallet,
  },
  {
    id: 'birth-care',
    title: '출산·육아',
    description: '출산/육아를 위해 일을 쉬거나 근무 시간을 줄여야 할 거 같아요',
    href: '#policy-birth-care',
    icon: Baby,
  },
]

export const guideCards: GuideCard[] = [
  {
    id: 'center',
    title: '가까운 고용센터 찾기',
    description: '가까운 고용센터를 찾아 취업지원과 고용 관련 상담을 받으세요.',
    href: '#guide-center',
    tint: 'lavender',
  },
  {
    id: 'howto',
    title: '고용24 이용가이드',
    description: '고용24 서비스의 다양한 기능을 쉽게 활용할 수 있는 이용 방법을 확인하세요.',
    href: '#guide-howto',
    tint: 'mint',
  },
  {
    id: 'forms',
    title: '서식자료실',
    description: '필요한 서식을 다운로드하여 간편하게 서류를 작성하세요.',
    href: '#guide-forms',
    tint: 'sky',
  },
]

export const newsItems: NewsItem[] = [
  {
    id: 'news-1',
    title: '한빛에너지, 하반기 신입·경력사원 62명 공개 채용',
    date: '2026-09-11',
    excerpt: '한빛에너지가 대졸·고졸을 포함해 올해 하반기 신입 및 경력사원 공개 채용을 실시한다고 밝혔다...',
    href: '#news-1',
  },
  {
    id: 'news-2',
    title: '인주도시공사, 3차 기간제 직원 채용 실시',
    date: '2026-09-11',
    excerpt: '인주도시공사는 지역 일자리 창출을 위해 기간제 직원 5명을 추가로 채용한다고 밝혔다...',
    href: '#news-2',
  },
  {
    id: 'news-3',
    title: '청년일자리 도약장려금 하반기 신청 접수 시작',
    date: '2026-09-09',
    excerpt: '고용노동부는 청년을 정규직으로 채용한 중소기업을 대상으로 장려금 신청을 접수한다고 안내했다...',
    href: '#news-3',
  },
  {
    id: 'news-4',
    title: '국민내일배움카드 디지털 훈련과정 신설',
    date: '2026-09-08',
    excerpt: '디지털 전환에 대응하기 위한 신규 훈련과정이 국민내일배움카드 대상 과정에 추가됐다...',
    href: '#news-4',
  },
]

export const noticeItems: NoticeItem[] = [
  { id: 'notice-1', title: '시스템 개선 작업에 따른 서비스 중단 안내', date: '2026-09-02', href: '#notice-1' },
  { id: 'notice-2', title: '추석 연휴 고객센터 운영시간 안내', date: '2026-09-10', href: '#notice-2', isNew: true },
  { id: 'notice-3', title: '모바일 앱 업데이트 안내(로그인 방식 개선)', date: '2026-09-08', href: '#notice-3' },
  { id: 'notice-4', title: '개인정보처리방침 개정 사전 안내', date: '2026-09-07', href: '#notice-4' },
]

export const promotionSlides: PromotionSlide[] = [
  {
    id: 'promo-1',
    eyebrow: '국민취업지원제도',
    title: '구직촉진수당과 함께하는 취업 여정',
    subtitle: '소득 지원부터 취업 지원까지, 필요한 순간에 함께합니다.',
    href: '#promo-1',
    tint: 'lavender',
  },
  {
    id: 'promo-2',
    eyebrow: '국민내일배움카드',
    title: '배우고 싶은 순간, 배움으로 채우다',
    subtitle: '평생 훈련비를 지원받아 새로운 역량을 키워보세요.',
    href: '#promo-2',
    tint: 'mint',
  },
  {
    id: 'promo-3',
    eyebrow: '청년일자리 도약장려금',
    title: '청년과 기업이 함께 도약하는 방법',
    subtitle: '청년을 채용한 기업에 인건비를 지원합니다.',
    href: '#promo-3',
    tint: 'sky',
  },
  {
    id: 'promo-4',
    eyebrow: '육아휴직 급여',
    title: '일과 육아, 함께 지켜드립니다',
    subtitle: '육아휴직 급여 신청부터 지급까지 한 번에 확인하세요.',
    href: '#promo-4',
    tint: 'lavender',
  },
]

export const familySites: LinkListGroup = {
  id: 'family',
  label: '패밀리사이트',
  links: [
    { id: 'family-1', label: '고용복지플러스센터(예시)', href: '#family-1' },
    { id: 'family-2', label: '직업훈련포털(예시)', href: '#family-2' },
    { id: 'family-3', label: '청년정책포털(예시)', href: '#family-3' },
    { id: 'family-4', label: '여성새로일하기센터(예시)', href: '#family-4' },
  ],
}

export const relatedOrgs: LinkListGroup = {
  id: 'related',
  label: '유관기관',
  links: [
    { id: 'org-1', label: '근로복지서비스(예시)', href: '#org-1' },
    { id: 'org-2', label: '산업인력개발원(예시)', href: '#org-2' },
    { id: 'org-3', label: '중소기업진흥공단(예시)', href: '#org-3' },
    { id: 'org-4', label: '사회적기업진흥원(예시)', href: '#org-4' },
  ],
}

export const footerPolicyLinks: LinkListGroup = {
  id: 'policy-links',
  label: '정책 링크',
  links: [
    { id: 'terms', label: '이용약관', href: '#terms' },
    { id: 'privacy', label: '개인정보처리방침', href: '#privacy' },
    { id: 'email-refuse', label: '이메일무단수집거부', href: '#email-refuse' },
    { id: 'copyright', label: '저작권보호정책', href: '#copyright' },
    { id: 'open-api', label: '오픈API 서비스', href: '#open-api' },
    { id: 'sitemap', label: '사이트맵', href: '#sitemap' },
  ],
}
