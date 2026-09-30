<script setup lang="ts">
import { IconArrowRight, IconBolt, IconClock, IconCurrencyDollar, IconDownload, IconLoader2, IconPlayerPlay, IconPlayerStop, IconUsers } from '@tabler/icons-vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardAction, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableEmpty, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet'
import { dollars, duration, errorMessage, number, statusLabels, type Analysis, type Benchmark } from '@/lib/api'

definePageMeta({ title: 'Scalability benchmark' })
const api = useKbcApi()
const count = ref(10)
const concurrency = ref(5)
const job = useState<Benchmark | null>('benchmark-job', () => null)
const starting = ref(false)
const cancelling = ref(false)
const savedLoading = ref(false)
const historyError = ref('')
const historyRefresh = ref(0)
const error = ref('')
const selectedResult = ref<Analysis | null>(null)
const sheetOpen = ref(false)
const filter = ref('all')
const page = ref(0)
const health = ref<Awaited<ReturnType<typeof api.health>> | null>(null)
let pollTimer: ReturnType<typeof setTimeout> | undefined
let mounted = false
let jobRequest = 0
const running = computed(() => job.value?.status === 'running')
const progress = computed(() => job.value ? Math.min(100, job.value.completed_count / job.value.requested_count * 100) : 0)
const filteredResults = computed(() => (job.value?.results ?? []).filter(result => filter.value === 'all' || (filter.value === 'abstained' ? ['insufficient_information', 'no_match'].includes(result.status) : result.status === filter.value)))
const visibleResults = computed(() => filteredResults.value.slice(page.value * 20, (page.value + 1) * 20))
const outcomes = computed(() => job.value
  ? [
      { label: 'With offers', value: job.value.metrics.recommended_count, class: 'bg-primary', text: 'text-primary' },
      { label: 'Abstained', value: job.value.metrics.abstained_count, class: 'bg-chart-3', text: 'text-chart-3' },
      { label: 'Opted out', value: job.value.metrics.opt_out_count, class: 'bg-muted-foreground', text: 'text-muted-foreground' },
      { label: 'Errors', value: job.value.metrics.error_count, class: 'bg-destructive', text: 'text-destructive' }
    ]
  : [])
watch(filter, () => {
  page.value = 0
})
watch(() => [job.value?.id, job.value?.status], ([id, status], [previousId, previousStatus]) => {
  if (id && status !== 'running' && (id !== previousId || status !== previousStatus))
    ++historyRefresh.value
})
function schedulePoll() {
  clearTimeout(pollTimer)
  if (mounted && running.value)
    pollTimer = setTimeout(poll, 1500)
}
async function poll() {
  if (!job.value)
    return
  const id = job.value.id
  const request = ++jobRequest
  try {
    const result = await api.benchmark(id)
    if (request === jobRequest && mounted && job.value?.id === id) {
      job.value = result
      error.value = ''
    }
  } catch (cause) {
    if (request === jobRequest && mounted)
      error.value = `Could not refresh the run: ${errorMessage(cause)}`
  } finally {
    if (request === jobRequest)
      schedulePoll()
  }
}
async function start() {
  if (starting.value || running.value || savedLoading.value)
    return
  const request = ++jobRequest
  starting.value = true
  error.value = ''
  historyError.value = ''
  selectedResult.value = null
  page.value = 0
  filter.value = 'all'
  try {
    const result = await api.startBenchmark(count.value, concurrency.value)
    if (request !== jobRequest || !mounted)
      return
    job.value = result
    ++historyRefresh.value
    localStorage.setItem('kbc-benchmark-id', job.value.id)
    schedulePoll()
  } catch (cause) {
    if (request === jobRequest && mounted)
      error.value = errorMessage(cause)
  } finally {
    if (request === jobRequest)
      starting.value = false
  }
}
async function cancel() {
  if (!job.value || cancelling.value)
    return
  clearTimeout(pollTimer)
  const request = ++jobRequest
  cancelling.value = true
  try {
    const result = await api.cancelBenchmark(job.value.id)
    if (request !== jobRequest || !mounted)
      return
    job.value = result
    schedulePoll()
  } catch (cause) {
    if (request === jobRequest && mounted)
      error.value = errorMessage(cause)
  } finally {
    if (request === jobRequest) {
      cancelling.value = false
      schedulePoll()
    }
  }
}
async function loadSavedBenchmark(id: string, restoring = false) {
  if (!restoring && (starting.value || cancelling.value || running.value)) {
    historyError.value = 'Finish or stop the current benchmark before opening a saved result.'
    return
  }
  clearTimeout(pollTimer)
  const request = ++jobRequest
  savedLoading.value = true
  historyError.value = ''
  try {
    const result = await api.benchmark(id)
    if (request !== jobRequest || !mounted)
      return
    job.value = result
    selectedResult.value = null
    sheetOpen.value = false
    page.value = 0
    filter.value = 'all'
    error.value = ''
    localStorage.setItem('kbc-benchmark-id', id)
    schedulePoll()
  } catch (cause) {
    if (request === jobRequest && mounted)
      historyError.value = `Could not load the saved benchmark: ${errorMessage(cause)}`
  } finally {
    if (request === jobRequest)
      savedLoading.value = false
  }
}
function inspect(result: Analysis) {
  selectedResult.value = result
  sheetOpen.value = true
}
function exportResults() {
  if (!job.value)
    return
  const url = URL.createObjectURL(new Blob([JSON.stringify(job.value, null, 2)], { type: 'application/json' }))
  const link = document.createElement('a')
  link.href = url
  link.download = `kbc-benchmark-${job.value.id}.json`
  link.click()
  URL.revokeObjectURL(url)
}
onMounted(async () => {
  mounted = true
  void api.health().then((value) => {
    health.value = value
  }).catch(() => { })
  const savedId = job.value?.id ?? localStorage.getItem('kbc-benchmark-id')
  if (savedId)
    await loadSavedBenchmark(savedId, true)
})
onBeforeUnmount(() => {
  mounted = false
  clearTimeout(pollTimer)
  ++jobRequest
})
</script>

<template>
  <div class="flex flex-col gap-4 md:gap-6">
    <Card>
      <CardHeader>
        <CardTitle>Run a benchmark</CardTitle>
        <CardDescription>Measure processing time, throughput and estimated cost across synthetic clients.</CardDescription>
        <CardAction>
          <Badge variant="outline">
            <IconBolt /> Live execution
          </Badge>
        </CardAction>
      </CardHeader>
      <CardContent class="grid gap-4 xl:grid-cols-[1fr_1fr_auto] xl:items-end">
        <fieldset
          :disabled="running || starting"
          class="min-w-0"
        >
          <legend class="text-muted-foreground mb-2 text-xs font-medium">
            Batch size
          </legend>
          <div class="grid grid-cols-3 gap-2">
            <Button
              v-for="size in [10, 100, 1000]"
              :key="size"
              :variant="count === size ? 'default' : 'outline'"
              :aria-pressed="count === size"
              :disabled="running || starting"
              class="tabular-nums"
              @click="count = size"
            >
              {{ number(size) }} clients
            </Button>
          </div>
        </fieldset>
        <div>
          <label
            for="concurrency"
            class="text-muted-foreground mb-2 flex items-center justify-between text-xs font-medium"
          >
            <span>Concurrent clients</span><span class="tabular-nums">{{ concurrency }} / 10</span>
          </label>
          <div class="flex h-9 items-center rounded-md border px-3">
            <input
              id="concurrency"
              v-model.number="concurrency"
              type="range"
              min="1"
              max="10"
              step="1"
              class="accent-primary w-full"
              :disabled="running || starting"
            >
          </div>
        </div>
        <Button
          :disabled="starting || running || savedLoading || health?.jev_configured === false"
          @click="start"
        >
          <IconLoader2
            v-if="starting"
            class="animate-spin"
          />
          <IconPlayerPlay v-else />
          {{ starting ? 'Starting…' : running ? 'Run in progress' : 'Start benchmark' }}
        </Button>
      </CardContent>
      <CardFooter class="text-muted-foreground text-xs">
        Every run calls Jev and, when needed, OpenAI with synthetic data. Estimates use configured provider pricing; rate limits apply.
        {{ health && !health.jev_configured ? 'Set JEV_API on the backend to run this benchmark.' : '' }}
      </CardFooter>
    </Card>
    <p
      v-if="error"
      role="alert"
      class="border-destructive/30 text-destructive rounded-xl border p-4 text-sm"
    >
      {{ error }}
    </p>
    <template v-if="job">
      <Card>
        <CardHeader class="flex flex-wrap items-center justify-between gap-3">
          <div class="grid gap-1">
            <CardTitle class="flex items-center gap-2">
              <IconLoader2
                v-if="running"
                class="text-primary size-4 animate-spin"
              />
              {{ job.status === 'running' ? 'Benchmark running' : job.status === 'completed' ? 'Benchmark complete' : job.status === 'cancelled' ? 'Benchmark stopped' : 'Benchmark failed' }}
            </CardTitle>
            <CardDescription>{{ number(job.completed_count) }} / {{ number(job.requested_count) }} clients processed · concurrency {{ job.concurrency }}</CardDescription>
          </div>
          <div class="flex items-center gap-3">
            <Badge
              variant="outline"
              class="tabular-nums"
            >
              {{ number(progress) }}%
            </Badge>
            <Button
              v-if="running"
              variant="outline"
              size="sm"
              :disabled="cancelling"
              @click="cancel"
            >
              <IconPlayerStop /> {{ cancelling ? 'Stopping…' : 'Stop run' }}
            </Button>
            <Button
              v-else
              variant="outline"
              size="sm"
              @click="exportResults"
            >
              <IconDownload /> Export JSON
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div
            class="bg-muted h-1.5 overflow-hidden rounded-full"
            role="progressbar"
            :aria-valuenow="job.completed_count"
            :aria-valuemin="0"
            :aria-valuemax="job.requested_count"
            aria-label="Clients processed"
          >
            <div
              class="bg-primary h-full rounded-full transition-all duration-500"
              :style="{ width: `${progress}%` }"
            />
          </div>
          <p
            v-if="job.error"
            class="text-destructive mt-3 text-sm"
          >
            {{ job.error }}
          </p>
          <p
            v-if="cancelling"
            class="text-muted-foreground mt-3 text-sm"
          >
            In-flight requests finish first so their usage is included.
          </p>
        </CardContent>
      </Card>

      <div class="*:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card dark:*:data-[slot=card]:bg-card grid gap-4 *:data-[slot=card]:bg-gradient-to-t *:data-[slot=card]:shadow-xs @xl/main:grid-cols-2 @5xl/main:grid-cols-4">
        <Card
          v-for="metric in [
            { label: 'Wall-clock duration', value: duration(job.elapsed_ms), badge: 'Measured', title: 'Time for the entire run', hint: 'Includes provider waiting time', icon: IconClock },
            { label: 'Client throughput', value: `${number(job.metrics.clients_per_second)} / s`, badge: 'Measured', title: 'Processed clients per second', hint: 'All decisions / elapsed time', icon: IconUsers },
            { label: 'Estimated total cost', value: dollars(job.metrics.estimated_cost_usd), badge: 'Estimate', title: 'Jev and OpenAI usage', hint: job.metrics.usage_source === 'provider' ? 'Provider-reported token usage' : 'Includes estimated token usage', icon: IconCurrencyDollar },
            { label: 'Cost per client', value: job.completed_count ? dollars(job.metrics.estimated_cost_usd / job.completed_count) : '—', badge: 'Estimate', title: 'Cost per processed client', hint: 'Includes abstentions and opt-outs', icon: IconBolt }
          ]"
          :key="metric.label"
          class="@container/card"
        >
          <CardHeader>
            <CardDescription>{{ metric.label }}</CardDescription>
            <CardTitle class="col-span-2 text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
              {{ metric.value }}
            </CardTitle>
            <CardAction class="row-span-1">
              <Badge variant="outline">
                <component :is="metric.icon" /> {{ metric.badge }}
              </Badge>
            </CardAction>
          </CardHeader>
          <CardFooter class="flex-col items-start gap-1.5 text-sm">
            <div class="font-medium">
              {{ metric.title }}
            </div>
            <div class="text-muted-foreground">
              {{ metric.hint }}
            </div>
          </CardFooter>
        </Card>
      </div>
      <div class="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Decision distribution</CardTitle>
            <CardDescription>Outcomes across all processed clients.</CardDescription>
          </CardHeader>
          <CardContent>
            <div class="bg-muted mb-4 flex h-2 overflow-hidden rounded-full">
              <div
                v-for="outcome in outcomes"
                :key="outcome.label"
                :class="outcome.class"
                :style="{ width: `${job.completed_count ? outcome.value / job.completed_count * 100 : 0}%` }"
              />
            </div>
            <div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div
                v-for="outcome in outcomes"
                :key="outcome.label"
              >
                <div
                  class="text-2xl font-semibold tabular-nums"
                  :class="outcome.text"
                >
                  {{ number(outcome.value) }}
                </div>
                <div class="text-muted-foreground text-xs">
                  {{ outcome.label }}
                </div>
              </div>
            </div>
          </CardContent>
          <CardFooter class="text-muted-foreground text-xs">
            Abstentions are valid decisions. Errors and personalization opt-outs are counted separately.
          </CardFooter>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Latency &amp; API usage</CardTitle>
            <CardDescription>Client latency and token consumption during this run.</CardDescription>
          </CardHeader>
          <CardContent class="grid grid-cols-3 gap-4">
            <div
              v-for="metric in [{ label: 'Median · p50', value: duration(job.metrics.p50_latency_ms) }, { label: 'Tail · p95', value: duration(job.metrics.p95_latency_ms) }, { label: 'Average', value: duration(job.metrics.average_latency_ms) }, { label: 'Provider calls', value: number(job.metrics.api_calls) }, { label: 'Input tokens', value: number(job.metrics.input_tokens) }, { label: 'Output tokens', value: number(job.metrics.output_tokens) }]"
              :key="metric.label"
            >
              <div class="text-muted-foreground text-xs">
                {{ metric.label }}
              </div>
              <div class="mt-1 text-lg font-medium tabular-nums">
                {{ metric.value }}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card v-if="job.category_registry_before && job.category_registry_after">
        <CardHeader class="flex flex-wrap items-center justify-between gap-3">
          <div class="grid gap-1">
            <CardTitle>Category learning</CardTitle>
            <CardDescription>{{ job.category_registry_before.count }} categories before · {{ job.category_registry_after.count }} now · {{ job.metrics.openai_calls }} OpenAI calls</CardDescription>
          </div>
          <Button
            as-child
            variant="outline"
            size="sm"
          >
            <NuxtLink to="/categories">View registry <IconArrowRight /></NuxtLink>
          </Button>
        </CardHeader>
        <CardContent>
          <div
            v-if="job.category_registry_after.labels.some(label => !job?.category_registry_before?.labels.includes(label))"
            class="flex flex-wrap gap-2"
          >
            <Badge
              v-for="label in job.category_registry_after.labels.filter(label => !job?.category_registry_before?.labels.includes(label))"
              :key="label"
              variant="outline"
            >
              New · {{ label }}
            </Badge>
          </div>
          <p
            v-else
            class="text-muted-foreground text-sm"
          >
            No new category has been saved during this run.
          </p>
        </CardContent>
        <CardFooter
          v-if="job.metrics.providers"
          class="grid gap-3 sm:grid-cols-2"
        >
          <div
            v-for="(provider, name) in job.metrics.providers"
            :key="name"
            class="text-sm"
          >
            <span class="font-medium">{{ String(name).toLowerCase() === 'openai' ? 'OpenAI' : 'Jev' }}</span>
            <span class="text-muted-foreground ml-2">{{ number(provider.api_calls) }} calls · {{ dollars(provider.estimated_cost_usd) }} estimated</span>
          </div>
        </CardFooter>
      </Card>

      <Card>
        <CardHeader class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div class="grid gap-1">
            <CardTitle>Client results</CardTitle>
            <CardDescription>Select a client to inspect profiles, evidence and generated advertisements.</CardDescription>
          </div>
          <Select v-model="filter">
            <SelectTrigger
              aria-label="Filter results"
              class="w-full sm:w-44"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">
                All decisions
              </SelectItem>
              <SelectItem value="recommended">
                With offers
              </SelectItem>
              <SelectItem value="abstained">
                Abstained
              </SelectItem>
              <SelectItem value="opt_out">
                Opted out
              </SelectItem>
              <SelectItem value="error">
                Technical errors
              </SelectItem>
            </SelectContent>
          </Select>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Client</TableHead>
                <TableHead>Decision</TableHead>
                <TableHead>Profiles</TableHead>
                <TableHead class="text-right">
                  Ads
                </TableHead>
                <TableHead class="text-right">
                  Duration
                </TableHead>
                <TableHead class="text-right">
                  Est. cost
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow
                v-for="result in visibleResults"
                :key="result.client.id"
                class="cursor-pointer"
                @click="inspect(result)"
              >
                <TableCell>
                  <button
                    class="text-left font-medium hover:underline"
                    @click.stop="inspect(result)"
                  >
                    {{ result.client.name }}
                  </button>
                  <div class="text-muted-foreground text-xs">
                    {{ result.client.city }}
                  </div>
                </TableCell>
                <TableCell>
                  <Badge :variant="result.status === 'error' ? 'destructive' : 'outline'">
                    {{ statusLabels[result.status] }}
                  </Badge>
                </TableCell>
                <TableCell class="text-muted-foreground max-w-48 truncate">
                  {{ result.profiles.map(profile => profile.label).join(', ') || '—' }}
                </TableCell>
                <TableCell class="text-right tabular-nums">
                  {{ result.ads.length }}
                </TableCell>
                <TableCell class="text-right tabular-nums">
                  {{ duration(result.metrics.duration_ms) }}
                </TableCell>
                <TableCell class="text-right tabular-nums">
                  {{ dollars(result.metrics.estimated_cost_usd) }}
                </TableCell>
              </TableRow>
              <TableEmpty
                v-if="!visibleResults.length"
                :colspan="6"
              >
                {{ running ? 'Waiting for the first matching result…' : 'No results in this view.' }}
              </TableEmpty>
            </TableBody>
          </Table>
        </CardContent>
        <CardFooter class="flex flex-wrap justify-between gap-3">
          <span class="text-muted-foreground text-xs">{{ number(filteredResults.length) }} results</span>
          <div class="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              :disabled="page === 0"
              @click="page--"
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              :disabled="(page + 1) * 20 >= filteredResults.length"
              @click="page++"
            >
              Next
            </Button>
          </div>
        </CardFooter>
      </Card>
      <p class="text-muted-foreground text-xs">
        Measured for this run only; throughput is not a capacity guarantee. Cost uses configured token rates and may include estimates, retries and category discovery. Partial or stopped runs are reported as measured.
      </p>
    </template>
    <Card v-else>
      <CardHeader>
        <CardTitle>No benchmark results yet</CardTitle>
        <CardDescription>Choose a batch size and start the workflow. Live metrics and individual client outcomes will appear here.</CardDescription>
      </CardHeader>
    </Card>
    <p
      v-if="savedLoading"
      role="status"
      class="text-muted-foreground flex items-center gap-2 text-sm"
    >
      <IconLoader2 class="size-4 animate-spin" /> Loading saved benchmark…
    </p>
    <p
      v-if="historyError"
      role="alert"
      class="text-destructive text-sm"
    >
      {{ historyError }}
    </p>
    <RunHistory
      kind="benchmark"
      :refresh-key="historyRefresh"
      @select="loadSavedBenchmark"
    />
    <Sheet v-model:open="sheetOpen">
      <SheetContent
        side="right"
        class="w-full overflow-y-auto p-6 sm:max-w-4xl"
      >
        <SheetHeader class="mb-4 p-0 pr-8">
          <SheetTitle>Inspect a client result</SheetTitle>
          <SheetDescription>Evidence, decisions and advertisements from this benchmark run.</SheetDescription>
        </SheetHeader>
        <AnalysisResult
          v-if="selectedResult"
          :analysis="selectedResult"
          show-client
        />
      </SheetContent>
    </Sheet>
  </div>
</template>
