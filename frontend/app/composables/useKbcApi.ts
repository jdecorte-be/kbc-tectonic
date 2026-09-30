import { analysisSchema, benchmarkSchema, categoriesSchema, clientDetailSchema, clientListSchema, healthSchema, productsSchema } from '@/lib/api'
import { dashboardClientSchema } from '@/lib/dashboard'

export function useKbcApi() {
  return {
    categories: async () => categoriesSchema.parse(await $fetch('/api/categories')),
    health: async () => healthSchema.parse(await $fetch('/api/health')),
    clients: async (q = '', limit = 50, offset = 0, optInOnly = false) => clientListSchema.parse(await $fetch('/api/clients', { query: { q, limit, offset, opt_in_only: optInOnly } })),
    client: async (id: string) => clientDetailSchema.parse(await $fetch(`/api/clients/${encodeURIComponent(id)}`)),
    clientContext: async (id: string) => dashboardClientSchema.parse(await $fetch(`/api/clients/${encodeURIComponent(id)}/context`)),
    products: async () => productsSchema.parse(await $fetch('/api/products')),
    analyze: async (clientId: string) => analysisSchema.parse(await $fetch('/api/analyses', { method: 'POST', body: { client_id: clientId }, timeout: 180000, retry: 0 })),
    startBenchmark: async (count: number, concurrency: number) => benchmarkSchema.parse(await $fetch('/api/benchmarks', { method: 'POST', body: { count, concurrency }, retry: 0 })),
    benchmark: async (id: string) => benchmarkSchema.parse(await $fetch(`/api/benchmarks/${encodeURIComponent(id)}`)),
    cancelBenchmark: async (id: string) => benchmarkSchema.parse(await $fetch(`/api/benchmarks/${encodeURIComponent(id)}`, { method: 'DELETE', retry: 0 }))
  }
}
