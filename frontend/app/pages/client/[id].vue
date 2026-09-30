<script setup lang="ts">
import type { ChartConfig } from '@/components/ui/chart'
import { IconArrowLeft } from '@tabler/icons-vue'
import { VisArea, VisAxis, VisLine, VisXYContainer } from '@unovis/vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ChartContainer, ChartCrosshair, ChartTooltip, ChartTooltipContent, componentToString } from '@/components/ui/chart'
import { PROFILES, getClient } from '@/data/mock'

const route = useRoute()
const client = getClient(String(route.params.id))
if (!client) {
  throw createError({ statusCode: 404, statusMessage: 'Client not found', fatal: true })
}
definePageMeta({ title: 'Client' })

const months = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep']
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
      </div>
      <div class="flex flex-wrap gap-1 sm:ml-auto">
        <Badge
          v-for="p in client.profiles"
          :key="p.id"
          :variant="p === main ? 'default' : 'outline'"
        >
          {{ PROFILES[p.id].label }} {{ p.confidence }}%
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
          <CardDescription>Last 6 months</CardDescription>
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
          <CardDescription>Based on main profile: {{ PROFILES[main.id].label }}</CardDescription>
        </CardHeader>
        <CardContent class="grid gap-3">
          <div class="bg-primary/10 rounded-md p-3 font-medium">
            {{ PROFILES[main.id].offer }}
          </div>
          <div
            v-for="p in client.profiles.slice(1)"
            :key="p.id"
            class="rounded-md border p-3 text-sm"
          >
            <div class="text-muted-foreground text-xs">
              Secondary · {{ p.confidence }}%
            </div>
            {{ PROFILES[p.id].offer }}
          </div>
        </CardContent>
      </Card>
    </div>

    <div class="grid gap-4 lg:grid-cols-2">
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

      <Card>
        <CardHeader>
          <CardTitle>Recent transactions</CardTitle>
          <CardDescription>Latest activity</CardDescription>
        </CardHeader>
        <CardContent>
          <ul class="divide-y text-sm">
            <li
              v-for="t in client.transactions"
              :key="t.date + t.merchant"
              class="flex justify-between gap-3 py-2"
            >
              <span>
                {{ t.merchant }}
                <span class="text-muted-foreground block text-xs">{{ t.category }} · {{ t.date }}</span>
              </span>
              <span
                class="tabular-nums"
                :class="t.amount > 0 && 'text-primary'"
              >{{ eur(t.amount) }}</span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  </div>
</template>
