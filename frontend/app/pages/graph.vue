<script setup lang="ts">
import { IconAlertTriangle, IconArrowRight, IconLink, IconRefresh, IconSparkles, IconX } from '@tabler/icons-vue'
import ClientGraph from '@/components/ClientGraph.vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { ProfileId } from '@/types/api'
import { profileColor } from '@/lib/profileColor'
import { trackersFor } from '@/lib/trackers'

definePageMeta({ title: 'Graph' })

const clients = await useClients()
const dash = await useDashboard()
const jev = await useJev()
const profiles = await useProfiles()

const layout = ref<'sorted' | 'network'>('sorted')
const filter = ref<ProfileId[]>([])
const selectedId = ref<string>()

const scored = computed(() => clients.value.map(c => ({ c, t: trackersFor(c, jev.data.value?.clients[c.id]) })))
const jevCount = computed(() => scored.value.filter(s => s.t.source === 'jev').length)
const segments = computed(() => {
  const counts = new Map<ProfileId, number>()
  for (const { t } of scored.value) counts.set(t.main, (counts.get(t.main) ?? 0) + 1)
  return [...counts.entries()].sort((a, b) => b[1] - a[1])
})

const toggle = (p: ProfileId) => {
  filter.value = filter.value.includes(p) ? filter.value.filter(x => x !== p) : [...filter.value, p]
}

const selected = computed(() => scored.value.find(s => s.c.id === selectedId.value))
const links = computed(() => {
  const id = selectedId.value
  return (dash.value?.links ?? [])
    .filter(([a, b]) => a === id || b === id)
    .map(([a, b, reason]) => ({ client: clients.value.find(c => c.id === (a === id ? b : a))!, reason }))
    .filter(l => l.client)
})

const ordinal = (n: number) => `${n}${n % 100 >= 11 && n % 100 <= 13 ? 'th' : ({ 1: 'st', 2: 'nd', 3: 'rd' } as Record<number, string>)[n % 10] ?? 'th'}`
const pct = (v: number) => `${Math.round(v * 100)}%`
const ago = computed(() => {
  const at = jev.data.value?.analyzedAt
  if (!at) return null
  const min = Math.round((Date.now() - new Date(at).getTime()) / 60000)
  return min < 1 ? 'just now' : min < 60 ? `${min} min ago` : new Date(at).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' })
})
</script>

<template>
  <div class="flex flex-col gap-4 px-4 lg:px-6">
    <!-- Header -->
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div class="grid gap-1">
        <h1 class="text-xl font-semibold tracking-tight">
          Client graph
        </h1>
        <p class="text-muted-foreground text-sm">
          Live map of every client pulled towards its strongest profile. The ring shows how sure the tracker is; hover to trace connections.
        </p>
      </div>
      <div class="flex items-center gap-2">
        <Badge
          variant="outline"
          class="gap-1.5 font-normal"
        >
          <span
            class="size-1.5 rounded-full"
            :class="jevCount ? 'bg-primary' : 'bg-muted-foreground'"
          />
          <template v-if="jevCount">
            Jev · {{ jevCount }}/{{ clients.length }} scored · {{ ago }}
          </template>
          <template v-else>
            Rule-based trackers
          </template>
        </Badge>
        <Button
          size="sm"
          :disabled="jev.running.value"
          @click="jev.run()"
        >
          <IconRefresh
            v-if="jev.running.value"
            class="animate-spin"
          />
          <IconSparkles v-else />
          {{ jev.running.value ? 'Scoring…' : jevCount ? 'Re-run Jev' : 'Score with Jev' }}
        </Button>
      </div>
    </div>
    <p
      v-if="jev.error.value"
      class="text-destructive text-sm"
    >
      {{ jev.error.value }}
    </p>

    <!-- Toolbar -->
    <div class="flex flex-wrap items-center gap-3">
      <Tabs v-model="layout">
        <TabsList>
          <TabsTrigger value="sorted">
            By profile
          </TabsTrigger>
          <TabsTrigger value="network">
            Network
          </TabsTrigger>
        </TabsList>
      </Tabs>
      <Separator
        orientation="vertical"
        class="!h-6"
      />
      <div class="flex flex-wrap items-center gap-1.5">
        <button
          v-for="[p, n] in segments"
          :key="p"
          class="hover:bg-accent flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs transition-colors"
          :class="filter.length && !filter.includes(p) ? 'opacity-40' : filter.includes(p) ? 'bg-accent' : ''"
          @click="toggle(p)"
        >
          <span
            class="size-2 rounded-full"
            :style="{ background: profileColor(p) }"
          />
          {{ profiles[p].label }}
          <span class="text-muted-foreground tabular-nums">{{ n }}</span>
        </button>
        <Button
          v-if="filter.length"
          variant="ghost"
          size="sm"
          class="h-7 text-xs"
          @click="filter = []"
        >
          Clear
        </Button>
      </div>
    </div>

    <!-- Graph + details -->
    <div class="grid gap-4 lg:grid-cols-[1fr_320px]">
      <Card class="overflow-hidden py-0">
        <ClientGraph
          v-model:selected="selectedId"
          :layout="layout"
          :filter="filter"
          :height="600"
          @toggle-profile="toggle"
        />
        <div class="text-muted-foreground flex flex-wrap gap-x-5 gap-y-1 border-t px-4 py-2.5 text-xs">
          <span class="flex items-center gap-1.5"><span class="bg-primary h-0.5 w-4 rounded" /> Linked (household, shared payments)</span>
          <template v-if="layout === 'sorted'">
            <span class="flex items-center gap-1.5"><span class="bg-muted-foreground size-3 rounded-full" /> Profile hub (closer = more confident)</span>
            <span class="flex items-center gap-1.5"><span class="border-muted-foreground w-4 border-t-2 border-dashed" /> Also tracked ≥ 50%</span>
          </template>
          <span
            v-else
            class="flex items-center gap-1.5"
          ><span class="bg-muted-foreground h-px w-4" /> Similar clients</span>
          <span class="flex items-center gap-1.5"><span class="border-destructive size-3 rounded-full border-2" /> Habit alert</span>
        </div>
      </Card>

      <Card class="gap-4">
        <template v-if="selected">
          <CardHeader class="flex items-start justify-between gap-2">
            <div class="grid gap-1">
              <CardTitle>{{ selected.c.name }}</CardTitle>
              <CardDescription>
                {{ selected.c.age }} years · payday on the {{ ordinal(selected.c.payday) }}
              </CardDescription>
            </div>
            <Button
              variant="ghost"
              size="icon"
              class="size-7"
              @click="selectedId = undefined"
            >
              <IconX />
            </Button>
          </CardHeader>
          <CardContent class="flex flex-col gap-5">
            <section class="grid gap-2.5">
              <div class="flex items-center justify-between">
                <h3 class="text-sm font-medium">
                  Trackers
                </h3>
                <Badge
                  variant="secondary"
                  class="font-normal"
                >
                  {{ selected.t.source === 'jev' ? 'Jev' : 'Rules' }}
                </Badge>
              </div>
              <div
                v-for="tr in selected.t.trackers.slice(0, 6)"
                :key="tr.id"
                class="grid gap-1"
              >
                <div class="flex justify-between text-xs">
                  <span :class="tr.id === selected.t.main ? 'font-medium' : 'text-muted-foreground'">{{ profiles[tr.id].label }}</span>
                  <span class="text-muted-foreground tabular-nums">{{ pct(tr.confidence) }}</span>
                </div>
                <div class="bg-muted h-1.5 overflow-hidden rounded-full">
                  <div
                    class="h-full rounded-full"
                    :style="{ width: pct(tr.confidence), background: profileColor(tr.id) }"
                  />
                </div>
              </div>
              <p
                v-if="selected.t.incomeRegularity !== null"
                class="text-muted-foreground text-xs"
              >
                Income regularity: {{ pct(selected.t.incomeRegularity) }}
              </p>
            </section>

            <section
              v-if="selected.c.change"
              class="flex gap-2 rounded-lg border p-3 text-sm"
              :class="selected.c.change.severity !== 'info' ? 'border-destructive/40' : ''"
            >
              <IconAlertTriangle
                class="mt-0.5 size-4 shrink-0"
                :class="selected.c.change.severity !== 'info' ? 'text-destructive' : 'text-primary'"
              />
              <div class="grid gap-0.5">
                <span class="font-medium">{{ selected.c.change.habit }} {{ selected.c.change.delta > 0 ? '+' : '' }}{{ selected.c.change.delta }}%</span>
                <span class="text-muted-foreground text-xs">{{ selected.c.change.text }}</span>
              </div>
            </section>

            <section
              v-if="links.length"
              class="grid gap-2"
            >
              <h3 class="text-sm font-medium">
                Linked clients
              </h3>
              <button
                v-for="l in links"
                :key="l.client.id"
                class="hover:bg-accent flex items-start gap-2 rounded-md p-1.5 text-left text-sm"
                @click="selectedId = l.client.id"
              >
                <IconLink class="text-primary mt-0.5 size-4 shrink-0" />
                <span class="grid">
                  <span>{{ l.client.name }}</span>
                  <span class="text-muted-foreground text-xs">{{ l.reason }}</span>
                </span>
              </button>
            </section>

            <section class="grid gap-1.5">
              <h3 class="text-sm font-medium">
                Why
              </h3>
              <p
                v-for="s in selected.c.signals.slice(0, 3)"
                :key="s.text"
                class="text-muted-foreground text-xs"
              >
                · {{ s.text }}
              </p>
            </section>

            <Button
              as-child
              variant="outline"
              size="sm"
            >
              <NuxtLink :to="`/client/${selected.c.id}`">
                Open full profile <IconArrowRight />
              </NuxtLink>
            </Button>
          </CardContent>
        </template>

        <template v-else>
          <CardHeader>
            <CardTitle>Select a client</CardTitle>
            <CardDescription>Click a node to see its trackers, habit changes and links.</CardDescription>
          </CardHeader>
          <CardContent class="flex flex-col gap-2">
            <div
              v-for="[p, n] in segments"
              :key="p"
              class="flex items-center justify-between text-sm"
            >
              <span class="flex items-center gap-2">
                <span
                  class="size-2.5 rounded-sm"
                  :style="{ background: profileColor(p) }"
                />
                {{ profiles[p].label }}
              </span>
              <span class="text-muted-foreground tabular-nums">{{ n }}</span>
            </div>
          </CardContent>
        </template>
      </Card>
    </div>
  </div>
</template>
