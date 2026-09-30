<script setup lang="ts">
import type { ChartConfig } from '@/components/ui/chart'
import { VisArea, VisAxis, VisLine, VisXYContainer } from '@unovis/vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  ChartContainer,
  ChartCrosshair,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
  componentToString
} from '@/components/ui/chart'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { HABITS } from '@/types/api'
import type { Habit, WeekPoint as ApiWeekPoint } from '@/types/api'

type WeekPoint = Omit<ApiWeekPoint, 'date'> & { date: Date }

const habit = ref<Habit>('Travel')
const dash = await useDashboard()
const data = computed<WeekPoint[]>(() => (dash.value?.habitTrends[habit.value] ?? []).map(p => ({ ...p, date: new Date(p.date) })))

const chartConfig = {
  spend: { label: 'Avg weekly spend (€)', color: 'var(--chart-1)' },
  baseline: { label: 'Client baseline (€)', color: 'var(--chart-3)' }
} satisfies ChartConfig

const svgDefs = `
  <linearGradient id="fillSpend" x1="0" y1="0" x2="0" y2="1">
    <stop offset="5%" stop-color="var(--color-spend)" stop-opacity="0.8" />
    <stop offset="95%" stop-color="var(--color-spend)" stop-opacity="0.1" />
  </linearGradient>
`
const fmtDate = (d: number) => new Date(d).toLocaleDateString('en-GB', { month: 'short', day: 'numeric' })
const maxY = computed(() => Math.ceil(Math.max(...data.value.map(p => p.spend)) * 1.15))
</script>

<template>
  <Card class="pt-0">
    <CardHeader class="flex items-center gap-2 space-y-0 border-b py-5 sm:flex-row">
      <div class="grid flex-1 gap-1">
        <CardTitle>Habit trend</CardTitle>
        <CardDescription>Average weekly spend per client vs. their own baseline, last 12 weeks</CardDescription>
      </div>
      <Select v-model="habit">
        <SelectTrigger
          class="w-[160px] rounded-lg sm:ml-auto"
          aria-label="Habit"
        >
          <SelectValue placeholder="Habit" />
        </SelectTrigger>
        <SelectContent class="rounded-xl">
          <SelectItem
            v-for="h in HABITS"
            :key="h"
            :value="h"
            class="rounded-lg"
          >
            {{ h }}
          </SelectItem>
        </SelectContent>
      </Select>
    </CardHeader>
    <CardContent class="px-2 pt-4 sm:px-6 sm:pt-6 pb-4">
      <ChartContainer
        :config="chartConfig"
        class="aspect-auto h-[250px] w-full"
        :cursor="false"
      >
        <VisXYContainer
          :data="data"
          :svg-defs="svgDefs"
          :margin="{ left: -20 }"
          :y-domain="[0, maxY]"
        >
          <VisArea
            :x="(d: WeekPoint) => d.date"
            :y="(d: WeekPoint) => d.spend"
            color="url(#fillSpend)"
            :opacity="0.6"
          />
          <VisLine
            :x="(d: WeekPoint) => d.date"
            :y="(d: WeekPoint) => d.spend"
            :color="chartConfig.spend.color"
            :line-width="1.5"
          />
          <VisLine
            :x="(d: WeekPoint) => d.date"
            :y="(d: WeekPoint) => d.baseline"
            :color="chartConfig.baseline.color"
            :line-width="1.5"
          />
          <VisAxis
            type="x"
            :x="(d: WeekPoint) => d.date"
            :tick-line="false"
            :domain-line="false"
            :grid-line="false"
            :num-ticks="6"
            :tick-format="fmtDate"
          />
          <VisAxis
            type="y"
            :num-ticks="3"
            :tick-line="false"
            :domain-line="false"
          />
          <ChartTooltip />
          <ChartCrosshair
            :template="componentToString(chartConfig, ChartTooltipContent, { labelFormatter: (d: number | Date) => fmtDate(+d) })"
            :color="(d: WeekPoint, i: number) => [chartConfig.spend.color, chartConfig.baseline.color][i % 2]"
          />
        </VisXYContainer>
        <ChartLegendContent />
      </ChartContainer>
    </CardContent>
  </Card>
</template>
