<script setup lang="ts">
import { IconArrowDownLeft, IconArrowUpRight, IconCalendar, IconCreditCard, IconWallet } from '@tabler/icons-vue'
import { counterpartyName, euros, number, transactionCategory, type ClientDetail } from '@/lib/api'

defineProps<{ detail: ClientDetail }>()
const signedAmount = (transaction: Record<string, unknown>) => {
  const raw = Number(transaction.montant ?? 0)
  return `${String(transaction.sens).toLowerCase() === 'debit' ? '−' : '+'}${euros(raw)}`
}
const date = (raw: unknown) => typeof raw === 'string' ? new Date(raw).toLocaleDateString('en-BE', { day: '2-digit', month: 'short' }) : '—'
</script>

<template>
  <div class="flex flex-col gap-5">
    <div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <div
        v-for="stat in [
          { label: 'Account balance', value: euros(detail.client.balance), icon: IconWallet },
          { label: 'Transactions', value: number(detail.client.transaction_count), icon: IconCreditCard },
          { label: 'Observed history', value: `${detail.facts.observation_days ?? '—'} days`, icon: IconCalendar },
          { label: 'Observed credits', value: euros(Number(detail.facts.total_credit_cents ?? 0) / 100), icon: IconArrowDownLeft }
        ]"
        :key="stat.label"
        class="bg-background/40 rounded-lg border p-3.5"
      >
        <div class="text-muted-foreground mb-2 flex items-center justify-between gap-2 text-xs">
          <span>{{ stat.label }}</span><component
            :is="stat.icon"
            class="size-3.5"
          />
        </div>
        <p class="text-lg font-semibold tracking-tight tabular-nums">
          {{ stat.value }}
        </p>
      </div>
    </div>
    <div>
      <div class="mb-3 flex items-center justify-between">
        <h3 class="text-xs font-medium tracking-wide uppercase">
          Recent transactions
        </h3><span class="text-muted-foreground text-xs">{{ Math.min(5, detail.transactions.length) }} transactions</span>
      </div>
      <div
        v-if="!detail.transactions.length"
        class="text-muted-foreground rounded-lg border border-dashed p-5 text-center text-sm"
      >
        No transactions available for this client.
      </div>
      <div
        v-else
        class="divide-y"
      >
        <div
          v-for="transaction in [...detail.transactions].sort((a, b) => String(b.date).localeCompare(String(a.date))).slice(0, 5)"
          :key="String(transaction.transaction_id)"
          class="flex items-center gap-3 py-2.5"
        >
          <div class="bg-muted text-muted-foreground flex size-8 shrink-0 items-center justify-center rounded-full">
            <IconArrowDownLeft
              v-if="String(transaction.sens).toLowerCase() === 'credit'"
              class="size-4"
            /><IconArrowUpRight
              v-else
              class="size-4"
            />
          </div>
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm">
              {{ counterpartyName(transaction.contrepartie) }}
            </p><p class="text-muted-foreground truncate text-[11px]">
              {{ transactionCategory(transaction.categorie) }} · {{ date(transaction.date) }}
            </p>
          </div>
          <span
            class="text-sm font-medium tabular-nums"
            :class="String(transaction.sens).toLowerCase() === 'credit' ? 'text-primary' : ''"
          >{{ signedAmount(transaction) }}</span>
        </div>
      </div>
      <details
        v-if="detail.transactions.length > 5"
        class="mt-3"
      >
        <summary class="text-muted-foreground hover:text-foreground cursor-pointer text-xs">
          Explore full history ({{ detail.transactions.length }})
        </summary>
        <div class="mt-3 max-h-80 overflow-auto rounded-lg border">
          <table class="w-full text-left text-xs">
            <thead class="bg-muted sticky top-0">
              <tr>
                <th class="p-3">
                  Date
                </th><th class="p-3">
                  Description / reference
                </th><th class="p-3 text-right">
                  Amount
                </th>
              </tr>
            </thead><tbody class="divide-y">
              <tr
                v-for="transaction in [...detail.transactions].sort((a, b) => String(b.date).localeCompare(String(a.date)))"
                :key="String(transaction.transaction_id)"
              >
                <td class="p-3 whitespace-nowrap">
                  {{ date(transaction.date) }}
                </td><td class="p-3">
                  {{ counterpartyName(transaction.contrepartie) }} · {{ transactionCategory(transaction.categorie) }}<span class="text-muted-foreground mt-1 block">{{ transaction.transaction_id }}</span>
                </td><td class="p-3 text-right whitespace-nowrap tabular-nums">
                  {{ signedAmount(transaction) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </details>
    </div>
  </div>
</template>
