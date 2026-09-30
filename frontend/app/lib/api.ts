import { z } from 'zod'

export const clientSchema = z.object({
  id: z.string(), name: z.string(), age: z.number(), city: z.string(), country: z.string(),
  balance: z.number(), transaction_count: z.number(), personalization_allowed: z.boolean()
})
export const clientListSchema = z.object({ items: z.array(clientSchema), total: z.number() })
export const clientDetailSchema = z.object({
  client: clientSchema, facts: z.record(z.string(), z.unknown()), transactions: z.array(z.record(z.string(), z.unknown()))
})
export const healthSchema = z.object({
  status: z.literal('ok'), jev_configured: z.boolean(), model: z.string(), client_count: z.number(), product_count: z.number(), openai_configured: z.boolean().optional(), openai_model: z.string().optional(), category_count: z.number().optional(),
  pricing: z.object({ input_usd_per_million: z.number(), output_usd_per_million: z.number(), source: z.string() })
})
export const productsSchema = z.object({ items: z.array(z.object({ id: z.string(), name: z.string(), description: z.string() })) })
export const usageSourceSchema = z.enum(['provider', 'estimated', 'none'])
export const categoriesSchema = z.object({
  items: z.array(z.object({ id: z.string(), label: z.string(), description: z.string(), source: z.string(), created_at: z.string(), client_count: z.number() })),
  questions: z.array(z.object({ id: z.string(), instructions: z.string() }))
})
export const providerMetricsSchema = z.record(z.string(), z.object({ api_calls: z.number(), input_tokens: z.number(), output_tokens: z.number(), estimated_cost_usd: z.number() }))
export const registrySnapshotSchema = z.object({ count: z.number(), labels: z.array(z.string()) })
export const categorySchema = z.object({ id: z.string(), label: z.string(), source: z.enum(['jev', 'openai', 'unknown']), confidence: z.number(), evidence: z.array(z.string()), created: z.boolean() })
export const analysisSchema = z.object({
  client: clientSchema,
  status: z.enum(['recommended', 'insufficient_information', 'no_match', 'opt_out', 'error']),
  summary: z.string(),
  category: categorySchema.nullable().optional(),
  profiles: z.array(z.object({ id: z.string(), label: z.string(), confidence: z.number().min(0).max(1), evidence: z.array(z.string()) })),
  facts: z.record(z.string(), z.unknown()), missing_information: z.array(z.string()),
  ads: z.array(z.object({
    product_id: z.string(), product_name: z.string(), title: z.string(), body: z.string(), reason: z.string(),
    confidence: z.number().min(0).max(1), evidence: z.array(z.string())
  })),
  products_evaluated: z.number(),
  metrics: z.object({ duration_ms: z.number(), api_calls: z.number(), openai_calls: z.number().default(0), providers: providerMetricsSchema.optional(), jev_calls: z.number().optional(), input_tokens: z.number(), output_tokens: z.number(), estimated_cost_usd: z.number(), usage_source: usageSourceSchema }),
  stages: z.array(z.object({ name: z.string(), status: z.string(), duration_ms: z.number(), detail: z.string() })),
  error: z.string().nullable().optional()
})
export const benchmarkSchema = z.object({
  id: z.string(), status: z.enum(['running', 'completed', 'cancelled', 'failed']), requested_count: z.number(), completed_count: z.number(),
  category_registry_before: registrySnapshotSchema.optional(), category_registry_after: registrySnapshotSchema.nullable().optional(),
  concurrency: z.number(), elapsed_ms: z.number(), results: z.array(analysisSchema),
  metrics: z.object({
    duration_ms: z.number(), api_calls: z.number(), openai_calls: z.number().default(0), providers: providerMetricsSchema.optional(), jev_calls: z.number().optional(), input_tokens: z.number(), output_tokens: z.number(), estimated_cost_usd: z.number(),
    clients_per_second: z.number(), average_latency_ms: z.number(), p50_latency_ms: z.number(), p95_latency_ms: z.number(),
    recommended_count: z.number(), abstained_count: z.number(), opt_out_count: z.number(), error_count: z.number(), usage_source: usageSourceSchema
  }), error: z.string().nullable().optional()
})
export type ClientSummary = z.infer<typeof clientSchema>
export type ClientDetail = z.infer<typeof clientDetailSchema>
export type Analysis = z.infer<typeof analysisSchema>
export type Benchmark = z.infer<typeof benchmarkSchema>

export const statusLabels: Record<Analysis['status'], string> = {
  recommended: 'Relevant offers', insufficient_information: 'Insufficient information', no_match: 'No suitable offer', opt_out: 'Personalization declined', error: 'Technical error'
}
export const euros = (value: number) => new Intl.NumberFormat('en-BE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 2 }).format(value)
export const dollars = (value: number) => new Intl.NumberFormat('en-BE', { style: 'currency', currency: 'USD', minimumFractionDigits: 4, maximumFractionDigits: 6 }).format(value)
export const number = (value: number) => new Intl.NumberFormat('en-BE', { maximumFractionDigits: 2 }).format(value)
export const duration = (ms: number) => ms >= 60000 ? `${Math.floor(ms / 60000)} min ${Math.floor((ms % 60000) / 1000)} s` : `${number(ms / 1000)} s`
export const confidence = (value: number) => `${Math.round(value * 100)}%`
export function errorMessage(error: unknown): string {
  if (error instanceof z.ZodError) return 'The server response is incomplete or incompatible. Check the backend version.'
  if (error && typeof error === 'object' && 'data' in error) {
    const data = error.data as { detail?: unknown, message?: string } | undefined
    if (typeof data?.detail === 'string') return data.detail
    if (typeof data?.message === 'string') return data.message
  }
  return error instanceof Error ? error.message : 'The server is unavailable. Please try again shortly.'
}

const transactionCategories: Record<string, string> = {
  courses: 'Groceries', restauration_rapide: 'Fast food', restaurant: 'Restaurants', cafe_boulangerie: 'Cafés & bakeries', shopping: 'Shopping', electronique: 'Electronics', maison: 'Home & furniture', transport_public: 'Public transport', carburant: 'Fuel', loisirs: 'Leisure', sport: 'Sports', livres: 'Books', animaux: 'Pets', aide_familiale: 'Family support', job_etudiant: 'Student employment', revenu_activite: 'Business income', pension: 'Pension', salaire: 'Salary', loyer: 'Rent', credit_logement: 'Mortgage', energie: 'Energy', assurance_habitation: 'Home insurance', telecom: 'Telecom', abonnement: 'Subscriptions', assurance_auto: 'Car insurance', transfert_epargne: 'Savings transfer', investissement: 'Investments', remboursement_achat: 'Purchase refund', voyage_transport: 'Travel booking', hebergement_voyage: 'Travel accommodation', virement_entre_proches: 'Personal transfer', retrait_especes: 'Cash withdrawal'
}
export const transactionCategory = (value: unknown) => transactionCategories[String(value)] ?? String(value ?? 'Uncategorized').replaceAll('_', ' ')
export const countryName = (value: string) => ({ 'Belgique': 'Belgium', 'Pays-Bas': 'Netherlands', 'Allemagne': 'Germany' }[value] ?? value)
export const counterpartyName = (value: unknown) => String(value ?? 'Unknown counterparty').replaceAll('entreprise fictive', 'synthetic company').replaceAll('personne fictive', 'synthetic person').replaceAll('bailleur fictif', 'synthetic landlord').replaceAll('(fictive)', '(synthetic)').replaceAll('(fictif)', '(synthetic)').replaceAll('Compte épargne personnel fictif', 'Synthetic personal savings account').replaceAll('Compte investissement personnel fictif', 'Synthetic personal investment account').replaceAll('Organisme de pension fictif', 'Synthetic pension provider').replaceAll('Prêteur logement fictif', 'Synthetic mortgage lender').replaceAll('Assureur fictif', 'Synthetic insurer').replaceAll('Distributeur fictif', 'Synthetic ATM')
