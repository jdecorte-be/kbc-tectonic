import { z } from 'zod'
import { analysisSchema, clientSchema } from '@/lib/api'

export const dashboardSegmentSchema = z.object({
  id: z.string(),
  label: z.string(),
  description: z.string(),
  evidence: z.array(z.string())
})

export const dashboardClientSchema = z.object({
  client: clientSchema,
  segments: z.array(dashboardSegmentSchema),
  context: z.object({
    observation_days: z.number(),
    monthly_income_cents: z.number(),
    savings_cents: z.number(),
    investment_cents: z.number(),
    recurring_payment_count: z.number(),
    summary: z.string()
  }),
  analysis: z.object({
    status: z.union([z.literal('not_analyzed'), analysisSchema.shape.status]),
    category: z.object({ id: z.string(), label: z.string() }).nullable(),
    summary: z.string(),
    created_at: z.string().nullable(),
    source: z.enum(['analysis', 'benchmark']).nullable(),
    id: z.string().nullable(),
    ads: z.array(z.object({
      product_id: z.string(),
      product_name: z.string(),
      title: z.string(),
      reason: z.string(),
      confidence: z.number()
    }))
  })
})

export const customerNetworkSchema = z.object({
  nodes: z.array(z.object({
    id: z.string(),
    label: z.string(),
    kind: z.enum(['segment', 'client', 'product']),
    client_id: z.string().optional(),
    count: z.number().optional()
  })),
  links: z.array(z.object({ source: z.string(), target: z.string(), kind: z.enum(['segment', 'recommendation']) })),
  shown_clients: z.number(),
  total_clients: z.number()
})

export const dashboardSchema = z.object({
  summary: z.object({
    total_clients: z.number(),
    opt_in_count: z.number(),
    opt_out_count: z.number(),
    analyzed_count: z.number(),
    recommended_count: z.number(),
    not_analyzed_count: z.number(),
    abstained_count: z.number(),
    error_count: z.number(),
    selected_ad_count: z.number(),
    total_balance_cents: z.number(),
    total_transactions: z.number()
  }),
  segments: z.array(z.object({ id: z.string(), label: z.string(), count: z.number(), description: z.string() })),
  outcomes: z.array(z.object({ id: z.string(), label: z.string(), count: z.number() })),
  products: z.array(z.object({ id: z.string(), name: z.string(), count: z.number() })),
  cashflow: z.array(z.object({ month: z.string(), credit_cents: z.number(), debit_cents: z.number() })),
  clients: z.object({ items: z.array(dashboardClientSchema), total: z.number() }),
  network: customerNetworkSchema,
  generated_at: z.string()
})

export type Dashboard = z.infer<typeof dashboardSchema>
export type DashboardClient = z.infer<typeof dashboardClientSchema>
export type CustomerNetworkData = z.infer<typeof customerNetworkSchema>
