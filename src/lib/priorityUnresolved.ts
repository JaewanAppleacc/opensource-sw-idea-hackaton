/**
 * Deterministic (never LLM-judged) priority ordering for "선택 전에 우선
 * 확인할 정보" (TASK section 6). Pure function: same inputs always produce
 * the same ordered list.
 *
 * Priority buckets, in order:
 *   1. absent items on an axis the user selected as important
 *   2. vague items on an axis the user selected as important
 *   3. financially-relevant gaps (salary, probation_terms) not already
 *      covered above -- these affect the finance comparison's accuracy
 *      even if the user didn't tick 임금·보상/고용안정성
 *   4. remaining absent items (unselected axes)
 *   5. remaining vague items (unselected axes)
 * confirmed sub-items never appear here.
 */
import type { FieldName } from './apiClient'
import type { AxisId, AxisResult, AxisSubItemResult } from './comparisonAxes'

export type RegionSide = 'metro' | 'jeonbuk'

export interface PriorityItem {
  region: RegionSide
  axisId: AxisId
  axisLabel: string
  subLabel: string
  status: 'vague' | 'absent'
  sourceField: FieldName | null
  action: AxisSubItemResult['action']
  bucket: 1 | 2 | 3 | 4 | 5
}

const FINANCIALLY_RELEVANT_FIELDS: FieldName[] = ['salary', 'probation_terms']

function dedupeKey(region: RegionSide, item: AxisSubItemResult): string {
  return `${region}:${item.sourceField ?? item.subLabel}`
}

export function buildPriorityUnresolvedList(
  regions: { region: RegionSide; axes: AxisResult[] }[],
  selectedAxisIds: AxisId[],
): PriorityItem[] {
  const seen = new Set<string>()
  const buckets: PriorityItem[][] = [[], [], [], [], []]

  function collect(bucketIndex: 0 | 1 | 2 | 3 | 4, predicate: (region: RegionSide, axis: AxisResult, item: AxisSubItemResult) => boolean) {
    for (const { region, axes } of regions) {
      for (const axis of axes) {
        for (const item of axis.subItems) {
          const status = item.audited?.status
          if (status !== 'vague' && status !== 'absent') continue
          const key = dedupeKey(region, item)
          if (seen.has(key)) continue
          if (!predicate(region, axis, item)) continue
          seen.add(key)
          buckets[bucketIndex].push({
            region,
            axisId: axis.id,
            axisLabel: axis.label,
            subLabel: item.subLabel,
            status,
            sourceField: item.sourceField,
            action: item.action,
            bucket: (bucketIndex + 1) as 1 | 2 | 3 | 4 | 5,
          })
        }
      }
    }
  }

  const isSelected = (axis: AxisResult) => selectedAxisIds.includes(axis.id)
  const isFinancial = (item: AxisSubItemResult) => item.sourceField !== null && FINANCIALLY_RELEVANT_FIELDS.includes(item.sourceField)

  // 1. selected axis, absent
  collect(0, (_r, axis, item) => isSelected(axis) && item.audited?.status === 'absent')
  // 2. selected axis, vague
  collect(1, (_r, axis, item) => isSelected(axis) && item.audited?.status === 'vague')
  // 3. financially relevant, not already covered
  collect(2, (_r, _axis, item) => isFinancial(item))
  // 4. remaining absent
  collect(3, (_r, _axis, item) => item.audited?.status === 'absent')
  // 5. remaining vague
  collect(4, (_r, _axis, item) => item.audited?.status === 'vague')

  return buckets.flat()
}
