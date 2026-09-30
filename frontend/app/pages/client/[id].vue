<script setup lang="ts">
import type { ChartConfig } from '@/components/ui/chart'
import { IconArrowLeft } from '@tabler/icons-vue'
import { VisArea, VisAxis, VisLine, VisXYContainer } from '@unovis/vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ChartContainer, ChartCrosshair, ChartTooltip, ChartTooltipContent, componentToString } from '@/components/ui/chart'

const route = useRoute()
const { data: clientData } = await useClient(String(route.params.id))
const client = clientData.value
if (!client) {
  throw createError({ statusCode: 404, statusMessage: 'Client not found', fatal: true })
}
definePageMeta({ title: 'Client' })

const months = client.spendMonths
const series = client.monthlySpend.map((spend, i) => ({ i, spend }))
type Row = typeof series[number]

const chartConfig = {
  spend: { label: 'Monthly spend (€)', color: 'var(--chart-1)' }
} satisfies ChartConfig

const eur = (n: number) => `${n < 0 ? '-' : n > 0 ? '+' : ''}€${Math.abs(n).toLocaleString('en-BE', { maximumFractionDigits: 2 })}`
const fmtMonth = (i: number | Date) => months[Math.round(+i)] ?? ''
const main = client.profiles[0]!
const avgSpend = Math.round(client.monthlySpend.reduce((a, b) => a + b, 0) / client.monthlySpend.length)

const tiles = [
  { label: 'Avg. monthly spend', value: `€${avgSpend.toLocaleString('en-BE')}` },
  { label: 'Savings rate', value: `${client.savingsRate}%` },
  { label: 'Recurring payments', value: client.recurringCount },
  { label: 'Cash share', value: `${client.cashShare}%` }
]

const [allClients, relations, profiles] = await Promise.all([useClients(), useRelations(), useProfiles()])
const related = (relations.value[client.id] ?? [])
  .map(r => ({ ...r, client: allClients.value.find(c => c.id === r.clientId)! }))
  .filter(r => r.client)

const lastScanned = new Date(client.lastScanned).toLocaleString('en-BE', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'UTC' })

// Radial relation graph: client in the centre, related clients on a ring.
const GRAPH = { w: 640, h: 320, r: 120 }
const nodes = related.map((r, i) => {
  const a = (2 * Math.PI * i) / related.length - Math.PI / 2
  return { ...r, x: GRAPH.w / 2 + GRAPH.r * 1.6 * Math.cos(a), y: GRAPH.h / 2 + GRAPH.r * Math.sin(a) }
})

useSeoMeta({ title: client.name })
</script>

<template>
  <div class="flex flex-col gap-4 px-4 lg:px-6">
    <div>
      <Button
        variant="ghost"
        size="sm"
        as-child
      >
        <NuxtLink to="/client">
          <IconArrowLeft /> All clients
        </NuxtLink>
      </Button>
    </div>

    <div class="flex flex-wrap items-center gap-3">
      <div>
        <h2 class="text-2xl font-semibold">
          {{ client.name }}
        </h2>
        <p class="text-muted-foreground text-sm">
          {{ client.age }} years · payday on the {{ client.payday }}th · top habit: {{ client.topHabit }}
        </p>
        <p class="text-muted-foreground text-xs">
          Last scanned: {{ lastScanned }} UTC
        </p>
      </div>
      <div class="flex flex-wrap gap-1 sm:ml-auto">
        <Badge
          v-for="p in client.profiles"
          :key="p.id"
          :variant="p === main ? 'default' : 'outline'"
        >
          {{ profiles[p.id].label }} {{ p.confidence }}%
        </Badge>
      </div>
    </div>

    <div
      v-if="client.change"
      class="bg-primary/10 flex flex-wrap items-center gap-2 rounded-xl p-3 text-sm"
    >
      <Badge :variant="client.change.severity === 'alert' ? 'destructive' : 'secondary'">
        Habit change · {{ client.change.delta > 0 ? '+' : '' }}{{ client.change.delta }}%
      </Badge>
      {{ client.change.text }}
    </div>

    <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <div
        v-for="t in tiles"
        :key="t.label"
        class="rounded-xl border p-4"
      >
        <div class="text-muted-foreground text-sm">
          {{ t.label }}
        </div>
        <div class="text-2xl font-semibold tabular-nums">
          {{ t.value }}
        </div>
      </div>
    </div>

    <div class="grid gap-4 lg:grid-cols-3">
      <Card class="lg:col-span-2">
        <CardHeader>
          <CardTitle>Spending trend</CardTitle>
          <CardDescription>Per 30 days, last {{ months.length }} periods</CardDescription>
        </CardHeader>
        <CardContent>
          <ChartContainer
            :config="chartConfig"
            class="aspect-auto h-[220px] w-full"
            :cursor="false"
          >
            <VisXYContainer
              :data="series"
              :margin="{ left: -10 }"
              :y-domain="[0, Math.max(...client.monthlySpend) * 1.2]"
            >
              <VisArea
                :x="(d: Row) => d.i"
                :y="(d: Row) => d.spend"
                :color="chartConfig.spend.color"
                :opacity="0.25"
              />
              <VisLine
                :x="(d: Row) => d.i"
                :y="(d: Row) => d.spend"
                :color="chartConfig.spend.color"
                :line-width="2"
              />
              <VisAxis
                type="x"
                :tick-line="false"
                :domain-line="false"
                :grid-line="false"
                :num-ticks="5"
                :tick-format="fmtMonth"
              />
              <VisAxis
                type="y"
                :num-ticks="3"
                :tick-line="false"
                :domain-line="false"
              />
              <ChartTooltip />
              <ChartCrosshair
                :template="componentToString(chartConfig, ChartTooltipContent, { labelFormatter: fmtMonth })"
                :color="chartConfig.spend.color"
              />
            </VisXYContainer>
          </ChartContainer>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Suggested action</CardTitle>
          <CardDescription>Based on main profile: {{ profiles[main.id].label }}</CardDescription>
        </CardHeader>
        <CardContent class="grid gap-3">
          <div class="bg-primary/10 rounded-md p-3 font-medium">
            {{ profiles[main.id].offer }}
          </div>
          <div
            v-for="p in client.profiles.slice(1)"
            :key="p.id"
            class="rounded-md border p-3 text-sm"
          >
            <div class="text-muted-foreground text-xs">
              Secondary · {{ p.confidence }}%
            </div>
            {{ profiles[p.id].offer }}
          </div>
        </CardContent>
      </Card>
    </div>

    <div class="grid gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Why this profile</CardTitle>
          <CardDescription>Signals detected in the transactions</CardDescription>
        </CardHeader>
        <CardContent class="grid gap-3">
          <div
            v-for="s in client.signals"
            :key="s.text"
            class="grid gap-1"
          >
            <div class="flex justify-between gap-3 text-sm">
              <span>{{ s.text }}</span>
              <span class="text-muted-foreground tabular-nums">{{ Math.round(s.weight * 100) }}%</span>
            </div>
            <div class="bg-muted h-1.5 overflow-hidden rounded-full">
              <div
                class="bg-primary h-full rounded-full"
                :style="{ width: `${s.weight * 100}%` }"
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>

    <Card>
      <CardHeader>
        <CardTitle>Related clients</CardTitle>
        <CardDescription>Linked accounts and clients with a similar profile</CardDescription>
      </CardHeader>
      <CardContent>
        <p
          v-if="!related.length"
          class="text-muted-foreground text-sm"
        >
          No related clients.
        </p>
        <svg
          v-if="related.length"
          :viewBox="`0 0 ${GRAPH.w} ${GRAPH.h}`"
          class="mb-4 h-auto w-full max-w-2xl"
          role="img"
          aria-label="Relation graph"
        >
          <line
            v-for="n in nodes"
            :key="`l-${n.client.id}`"
            :x1="GRAPH.w / 2"
            :y1="GRAPH.h / 2"
            :x2="n.x"
            :y2="n.y"
            class="stroke-primary"
            :stroke-width="n.kind === 'linked' ? 2.5 : 1"
            :stroke-dasharray="n.kind === 'linked' ? undefined : '4 4'"
          />
          <NuxtLink
            v-for="n in nodes"
            :key="n.client.id"
            :to="`/client/${n.client.id}`"
          >
            <circle
              :cx="n.x"
              :cy="n.y"
              r="9"
              class="fill-background stroke-primary"
              stroke-width="2"
            />
            <text
              :x="n.x"
              :y="n.y + 24"
              text-anchor="middle"
              class="fill-foreground text-[11px]"
            >{{ n.client.name }}</text>
          </NuxtLink>
          <circle
            :cx="GRAPH.w / 2"
            :cy="GRAPH.h / 2"
            r="14"
            class="fill-primary"
          />
          <text
            :x="GRAPH.w / 2"
            :y="GRAPH.h / 2 + 30"
            text-anchor="middle"
            class="fill-foreground text-xs font-semibold"
          >{{ client.name }}</text>
        </svg>
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <NuxtLink
            v-for="r in related"
            :key="r.client.id"
            :to="`/client/${r.client.id}`"
            class="hover:bg-muted/50 flex flex-col gap-2 rounded-xl border p-3 transition-colors"
          >
            <div class="flex items-center justify-between gap-2">
              <span class="font-medium">{{ r.client.name }}</span>
              <Badge :variant="r.kind === 'linked' ? 'default' : 'outline'">
                {{ r.kind === 'linked' ? 'Linked' : 'Similar' }}
              </Badge>
            </div>
            <span class="text-muted-foreground text-xs">{{ profiles[r.client.profiles[0]!.id].label }} · {{ r.client.age }} y</span>
            <span class="text-xs">{{ r.reason }}</span>
          </NuxtLink>
        </div>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Transactions</CardTitle>
        <CardDescription>{{ client.transactions.length }} most recent</CardDescription>
      </CardHeader>
      <CardContent>
        <table class="w-full text-sm">
          <thead class="text-muted-foreground text-left text-xs">
            <tr>
              <th class="py-2 font-medium">Date</th>
              <th class="py-2 font-medium">Merchant</th>
              <th class="py-2 font-medium">Category</th>
              <th class="py-2 text-right font-medium">Amount</th>
            </tr>
          </thead>
          <tbody class="divide-y">
            <tr
              v-for="t in client.transactions"
              :key="t.date + t.merchant"
            >
              <td class="py-2 tabular-nums">{{ t.date }}</td>
              <td class="py-2">{{ t.merchant }}</td>
              <td class="text-muted-foreground py-2">{{ t.category }}</td>
              <td
                class="py-2 text-right tabular-nums"
                :class="t.amount > 0 && 'text-primary'"
              >{{ eur(t.amount) }}</td>
            </tr>
          </tbody>
        </table>
      </CardContent>
    </Card>
  </div>
</template>
