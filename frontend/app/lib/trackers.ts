import type { Client, JevResult, ProfileId } from '@/types/api'

export interface Trackers {
  source: 'jev' | 'rules'
  main: ProfileId
  mainConfidence: number // 0..1
  trackers: { id: ProfileId, confidence: number }[] // highest first
  incomeRegularity: number | null
}

// Prefer Jev's trackers; fall back to the local rule-based profiles until Jev has scored the client.
export function trackersFor(c: Client, jev?: JevResult): Trackers {
  if (jev && !jev.error && jev.trackers?.length) {
    const trackers = [...jev.trackers].sort((a, b) => b.confidence - a.confidence)
    const main = jev.mainProfile ?? trackers[0]!.id
    return {
      source: 'jev',
      main,
      mainConfidence: trackers.find(t => t.id === main)?.confidence ?? jev.mainConfidence ?? 0,
      trackers,
      incomeRegularity: jev.incomeRegularity ?? null
    }
  }
  const trackers = c.profiles.map(p => ({ id: p.id, confidence: p.confidence > 1 ? p.confidence / 100 : p.confidence }))
    .sort((a, b) => b.confidence - a.confidence)
  return { source: 'rules', main: trackers[0]?.id ?? 'saver', mainConfidence: trackers[0]?.confidence ?? 0, trackers, incomeRegularity: null }
}
