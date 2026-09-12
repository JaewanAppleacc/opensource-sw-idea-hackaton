import type { LucideIcon } from 'lucide-react'

export type AudienceId = 'personal' | 'business'

export interface NavSubItem {
  id: string
  label: string
  description?: string
  href: string
}

export interface NavMenuItem {
  id: string
  label: string
  href: string
  children: NavSubItem[]
}

export type ServiceTabId = 'prepare' | 'find' | 'training' | 'leave'

export interface ServiceTab {
  id: ServiceTabId
  label: string
}

export interface QuickMenuItem {
  id: string
  label: string
  href: string
  icon: LucideIcon
  /** Internal SPA route (react-router path). When set, this takes priority over `href`. */
  to?: string
}

export interface StatSubLink {
  id: string
  label: string
  href: string
}

export interface StatItem {
  id: string
  label: string
  value: string
  unit: string
  links: StatSubLink[]
}

export interface PolicyCard {
  id: string
  title: string
  description: string
  href: string
  icon: LucideIcon
}

export type GuideTint = 'lavender' | 'mint' | 'sky'

export interface GuideCard {
  id: string
  title: string
  description: string
  href: string
  tint: GuideTint
}

export interface NewsItem {
  id: string
  title: string
  date: string
  excerpt: string
  href: string
}

export interface NoticeItem {
  id: string
  title: string
  date: string
  href: string
  isNew?: boolean
}

export interface PromotionSlide {
  id: string
  eyebrow: string
  title: string
  subtitle: string
  href: string
  tint: GuideTint
}

export interface LinkListGroup {
  id: string
  label: string
  links: StatSubLink[]
}

export interface SearchScope {
  id: string
  label: string
}
