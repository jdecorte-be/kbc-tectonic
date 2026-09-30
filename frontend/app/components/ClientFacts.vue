<script setup lang="ts">
import type { ChartConfig } from '@/components/ui/chart'
import { VisArea, VisAxis, VisLine, VisXYContainer } from '@unovis/vue'
import { z } from 'zod'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardAction, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { ChartContainer, ChartCrosshair, ChartLegendContent, ChartTooltip, ChartTooltipContent, componentToString } from '@/components/ui/chart'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { counterpartyName, euros, transactionCategory, type ClientDetail } from '@/lib/api'

const props = defineProps<{ detail: ClientDetail }>()
const expanded = ref(false)
const cashflowSchema = z.array(z.object({ month: z.string(), credit_cents: z.number(), debit_cents: z.number() }))
const cashflow = computed(() => {
  const result = cashflowSchema.safeParse(props.detail.facts.monthly_cashflow)
  return result.success ? result.data.map((row, index) => ({ index, month: row.month, credit: row.credit_cents / 100, debit: row.debit_cents / 100 })) : []
})
type CashflowPoint = typeof cashflow.value[number]
const chartConfig = {
  debit: { label: 'Debits (€)', color: 'var(--chart-1)' },
  credit: { label: 'Credits (€)', color: 'var(--chart-3)' }
} satisfies ChartConfig
const maxY = computed(() => Math.max(1, ...cashflow.value.flatMap(row => [row.credit, row.debit])) * 1.15)
const fmtAmount = (value: number) => new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'EUR', notation: 'compact', maximumFractionDigits: 1 }).format(value)
const fmtMonth = (index: number | Date) => {
  const month = cashflow.value[Math.round(+index)]?.month
  return month ? new Date(`${month}-01T00:00:00Z`).toLocaleDateString('en-GB', { month: 'short', timeZone: 'UTC' }) : ''
}
const transactions = computed(() => [...props.detail.transactions].sort((a, b) => String(b.date).localeCompare(String(a.date))))
const visibleTransactions = computed(() => expanded.value ? transactions.value : transactions.value.slice(0, 5))
const signedAmount = (transaction: Record<string, unknown>) => {
  const raw = Number(transaction.montant ?? 0)
  return `${String(transaction.sens).toLowerCase() === 'debit' ? '−' : '+'}${euros(raw)}`
}
const date = (raw: unknown) => typeof raw === 'string' ? new Date(raw).toLocaleDateString('en-BE', { day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC' }) : '—'
watch(() => props.detail.client.id, () => {
  expanded.value = false
})
</script>

<template>
  <div class="grid min-w-0 gap-4">
    <Card class="pt-0">
      <CardHeader class="flex flex-wrap items-center gap-2 space-y-0 border-b py-4">
        <div class="grid flex-1 gap-1">
          <CardTitle>Cash flow trend</CardTitle>
          <CardDescription>Observed monthly credits and debits, including transfers</CardDescription>
        </div>
        <Badge variant="outline">
          {{ cashflow.length }} {{ cashflow.length === 1 ? 'month' : 'months' }}
        </Badge>
      </CardHeader>
      <CardContent class="px-2 pt-2 sm:px-4">
        <ChartContainer
          v-if="cashflow.length > 1"
          :config="chartConfig"
          class="aspect-auto h-[220px] w-full"
          :cursor="false"
        >
          <VisXYContainer
            :key="detail.client.id"
            :data="cashflow"
            :margin="{ left: 8, right: 8 }"
            :y-domain="[0, maxY]"
          >
            <VisArea
              :x="(row: CashflowPoint) => row.index"
              :y="(row: CashflowPoint) => row.debit"
              :color="chartConfig.debit.color"
              :opacity="0.15"
            />
            <VisLine
              :x="(row: CashflowPoint) => row.index"
              :y="(row: CashflowPoint) => row.debit"
              :color="chartConfig.debit.color"
              :line-width="1.5"
            />
            <VisLine
              :x="(row: CashflowPoint) => row.index"
              :y="(row: CashflowPoint) => row.credit"
              :color="chartConfig.credit.color"
              :line-width="1.5"
            />
            <VisAxis
              type="x"
              :tick-line="false"
              :domain-line="false"
              :grid-line="false"
              :tick-values="cashflow.map(row => row.index)"
              :tick-format="fmtMonth"
            />
            <VisAxis
              type="y"
              :num-ticks="3"
              :tick-line="false"
              :domain-line="false"
              :tick-format="fmtAmount"
            />
            <ChartTooltip />
            <ChartCrosshair
              :template="componentToString(chartConfig, ChartTooltipContent, { labelFormatter: fmtMonth })"
              :color="(row: CashflowPoint, index: number) => [chartConfig.debit.color, chartConfig.credit.color][index % 2]"
            />
          </VisXYContainer>
          <ChartLegendContent />
        </ChartContainer>
        <p
          v-else
          class="text-muted-foreground flex min-h-40 items-center justify-center px-4 text-center text-sm"
        >
          At least two observed months are needed to show a trend.
        </p>
      </CardContent>
      <CardFooter class="flex-wrap justify-between gap-3 text-sm">
        <span><span class="text-muted-foreground">Observed credits</span> <span class="ml-1 font-medium tabular-nums">{{ euros(Number(detail.facts.total_credit_cents ?? 0) / 100) }}</span></span>
        <span><span class="text-muted-foreground">Observed debits</span> <span class="ml-1 font-medium tabular-nums">{{ euros(Number(detail.facts.total_debit_cents ?? 0) / 100) }}</span></span>
      </CardFooter>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Transactions</CardTitle>
        <CardDescription>{{ expanded ? 'Full observed history' : 'Most recent activity' }}</CardDescription>
        <CardAction>
          <Badge variant="outline">
            {{ detail.transactions.length }} total
          </Badge>
        </CardAction>
      </CardHeader>
      <CardContent>
        <p
          v-if="!detail.transactions.length"
          class="text-muted-foreground py-5 text-center text-sm"
        >
          No transactions available for this client.
        </p>
        <div
          v-else
          class="max-h-80 overflow-y-auto"
        >
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Merchant</TableHead>
                <TableHead class="hidden lg:table-cell">
                  Category
                </TableHead>
                <TableHead class="text-right">
                  Amount
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow
                v-for="transaction in visibleTransactions"
                :key="String(transaction.transaction_id)"
              >
                <TableCell class="text-muted-foreground tabular-nums">
                  {{ date(transaction.date) }}
                </TableCell>
                <TableCell class="max-w-56 truncate font-medium">
                  {{ counterpartyName(transaction.contrepartie) }}
                  <span
                    v-if="expanded"
                    class="text-muted-foreground block text-xs font-normal"
                  >{{ transaction.transaction_id }}</span>
                </TableCell>
                <TableCell class="text-muted-foreground hidden lg:table-cell">
                  {{ transactionCategory(transaction.categorie) }}
                </TableCell>
                <TableCell
                  class="text-right tabular-nums"
                  :class="String(transaction.sens).toLowerCase() === 'credit' ? 'text-primary' : ''"
                >
                  {{ signedAmount(transaction) }}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </CardContent>
      <CardFooter
        v-if="detail.transactions.length > 5"
        class="justify-between gap-3"
      >
        <span class="text-muted-foreground text-xs">{{ visibleTransactions.length }} of {{ detail.transactions.length }} transactions</span>
        <Button
          variant="outline"
          size="sm"
          @click="expanded = !expanded"
        >
          {{ expanded ? 'Show recent' : 'View full history' }}
        </Button>
      </CardFooter>
    </Card>
  </div>
</template>
