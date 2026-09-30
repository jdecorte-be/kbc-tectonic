<script setup lang="ts">
import { IconAlertTriangle, IconBulb, IconCoin, IconTags, IconUsers } from '@tabler/icons-vue'

import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardAction,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle
} from '@/components/ui/card'
const dashboard = (await useDashboard()).value
const kpis = dashboard?.kpis ?? { clientsTracked: 0, profilesDetected: 0, habitChanges: 0, openOpportunities: 0 }
const jev = dashboard?.jevUsage ?? { requests: 0, clientsAnalysed: 0, inputTokens: 0, outputTokens: 0, costUsd: 0 }

const fmt = (n: number) => n.toLocaleString('en-BE')
// Jev is cheap, so show enough significant digits to see sub-cent amounts
const usd = (n: number) => '$' + (n === 0 || n >= 0.01 ? n.toFixed(2) : n.toPrecision(2))

const cards = [
  { label: 'Clients tracked', value: fmt(kpis.clientsTracked), badge: '+2.4%', icon: IconUsers, title: 'Transactions analysed daily', hint: 'Across all monitored accounts' },
  { label: 'Profiles detected', value: String(kpis.profilesDetected), badge: '4 core', icon: IconTags, title: 'Student to retiree', hint: 'Each client can hold several profiles' },
  { label: 'Habit changes this week', value: fmt(kpis.habitChanges), badge: 'vs. own baseline', icon: IconAlertTriangle, title: 'Drift detected per client', hint: 'Travel, overdraft and investing lead' },
  { label: 'Open opportunities', value: fmt(kpis.openOpportunities), badge: 'To action', icon: IconBulb, title: 'Offers triggered by a habit change', hint: 'e.g. travel insurance, ETF plan' },
  { label: 'Jev AI cost', value: usd(jev.costUsd), badge: `${fmt(jev.clientsAnalysed)} clients`, icon: IconCoin, title: `${fmt(jev.inputTokens)} input tokens`, hint: '$0.042 per 1M input tokens, output free' }
]
</script>

<template>
  <div class="*:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card dark:*:data-[slot=card]:bg-card grid grid-cols-1 gap-4 px-4 *:data-[slot=card]:bg-gradient-to-t *:data-[slot=card]:shadow-xs lg:px-6 @xl/main:grid-cols-2 @5xl/main:grid-cols-3 @7xl/main:grid-cols-5">
    <Card
      v-for="c in cards"
      :key="c.label"
      class="@container/card"
    >
      <CardHeader>
        <CardDescription>{{ c.label }}</CardDescription>
        <CardTitle class="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
          {{ c.value }}
        </CardTitle>
        <CardAction>
          <Badge variant="outline">
            <component :is="c.icon" />
            {{ c.badge }}
          </Badge>
        </CardAction>
      </CardHeader>
      <CardFooter class="flex-col items-start gap-1.5 text-sm">
        <div class="line-clamp-1 font-medium">
          {{ c.title }}
        </div>
        <div class="text-muted-foreground">
          {{ c.hint }}
        </div>
      </CardFooter>
    </Card>
  </div>
</template>
