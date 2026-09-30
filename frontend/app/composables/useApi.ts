import type { Client, Dashboard, JevTrackers, ProfileDef, ProfileId, Relation } from '@/types/api'

export const useApiBase = () => useRuntimeConfig().public.apiBase as string

export async function useClients() {
  const base = useApiBase()
  const { data } = await useFetch<Client[]>(`${base}/api/clients`, { key: 'clients', default: () => [] })
  return data as Ref<Client[]>
}

export async function useClient(id: string) {
  const base = useApiBase()
  return useFetch<Client>(`${base}/api/clients/${id}`, { key: `client-${id}` })
}

export async function useDashboard() {
  const base = useApiBase()
  const { data } = await useFetch<Dashboard>(`${base}/api/dashboard`, { key: 'dashboard' })
  return data as Ref<Dashboard | null>
}

// Profile catalogue keyed by id, e.g. `profiles.value.student.label`.
export async function useProfiles() {
  const base = useApiBase()
  const { data } = await useFetch<ProfileDef[]>(`${base}/api/profiles`, { key: 'profiles', default: () => [] })
  return computed(() => Object.fromEntries(data.value.map(p => [p.id, p])) as Record<ProfileId, ProfileDef>)
}

// Related clients per client id (explicit links first, then similar clients).
export async function useRelations(limit = 4) {
  const base = useApiBase()
  const { data } = await useFetch<Record<string, Relation[]>>(`${base}/api/relations`, { key: `relations-${limit}`, query: { limit }, default: () => ({}) })
  return data as Ref<Record<string, Relation[]>>
}

// Cached Jev trackers per dashboard client; `run()` re-scores every client via the backend.
export async function useJev() {
  const base = useApiBase()
  const { data, refresh } = await useFetch<JevTrackers | null>(`${base}/api/jev/clients`, { key: 'jev', default: () => null })
  const running = ref(false)
  const error = ref<string | null>(null)
  async function run() {
    running.value = true
    error.value = null
    try {
      data.value = await $fetch<JevTrackers>(`${base}/api/jev/clients`, { method: 'POST' })
    } catch (e) {
      error.value = (e as { data?: { detail?: string } }).data?.detail ?? 'Jev request failed'
    } finally {
      running.value = false
    }
  }
  return { data, refresh, run, running, error }
}
