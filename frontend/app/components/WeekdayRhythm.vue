<script setup lang="ts">
import type { ChartConfig } from '@/components/ui/chart'
import { VisAxis, VisStackedBar, VisXYContainer } from '@unovis/vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  ChartContainer,
  ChartCrosshair,
  ChartTooltip,
  ChartTooltipContent,
  componentToString
} from '@/components/ui/chart'
import { weekdayRhythm } from '@/data/mock'

type Row = typeof weekdayRhythm[number]

const chartConfig = {
  spend: { label: 'Avg spend (€)', color: 'var(--chart-1)' }
} satisfies ChartConfig

const data = weekdayRhythm
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle>Spending rhythm</CardTitle>
      <CardDescription>Average spend per weekday — Friday and Saturday peak</CardDescription>
    </CardHeader>
    <CardContent>
      <ChartContainer
        :config="chartConfig"
        class="aspect-auto h-[180px] w-full"
        :cursor="false"
      >
        <VisXYContainer
          :data="data"
          :margin="{ left: -10 }"
        >
          <VisStackedBar
            :x="(_: Row, i: number) => i"
            :y="(d: Row) => d.spend"
            :color="chartConfig.spend.color"
            :rounded-corners="4"
            :bar-padding="0.25"
          />
          <VisAxis
            type="x"
            :tick-line="false"
            :domain-line="false"
            :grid-line="false"
            :num-ticks="7"
            :tick-format="(i: number) => data[i]?.day ?? ''"
          />
          <VisAxis
            type="y"
            :num-ticks="3"
            :tick-line="false"
            :domain-line="false"
          />
          <ChartTooltip />
          <ChartCrosshair
            :template="componentToString(chartConfig, ChartTooltipContent, { labelFormatter: (i: number | Date) => data[+i]?.day ?? '' })"
            :color="chartConfig.spend.color"
          />
        </VisXYContainer>
      </ChartContainer>
    </CardContent>
  </Card>
</template>
