import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { GovernmentNoticeBar } from '../sections/GovernmentNoticeBar'
import { AudienceSwitcher } from '../sections/AudienceSwitcher'
import { MainHeader } from '../sections/MainHeader'
import { GlobalNavigation } from '../sections/GlobalNavigation'
import { MobileMenu } from '../sections/MobileMenu'
import { Footer } from '../sections/Footer'
import { FloatingActions } from '../sections/FloatingActions'
import type { AudienceId } from '../../types'

export function SiteLayout() {
  const [audience, setAudience] = useState<AudienceId>('personal')
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  return (
    <div id="top" className="min-h-screen bg-white">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-lg focus:bg-brand-blue focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-white"
      >
        본문 바로가기
      </a>
      <a
        href="#gnb"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-16 focus:z-[100] focus:rounded-lg focus:bg-brand-blue focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-white"
      >
        주메뉴 바로가기
      </a>

      <div className="sticky top-0 z-30">
        <GovernmentNoticeBar />
        <AudienceSwitcher audience={audience} onChange={setAudience} />
        <header className="border-b border-ink-border bg-white">
          <MainHeader onOpenMobileMenu={() => setIsMenuOpen(true)} />
          <GlobalNavigation onOpenAllMenu={() => setIsMenuOpen(true)} />
        </header>
      </div>

      <MobileMenu isOpen={isMenuOpen} onClose={() => setIsMenuOpen(false)} />

      <main id="main-content">
        <Outlet />
      </main>

      <Footer />
      <FloatingActions />
    </div>
  )
}
