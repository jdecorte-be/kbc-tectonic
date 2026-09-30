import { PROFILE_IDS } from '@/types/api'
import type { Client, ProfileId } from '@/types/api'

// One categorical hue per profile, evenly spaced around the KBC teal.
export const profileColor = (p: ProfileId) =>
  `oklch(0.72 0.14 ${(PROFILE_IDS.indexOf(p) * 360) / PROFILE_IDS.length + 190})`

export const mainProfile = (profiles: { id: ProfileId, confidence: number }[]): ProfileId =>
  [...profiles].sort((a, b) => b.confidence - a.confidence)[0]?.id ?? 'saver'

// The backend returns profiles highest confidence first.
export const primaryProfile = (c: Client) => c.profiles[0]!
