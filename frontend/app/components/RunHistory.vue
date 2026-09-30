<script setup lang="ts">
import { IconChevronLeft, IconChevronRight, IconHistory, IconLoader2, IconRefresh } from '@tabler/icons-vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardAction, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { analysisHistorySchema, benchmarkHistorySchema, dollars, duration, errorMessage, number, statusLabels } from '@/lib/api'

const props = defineProps<{
  clientId?: string
  kind: 'analysis' | 'benchmark'
  refreshKey?: number
}>()
const emit = defineEmits<{ select: [id: string] }>()
type HistoryRow = { id: string, label: string, status: string, createdAt: string, durationMs: number, cost: number }
const rows = ref<HistoryRow[]>([])
const total = ref(0)
const offset = ref(0)
const loading = ref(true)
const error = ref('')
const limit = 10
const title = computed(() => props.kind === 'analysis' ? 'Analysis history' : 'Benchmark history')
const description = computed(() => props.kind === 'analysis' && props.clientId ? 'Revisit saved results for this client.' : 'Revisit saved runs and compare their results.')
let requestNumber = 0
let mounted = false

function dateLabel(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('en-BE', { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

async function load() {
  const request = ++requestNumber
  loading.value = true
  error.value = ''
  try {
    const query = { limit, offset: offset.value, ...(props.kind === 'analysis' && props.clientId ? { client_id: props.clientId } : {}) }
    const response = await $fetch(props.kind === 'analysis' ? '/api/analyses' : '/api/benchmarks', { query })
    if (request !== requestNumber)
      return
    if (props.kind === 'analysis') {
      const history = analysisHistorySchema.parse(response)
      total.value = history.total
      rows.value = history.items.map(item => ({ id: item.id, label: item.client_id, status: statusLabels[item.status], createdAt: item.created_at, durationMs: item.duration_ms, cost: item.estimated_cost_usd }))
    } else {
      const history = benchmarkHistorySchema.parse(response)
      total.value = history.total
      rows.value = history.items.map(item => ({ id: item.id, label: `${number(item.completed_count)} / ${number(item.requested_count)} clients`, status: item.status.charAt(0).toUpperCase() + item.status.slice(1), createdAt: item.created_at, durationMs: item.elapsed_ms, cost: item.metrics.estimated_cost_usd }))
    }
  } catch (cause) {
    if (request === requestNumber)
      error.value = errorMessage(cause)
  } finally {
    if (request === requestNumber)
      loading.value = false
  }
}

function changePage(direction: number) {
  offset.value = Math.max(0, offset.value + direction * limit)
  void load()
}

watch(() => [props.clientId, props.kind, props.refreshKey], () => {
  offset.value = 0
  rows.value = []
  total.value = 0
  if (mounted)
    void load()
})
onMounted(() => {
  mounted = true
  void load()
})
onBeforeUnmount(() => {
  mounted = false
  ++requestNumber
})
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        <IconHistory class="size-4" />
        {{ title }}
      </CardTitle>
      <CardDescription>{{ description }}</CardDescription>
      <CardAction>
        <Button
          variant="ghost"
          size="icon"
          :disabled="loading"
          :aria-label="`Refresh ${title.toLowerCase()}`"
          @click="load"
        >
          <IconRefresh :class="loading ? 'animate-spin' : ''" />
        </Button>
      </CardAction>
    </CardHeader>
    <CardContent>
      <div
        v-if="loading"
        role="status"
        class="text-muted-foreground flex items-center gap-2 py-4 text-sm"
      >
        <IconLoader2 class="size-4 animate-spin" />
        Loading saved runs…
      </div>
      <div
        v-else-if="error"
        role="alert"
        class="text-destructive flex flex-wrap items-center justify-between gap-3 text-sm"
      >
        {{ error }}
        <Button
          variant="outline"
          size="sm"
          @click="load"
        >
          Try again
        </Button>
      </div>
      <p
        v-else-if="!rows.length"
        class="text-muted-foreground py-4 text-sm"
      >
        {{ kind === 'analysis' ? 'No saved individual analyses yet. Run an analysis to save the first result.' : 'No saved benchmarks yet. Start a benchmark to save the first result.' }}
      </p>
      <ul
        v-else
        class="divide-y"
      >
        <li
          v-for="row in rows"
          :key="row.id"
          class="flex flex-wrap items-center justify-between gap-3 py-3 first:pt-0 last:pb-0"
        >
          <div class="grid min-w-0 gap-1.5">
            <div class="flex flex-wrap items-center gap-2">
              <span class="text-sm font-medium">{{ row.label }}</span>
              <Badge variant="outline">
                {{ row.status }}
              </Badge>
            </div>
            <p class="text-muted-foreground text-xs">
              <time :datetime="row.createdAt">{{ dateLabel(row.createdAt) }}</time>
              <span
                class="mx-1.5"
                aria-hidden="true"
              >·</span>
              {{ duration(row.durationMs) }}
              <span
                class="mx-1.5"
                aria-hidden="true"
              >·</span>
              {{ dollars(row.cost) }} estimated
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            @click="emit('select', row.id)"
          >
            View result
          </Button>
        </li>
      </ul>
    </CardContent>
    <CardFooter
      v-if="total > limit"
      class="justify-between gap-3 border-t pt-4"
    >
      <p class="text-muted-foreground text-xs">
        {{ number(offset + 1) }}–{{ number(Math.min(offset + limit, total)) }} of {{ number(total) }} runs
      </p>
      <div class="flex gap-1">
        <Button
          variant="outline"
          size="icon"
          aria-label="Previous history page"
          :disabled="loading || offset === 0"
          @click="changePage(-1)"
        >
          <IconChevronLeft />
        </Button>
        <Button
          variant="outline"
          size="icon"
          aria-label="Next history page"
          :disabled="loading || offset + limit >= total"
          @click="changePage(1)"
        >
          <IconChevronRight />
        </Button>
      </div>
    </CardFooter>
  </Card>
</template>
