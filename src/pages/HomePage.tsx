import { useState } from 'react'
import { HeroSearch } from '../components/sections/HeroSearch'
import { ServiceTabs } from '../components/sections/ServiceTabs'
import { QuickServiceCarousel } from '../components/sections/QuickServiceCarousel'
import { StatisticsPanel } from '../components/sections/StatisticsPanel'
import { PolicyCards } from '../components/sections/PolicyCards'
import { UserGuide } from '../components/sections/UserGuide'
import { NewsAndNotices } from '../components/sections/NewsAndNotices'
import { PromotionBanner } from '../components/sections/PromotionBanner'
import { BusinessCTA } from '../components/sections/BusinessCTA'
import { quickMenuByTab } from '../data/tabs'
import type { ServiceTabId } from '../types'

export function HomePage() {
  const [activeTab, setActiveTab] = useState<ServiceTabId>('find')

  return (
    <>
      <HeroSearch />
      <ServiceTabs activeTab={activeTab} onChange={setActiveTab} />
      <QuickServiceCarousel key={activeTab} items={quickMenuByTab[activeTab]} />
      <StatisticsPanel />
      <PolicyCards />
      <UserGuide />
      <NewsAndNotices />
      <PromotionBanner />
      <BusinessCTA />
    </>
  )
}
