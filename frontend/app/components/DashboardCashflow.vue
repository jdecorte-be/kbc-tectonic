<script setup lang="ts">
import type { ChartConfig } from '@/components/ui/chart'
import type { Dashboard } from '@/lib/dashboard'
import { VisArea, VisAxis, VisLine, VisXYContainer } from '@unovis/vue'
import { ChartContainer, ChartCrosshair, ChartLegendContent, ChartTooltip, ChartTooltipContent, componentToString } from '@/components/ui/chart'

const props = defineProps<{ cashflow: Dashboard['cashflow'] }>()
const points = computed(() => props.cashflow.map((row, index) => ({ index, month: row.month, credit: row.credit_cents / 100, debit: row.debit_cents / 100 })))
type Point = typeof points.value[number]
const config = {
  credit: { label: 'Credits (€)', color: 'var(--chart-1)' },
  debit: { label: 'Debits (€)', color: 'var(--chart-3)' }
} satisfies ChartConfig
const maxY = computed(() => Math.max(1, ...points.value.flatMap(point => [point.credit, point.debit])) * 1.1)
const formatMonth = (value: number | Date) => {
  const month = points.value[Math.round(+value)]?.month
  return month ? new Date(`${month}-01T00:00:00Z`).toLocaleDateString('en-GB', { month: 'short', timeZone: 'UTC' }) : ''
}
const formatAmount = (value: number) => new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'EUR', notation: 'compact', maximumFractionDigits: 1 }).format(value)
</script>

<template>
  <ChartContainer
    v-if="points.length > 1"
    :config="config"
    :cursor="false"
    class="aspect-auto h-52 w-full"
  >
    <VisXYContainer
      :data="points"
      :margin="{ left: 0, right: 6 }"
      :y-domain="[0, maxY]"
    >
      <VisArea
        :x="(point: Point) => point.index"
        :y="(point: Point) => point.credit"
        :color="config.credit.color"
        :opacity="0.1"
      />
      <VisLine
        :x="(point: Point) => point.index"
        :y="(point: Point) => point.credit"
        :color="config.credit.color"
        :line-width="2"
      />
      <VisLine
        :x="(point: Point) => point.index"
        :y="(point: Point) => point.debit"
        :color="config.debit.color"
        :line-width="2"
      />
      <VisAxis
        type="x"
        :tick-line="false"
        :domain-line="false"
        :grid-line="false"
        :tick-values="points.map(point => point.index)"
        :tick-format="formatMonth"
      />
      <VisAxis
        type="y"
        :num-ticks="3"
        :tick-line="false"
        :domain-line="false"
        :tick-format="formatAmount"
      />
      <ChartTooltip />
      <ChartCrosshair
        :template="componentToString(config, ChartTooltipContent, { labelFormatter: formatMonth })"
        :color="(_point: Point, index: number) => [config.credit.color, config.debit.color][index % 2]"
      />
    </VisXYContainer>
    <ChartLegendContent />
  </ChartContainer>
  <div
    v-else
    class="text-muted-foreground flex h-52 items-center justify-center px-6 text-center text-sm"
  >
    At least two observed months are needed to show a trend.
  </div>
</template>
