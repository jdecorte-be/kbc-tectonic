<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import type { Client } from '@/types/api'

const props = defineProps<{ client: Client | null }>()
const open = defineModel<boolean>('open', { default: false })
const profiles = await useProfiles()

const eur = (n: number) => `${n < 0 ? '-' : n > 0 ? '+' : ''}€${Math.abs(n).toLocaleString('en-BE', { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`
const maxSpend = computed(() => Math.max(...(props.client?.monthlySpend ?? [1])))
const months = computed(() => props.client?.spendMonths ?? [])
</script>

<template>
  <Sheet v-model:open="open">
    <SheetContent class="w-full gap-0 overflow-y-auto sm:max-w-md">
      <template v-if="client">
        <SheetHeader>
          <SheetTitle>{{ client.name }}</SheetTitle>
          <SheetDescription>
            {{ client.age }} years · payday on the {{ client.payday }}th ·
            <NuxtLink
              :to="`/client/${client.id}`"
              class="text-primary underline"
            >Open full profile</NuxtLink>
          </SheetDescription>
        </SheetHeader>

        <div class="flex flex-col gap-5 p-4 pt-0">
          <section class="grid gap-2">
            <h3 class="text-sm font-medium">
              Profiles
            </h3>
            <div
              v-for="p in client.profiles"
              :key="p.id"
              class="grid gap-1"
            >
              <div class="flex justify-between text-sm">
                <span>{{ profiles[p.id].label }}</span>
                <span class="text-muted-foreground tabular-nums">{{ p.confidence }}%</span>
              </div>
              <div class="bg-muted h-2 overflow-hidden rounded-full">
                <div
                  class="bg-primary h-full rounded-full"
                  :style="{ width: `${p.confidence}%` }"
                />
              </div>
            </div>
          </section>

          <section class="grid gap-2">
            <h3 class="text-sm font-medium">
              Why this profile
            </h3>
            <ul class="grid gap-1.5 text-sm">
              <li
                v-for="s in client.signals"
                :key="s.text"
                class="flex items-start justify-between gap-3"
              >
                <span>{{ s.text }}</span>
                <Badge
                  variant="outline"
                  class="tabular-nums"
                >
                  {{ Math.round(s.weight * 100) }}%
                </Badge>
              </li>
            </ul>
          </section>

          <Separator />

          <section class="grid gap-2">
            <h3 class="text-sm font-medium">
              Habits
            </h3>
            <div class="grid grid-cols-2 gap-2 text-sm">
              <div class="rounded-md border p-2">
                <div class="text-muted-foreground text-xs">
                  Top habit
                </div>{{ client.topHabit }}
              </div>
              <div class="rounded-md border p-2">
                <div class="text-muted-foreground text-xs">
                  Savings rate
                </div>{{ client.savingsRate }}%
              </div>
              <div class="rounded-md border p-2">
                <div class="text-muted-foreground text-xs">
                  Recurring payments
                </div>{{ client.recurringCount }}
              </div>
              <div class="rounded-md border p-2">
                <div class="text-muted-foreground text-xs">
                  Cash share
                </div>{{ client.cashShare }}%
              </div>
            </div>
            <div class="mt-1 flex h-16 items-end gap-2">
              <div
                v-for="(v, i) in client.monthlySpend"
                :key="i"
                class="flex flex-1 flex-col items-center gap-1"
              >
                <div
                  class="bg-primary/70 w-full rounded-t"
                  :style="{ height: `${(v / maxSpend) * 44}px` }"
                  :title="`€${v}`"
                />
                <span class="text-muted-foreground text-[10px]">{{ months[i] }}</span>
              </div>
            </div>
            <p
              v-if="client.change"
              class="text-sm"
            >
              <Badge :variant="client.change.severity === 'alert' ? 'destructive' : 'secondary'">
                Change
              </Badge>
              {{ client.change.text }}
            </p>
          </section>

          <Separator />

          <section class="grid gap-2">
            <h3 class="text-sm font-medium">
              Recent transactions
            </h3>
            <ul class="grid gap-1.5 text-sm">
              <li
                v-for="t in client.transactions"
                :key="t.date + t.merchant"
                class="flex justify-between gap-3"
              >
                <span>
                  {{ t.merchant }}
                  <span class="text-muted-foreground text-xs">· {{ t.category }} · {{ t.date }}</span>
                </span>
                <span
                  class="tabular-nums"
                  :class="t.amount > 0 && 'text-primary'"
                >{{ eur(t.amount) }}</span>
              </li>
            </ul>
          </section>

          <section class="bg-primary/10 grid gap-1 rounded-md p-3 text-sm">
            <span class="text-muted-foreground text-xs">Suggested action</span>
            <span class="font-medium">{{ profiles[client.profiles[0]!.id].offer }}</span>
          </section>
        </div>
      </template>
    </SheetContent>
  </Sheet>
</template>
