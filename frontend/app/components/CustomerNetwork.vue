<script setup lang="ts">
import type { CustomerNetworkData } from '@/lib/dashboard'
import { IconArrowRight, IconChevronLeft, IconChevronRight, IconClick, IconNetwork, IconX } from '@tabler/icons-vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardAction, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { number } from '@/lib/api'

const props = defineProps<{ network: CustomerNetworkData }>()
const page = ref(0)
const selectedId = ref('')
const hoveredId = ref('')
const pageSize = 12
const clients = computed(() => props.network.nodes.filter(node => node.kind === 'client'))
const visibleClients = computed(() => clients.value.slice(page.value * pageSize, (page.value + 1) * pageSize))
const visibleIds = computed(() => new Set(visibleClients.value.map(node => node.id)))
const links = computed(() => props.network.links.filter(link => visibleIds.value.has(link.source) || visibleIds.value.has(link.target)))
const linkedIds = computed(() => new Set(links.value.flatMap(link => [link.source, link.target])))
const visibleCounts = computed(() => {
  const counts = new Map<string, number>()
  for (const link of links.value) {
    const id = link.kind === 'segment' ? link.source : link.target
    counts.set(id, (counts.get(id) ?? 0) + 1)
  }
  return counts
})
const segments = computed(() => props.network.nodes.filter(node => node.kind === 'segment' && linkedIds.value.has(node.id)))
const products = computed(() => props.network.nodes.filter(node => node.kind === 'product' && linkedIds.value.has(node.id)))
const allVisible = computed(() => [...segments.value, ...visibleClients.value, ...products.value])
const height = computed(() => Math.max(320, Math.max(segments.value.length, visibleClients.value.length, products.value.length) * 47 + 80))
const selected = computed(() => allVisible.value.find(node => node.id === selectedId.value))
const focusId = computed(() => hoveredId.value || selectedId.value)
const focusedIds = computed(() => {
  if (!focusId.value)
    return new Set<string>()
  const ids = new Set([focusId.value])
  const focus = allVisible.value.find(node => node.id === focusId.value)
  for (const link of links.value) {
    if (link.source === focusId.value || link.target === focusId.value) {
      ids.add(link.source)
      ids.add(link.target)
    }
  }
  if (focus?.kind !== 'client') {
    const customerIds = new Set(visibleClients.value.filter(node => ids.has(node.id)).map(node => node.id))
    for (const link of links.value) {
      if (customerIds.has(link.source) || customerIds.has(link.target)) {
        ids.add(link.source)
        ids.add(link.target)
      }
    }
  }
  return ids
})
const selectedConnections = computed(() => {
  if (!selected.value)
    return []
  const ids = new Set<string>()
  for (const link of links.value) {
    if (link.source === selected.value.id)
      ids.add(link.target)
    if (link.target === selected.value.id)
      ids.add(link.source)
  }
  return allVisible.value.filter(node => ids.has(node.id))
})
const positions = computed(() => {
  const result = new Map<string, { x: number, y: number }>()
  for (const [column, nodes] of [segments.value, visibleClients.value, products.value].entries()) {
    nodes.forEach((node, index) => {
      result.set(node.id, { x: [138, 470, 802][column]!, y: 66 + (height.value - 103) * (index + 0.5) / Math.max(nodes.length, 1) })
    })
  }
  return result
})
const nodeColor = (kind: string) => kind === 'product' ? 'var(--chart-3)' : kind === 'segment' ? 'var(--primary)' : 'var(--muted-foreground)'
const clipped = (label: string, max = 24) => label.length > max ? `${label.slice(0, max - 1)}…` : label
function linePath(source: string, target: string) {
  const start = positions.value.get(source)
  const end = positions.value.get(target)
  if (!start || !end)
    return ''
  const x1 = start.x + 116
  const x2 = end.x - 116
  const mid = (x1 + x2) / 2
  return `M ${x1} ${start.y} C ${mid} ${start.y}, ${mid} ${end.y}, ${x2} ${end.y}`
}
function select(id: string) {
  selectedId.value = selectedId.value === id ? '' : id
}
function changePage(direction: number) {
  page.value += direction
  selectedId.value = ''
  hoveredId.value = ''
}
watch(() => props.network, () => {
  page.value = 0
  selectedId.value = ''
  hoveredId.value = ''
})
</script>

<template>
  <Card class="gap-0 overflow-hidden">
    <CardHeader class="gap-2 pb-4">
      <CardTitle class="flex items-center gap-2">
        <IconNetwork class="text-primary size-4" /> Customer connections
      </CardTitle>
      <CardDescription>Explore how observed habits connect customers to their selected adverts.</CardDescription>
      <CardAction>
        <Badge variant="outline">
          Interactive
        </Badge>
      </CardAction>
    </CardHeader>
    <CardContent class="px-0">
      <div
        v-if="!clients.length"
        class="text-muted-foreground flex min-h-60 flex-col items-center justify-center gap-3 px-6 text-center text-sm"
      >
        <IconNetwork class="size-8 opacity-50" />
        No customers match these filters. Clear a filter to explore their connections.
      </div>
      <template v-else>
        <div class="border-y bg-muted/15 px-4 py-2.5">
          <p class="text-muted-foreground flex items-center gap-2 text-xs">
            <IconClick class="size-4 shrink-0" /> Click a node to highlight its connections. Open a customer to inspect the evidence.
          </p>
        </div>
        <div
          class="overflow-x-auto px-2"
          tabindex="0"
          aria-label="Customer connection graph. Scroll horizontally on small screens."
        >
          <svg
            :viewBox="`0 0 940 ${height}`"
            class="w-full min-w-[780px]"
            role="group"
            aria-label="Observed segments, customers and selected advertisements"
          >
            <text
              x="22"
              y="31"
              class="fill-muted-foreground text-[12px] font-medium"
            >OBSERVED HABITS</text>
            <text
              x="354"
              y="31"
              class="fill-muted-foreground text-[12px] font-medium"
            >CUSTOMERS</text>
            <text
              x="686"
              y="31"
              class="fill-muted-foreground text-[12px] font-medium"
            >SELECTED ADVERTS</text>
            <line
              x1="22"
              x2="918"
              y1="46"
              y2="46"
              stroke="var(--border)"
            />
            <path
              v-for="link in links"
              :key="`${link.source}-${link.target}`"
              :d="linePath(link.source, link.target)"
              fill="none"
              :stroke="link.kind === 'recommendation' ? 'var(--chart-3)' : 'var(--primary)'"
              :stroke-width="focusId && focusedIds.has(link.source) && focusedIds.has(link.target) ? 2 : 1.2"
              :opacity="focusId ? (focusedIds.has(link.source) && focusedIds.has(link.target) ? 0.8 : 0.06) : 0.25"
              class="transition-opacity"
            />
            <g
              v-for="node in allVisible"
              :key="node.id"
              :transform="`translate(${positions.get(node.id)?.x ?? 0},${positions.get(node.id)?.y ?? 0})`"
              role="button"
              tabindex="0"
              :aria-label="`${node.label}: ${node.kind}. Highlight connections.`"
              :aria-pressed="selectedId === node.id"
              :opacity="focusId && !focusedIds.has(node.id) ? 0.3 : 1"
              class="cursor-pointer outline-none transition-opacity"
              @click="select(node.id)"
              @keydown.enter.prevent="select(node.id)"
              @keydown.space.prevent="select(node.id)"
              @focus="hoveredId = node.id"
              @blur="hoveredId = ''"
              @mouseenter="hoveredId = node.id"
              @mouseleave="hoveredId = ''"
            >
              <title>{{ node.label }}</title>
              <rect
                x="-116"
                y="-17"
                width="232"
                height="34"
                rx="8"
                fill="var(--card)"
                :stroke="selectedId === node.id || hoveredId === node.id ? nodeColor(node.kind) : 'var(--border)'"
                :stroke-width="selectedId === node.id ? 2 : 1"
              />
              <circle
                cx="-100"
                cy="0"
                r="3.5"
                :fill="nodeColor(node.kind)"
              />
              <text
                x="-88"
                y="4"
                class="fill-foreground text-[12px]"
                :class="node.kind !== 'client' ? 'font-medium' : ''"
              >
                {{ clipped(node.label, node.kind === 'client' ? 26 : 24) }}
              </text>
              <text
                v-if="node.count !== undefined && node.kind !== 'client'"
                x="103"
                y="4"
                text-anchor="end"
                class="fill-muted-foreground text-[11px]"
              >
                {{ number(visibleCounts.get(node.id) ?? 0) }}
              </text>
            </g>
            <text
              v-if="!products.length"
              x="802"
              :y="height / 2 - 2"
              text-anchor="middle"
              class="fill-muted-foreground text-[12px]"
            >No selected adverts</text>
            <text
              v-if="!products.length"
              x="802"
              :y="height / 2 + 18"
              text-anchor="middle"
              class="fill-muted-foreground text-[11px]"
            >for these customers yet</text>
          </svg>
        </div>
        <div
          v-if="selected"
          class="border-t bg-muted/20 flex flex-wrap items-center justify-between gap-3 px-4 py-3"
          aria-live="polite"
        >
          <div class="min-w-0 flex-1">
            <p class="text-sm font-medium">
              {{ selected.label }}
            </p>
            <p class="text-muted-foreground mt-1 text-xs leading-relaxed">
              {{ selectedConnections.length ? selectedConnections.map(node => node.label).join(' · ') : 'No habit or advert connection in this view.' }}
            </p>
          </div>
          <Button
            v-if="selected.client_id"
            variant="outline"
            size="sm"
            as-child
          >
            <NuxtLink :to="`/client/${encodeURIComponent(selected.client_id)}`">
              View customer <IconArrowRight class="size-3.5" />
            </NuxtLink>
          </Button>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Clear graph selection"
            @click="selectedId = ''"
          >
            <IconX class="size-4" />
          </Button>
        </div>
      </template>
    </CardContent>
    <CardFooter class="flex flex-wrap items-center justify-between gap-3 border-t py-3">
      <p class="text-muted-foreground text-xs">
        {{ number(visibleClients.length) }} visible · {{ number(network.shown_clients) }} sampled of {{ number(network.total_clients) }} matching customers.
        <span class="block">The table and totals cover the full filtered population.</span>
      </p>
      <div
        v-if="clients.length > pageSize"
        class="flex items-center gap-2"
      >
        <Button
          variant="outline"
          size="icon"
          class="size-8"
          :disabled="page === 0"
          aria-label="Previous graph customers"
          @click="changePage(-1)"
        >
          <IconChevronLeft class="size-4" />
        </Button>
        <span class="text-muted-foreground text-xs tabular-nums">{{ page + 1 }} / {{ Math.ceil(clients.length / pageSize) }}</span>
        <Button
          variant="outline"
          size="icon"
          class="size-8"
          :disabled="(page + 1) * pageSize >= clients.length"
          aria-label="Next graph customers"
          @click="changePage(1)"
        >
          <IconChevronRight class="size-4" />
        </Button>
      </div>
    </CardFooter>
  </Card>
</template>
