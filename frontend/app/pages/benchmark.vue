<script setup lang="ts">
import { IconArrowRight, IconBolt, IconClock, IconCurrencyDollar, IconDownload, IconLoader2, IconPlayerPlay, IconPlayerStop, IconUsers } from '@tabler/icons-vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet'
import { dollars, duration, errorMessage, number, statusLabels, type Analysis, type Benchmark } from '@/lib/api'

definePageMeta({ title: 'Scalability benchmark' })
const api = useKbcApi()
const count = ref(10)
const concurrency = ref(5)
const job = useState<Benchmark | null>('benchmark-job', () => null)
const starting = ref(false)
const cancelling = ref(false)
const error = ref('')
const selectedResult = ref<Analysis | null>(null)
const sheetOpen = ref(false)
const filter = ref('all')
const page = ref(0)
const health = ref<Awaited<ReturnType<typeof api.health>> | null>(null)
let pollTimer: ReturnType<typeof setTimeout> | undefined
let mounted = false
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
function schedulePoll() {
  clearTimeout(pollTimer)
  if (mounted && running.value)
    pollTimer = setTimeout(poll, 1500)
}
async function poll() {
  if (!job.value)
    return
  try {
    job.value = await api.benchmark(job.value.id)
    error.value = ''
  } catch (cause) {
    error.value = `Could not refresh the run: ${errorMessage(cause)}`
  } finally {
    schedulePoll()
  }
}
async function start() {
  if (starting.value || running.value)
    return
  starting.value = true
  error.value = ''
  selectedResult.value = null
  page.value = 0
  filter.value = 'all'
  try {
    job.value = await api.startBenchmark(count.value, concurrency.value)
    localStorage.setItem('kbc-benchmark-id', job.value.id)
    schedulePoll()
  } catch (cause) {
    error.value = errorMessage(cause)
  } finally {
    starting.value = false
  }
}
async function cancel() {
  if (!job.value)
    return
  cancelling.value = true
  try {
    job.value = await api.cancelBenchmark(job.value.id)
    schedulePoll()
  } catch (cause) {
    error.value = errorMessage(cause)
  } finally {
    cancelling.value = false
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
  if (job.value) {
    schedulePoll()
    return
  }
  const savedId = localStorage.getItem('kbc-benchmark-id')
  if (savedId) {
    try {
      job.value = await api.benchmark(savedId)
      schedulePoll()
    } catch {
      localStorage.removeItem('kbc-benchmark-id')
    }
  }
})
onBeforeUnmount(() => {
  mounted = false
  clearTimeout(pollTimer)
})
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="text-primary mb-2 text-[10px] font-semibold tracking-[0.2em] uppercase">
          From one client to one thousand
        </p><h1 class="text-3xl font-semibold tracking-tight">
          Put scalability to the test.
        </h1><p class="text-muted-foreground mt-2 max-w-2xl text-sm leading-relaxed">
          Run the same workflow at scale. Measure time, throughput and estimated cost, and inspect every decision.
        </p>
      </div><Badge
        variant="outline"
        class="gap-1.5 py-1.5"
      >
        <IconBolt class="text-primary size-3.5" /> Live execution
      </Badge>
    </div>

    <section class="bg-card rounded-xl border p-5 sm:p-6">
      <div class="grid gap-6 lg:grid-cols-[1fr_1fr_auto] lg:items-end">
        <fieldset :disabled="running || starting">
          <legend class="mb-3 text-xs font-medium">
            01 · Batch size
          </legend><div class="grid grid-cols-3 gap-2">
            <button
              v-for="size in [10, 100, 1000]"
              :key="size"
              class="hover:border-primary/50 rounded-lg border px-3 py-3 text-left transition disabled:opacity-50"
              :class="count === size ? 'border-primary bg-primary/10' : 'bg-background/30'"
              @click="count = size"
            >
              <span
                class="block text-lg font-semibold tabular-nums"
                :class="count === size ? 'text-primary' : ''"
              >{{ number(size) }}</span><span class="text-muted-foreground mt-1 block text-[10px]">clients</span>
            </button>
          </div>
        </fieldset>
        <div>
          <label
            for="concurrency"
            class="mb-3 flex items-center justify-between text-xs font-medium"
          ><span>02 · Concurrent clients</span><span class="text-primary tabular-nums">{{ concurrency }} / 10</span></label><div class="bg-background/30 rounded-lg border px-4 py-3">
            <input
              id="concurrency"
              v-model.number="concurrency"
              type="range"
              min="1"
              max="10"
              step="1"
              class="accent-primary my-1 w-full"
              :disabled="running || starting"
            ><p class="text-muted-foreground mt-1 text-[10px]">
              Parallel workflows · actual provider rate limits apply
            </p>
          </div>
        </div>
        <Button
          :disabled="starting || running || health?.jev_configured === false"
          class="h-12 px-6"
          @click="start"
        >
          <IconLoader2
            v-if="starting"
            class="size-4 animate-spin"
          /><IconPlayerPlay
            v-else
            class="size-4"
          />{{ starting ? 'Starting…' : running ? 'Run in progress' : 'Start benchmark' }}<IconArrowRight
            v-if="!running && !starting"
            class="size-4"
          />
        </Button>
      </div>
      <p class="text-muted-foreground mt-4 text-xs leading-relaxed">
        Every run makes real provider calls on synthetic client data. Costs include the configured pricing for Jev and any OpenAI category discovery. {{ health && !health.jev_configured ? 'Set JEV_API on the backend to run this benchmark.' : '' }}
      </p>
    </section>
    <div
      v-if="error"
      role="alert"
      class="border-destructive/30 bg-destructive/10 text-destructive rounded-xl border p-4 text-sm"
    >
      {{ error }}
    </div>

    <template v-if="job">
      <section class="bg-card rounded-xl border p-5">
        <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div class="flex items-center gap-3">
            <IconLoader2
              v-if="running"
              class="text-primary size-5 animate-spin"
            /><span
              v-else
              class="bg-primary/15 text-primary flex size-8 items-center justify-center rounded-full"
            ><IconBolt class="size-4" /></span><div>
              <h2 class="text-sm font-semibold">
                {{ job.status === 'running' ? 'Benchmark running' : job.status === 'completed' ? 'Benchmark complete' : job.status === 'cancelled' ? 'Benchmark stopped' : 'Benchmark failed' }}
              </h2><p class="text-muted-foreground mt-1 text-xs">
                {{ number(job.completed_count) }} / {{ number(job.requested_count) }} clients processed · concurrency {{ job.concurrency }}
              </p>
            </div>
          </div><div class="flex items-center gap-3">
            <span class="text-primary font-mono text-sm">{{ number(progress) }}%</span><Button
              v-if="running"
              variant="outline"
              size="sm"
              :disabled="cancelling"
              @click="cancel"
            >
              <IconPlayerStop class="size-3.5" />{{ cancelling ? 'Stopping…' : 'Stop run' }}
            </Button><Button
              v-else
              variant="outline"
              size="sm"
              @click="exportResults"
            >
              <IconDownload class="size-3.5" /> Export JSON
            </Button>
          </div>
        </div>
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
        </div><p
          v-if="job.error"
          class="text-destructive mt-3 text-xs"
        >
          {{ job.error }}
        </p><p
          v-if="cancelling"
          class="text-muted-foreground mt-3 text-xs"
        >
          In-flight requests finish first so their usage is included.
        </p>
      </section>

      <div class="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <div
          v-for="metric in [
            { label: 'Wall-clock duration', value: duration(job.elapsed_ms), hint: 'Entire run, including waiting time', icon: IconClock },
            { label: 'Client throughput', value: `${number(job.metrics.clients_per_second)} / s`, hint: 'All processed clients / elapsed time', icon: IconUsers },
            { label: 'Estimated total cost', value: dollars(job.metrics.estimated_cost_usd), hint: job.metrics.usage_source === 'provider' ? 'Provider-reported token usage' : 'Includes estimated token usage', icon: IconCurrencyDollar },
            { label: 'Cost per processed client', value: job.completed_count ? dollars(job.metrics.estimated_cost_usd / job.completed_count) : '—', hint: 'Includes abstentions and opt-outs', icon: IconBolt }
          ]"
          :key="metric.label"
          class="bg-card rounded-xl border p-5"
        >
          <div class="text-muted-foreground mb-4 flex items-center justify-between gap-2 text-xs">
            <span>{{ metric.label }}</span><component
              :is="metric.icon"
              class="size-4"
            />
          </div><p class="text-2xl font-semibold tracking-tight tabular-nums">
            {{ metric.value }}
          </p><p class="text-muted-foreground mt-2 text-[10px] leading-relaxed">
            {{ metric.hint }}
          </p>
        </div>
      </div>
      <div class="grid gap-5 lg:grid-cols-2">
        <section class="bg-card rounded-xl border p-5">
          <h3 class="mb-5 text-sm font-semibold">
            Decision distribution
          </h3><div class="bg-muted mb-5 flex h-3 overflow-hidden rounded-full">
            <div
              v-for="outcome in outcomes"
              :key="outcome.label"
              :class="outcome.class"
              :style="{ width: `${job.completed_count ? outcome.value / job.completed_count * 100 : 0}%` }"
            />
          </div><div class="grid grid-cols-4 gap-2">
            <div
              v-for="outcome in outcomes"
              :key="outcome.label"
            >
              <p
                class="text-lg font-semibold tabular-nums"
                :class="outcome.text"
              >
                {{ number(outcome.value) }}
              </p><p class="text-muted-foreground mt-1 text-[10px]">
                {{ outcome.label }}
              </p>
            </div>
          </div><p class="text-muted-foreground mt-4 text-[10px] leading-relaxed">
            Abstentions are valid decisions. Technical errors and personalization opt-outs are counted separately.
          </p>
        </section>
        <section class="bg-card rounded-xl border p-5">
          <h3 class="mb-5 text-sm font-semibold">
            Latency & API usage
          </h3><div class="grid grid-cols-3 gap-x-3 gap-y-5">
            <div
              v-for="metric in [{ label: 'Median · p50', value: duration(job.metrics.p50_latency_ms) }, { label: 'Tail · p95', value: duration(job.metrics.p95_latency_ms) }, { label: 'Average', value: duration(job.metrics.average_latency_ms) }, { label: 'Provider calls', value: number(job.metrics.api_calls) }, { label: 'Input tokens', value: number(job.metrics.input_tokens) }, { label: 'Output tokens', value: number(job.metrics.output_tokens) }]"
              :key="metric.label"
            >
              <p class="text-muted-foreground text-[10px]">
                {{ metric.label }}
              </p><p class="mt-1 text-base font-medium tabular-nums">
                {{ metric.value }}
              </p>
            </div>
          </div>
        </section>
      </div>

      <section
        v-if="job.category_registry_before && job.category_registry_after"
        class="bg-card rounded-xl border p-5"
      >
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 class="text-sm font-semibold">
              Category learning during this run
            </h3><p class="text-muted-foreground mt-1 text-xs">
              {{ job.category_registry_before.count }} categories before · {{ job.category_registry_after.count }} now · {{ job.metrics.openai_calls }} OpenAI calls
            </p>
          </div><Button
            as-child
            variant="outline"
            size="sm"
          >
            <NuxtLink to="/categories">View registry <IconArrowRight class="size-3.5" /></NuxtLink>
          </Button>
        </div><div
          v-if="job.category_registry_after.labels.some(label => !job?.category_registry_before?.labels.includes(label))"
          class="mt-4 flex flex-wrap gap-2"
        >
          <Badge
            v-for="label in job.category_registry_after.labels.filter(label => !job?.category_registry_before?.labels.includes(label))"
            :key="label"
            variant="secondary"
          >
            New · {{ label }}
          </Badge>
        </div><p
          v-else
          class="text-muted-foreground mt-3 text-xs"
        >
          No new category has been saved during this run.
        </p><div
          v-if="job.metrics.providers"
          class="mt-4 grid gap-3 border-t pt-4 sm:grid-cols-2"
        >
          <div
            v-for="(provider, name) in job.metrics.providers"
            :key="name"
            class="text-xs"
          >
            <span class="font-medium uppercase">{{ name }}</span><span class="text-muted-foreground ml-2">{{ number(provider.api_calls) }} calls · {{ dollars(provider.estimated_cost_usd) }} estimated</span>
          </div>
        </div>
      </section>

      <section class="bg-card overflow-hidden rounded-xl border">
        <div class="flex flex-wrap items-center justify-between gap-3 border-b p-5">
          <div>
            <h3 class="text-sm font-semibold">
              Client results
            </h3><p class="text-muted-foreground mt-1 text-xs">
              Select a client to inspect profiles, evidence and generated advertisements.
            </p>
          </div><select
            v-model="filter"
            aria-label="Filter results"
            class="bg-background h-9 rounded-lg border px-3 text-xs"
          >
            <option value="all">
              All decisions
            </option><option value="recommended">
              With offers
            </option><option value="abstained">
              Abstained
            </option><option value="opt_out">
              Opted out
            </option><option value="error">
              Technical errors
            </option>
          </select>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-muted/25 text-muted-foreground">
              <tr>
                <th class="px-5 py-3 font-normal">
                  Client
                </th><th class="px-4 py-3 font-normal">
                  Decision
                </th><th class="px-4 py-3 font-normal">
                  Profiles
                </th><th class="px-4 py-3 font-normal">
                  Ads
                </th><th class="px-4 py-3 font-normal">
                  Duration
                </th><th class="px-5 py-3 text-right font-normal">
                  Est. cost
                </th>
              </tr>
            </thead><tbody class="divide-y">
              <tr
                v-for="result in visibleResults"
                :key="result.client.id"
                class="hover:bg-muted/30 cursor-pointer"
                @click="inspect(result)"
              >
                <td class="px-5 py-4">
                  <button
                    class="text-left font-medium hover:underline"
                    @click.stop="inspect(result)"
                  >
                    {{ result.client.name }}
                  </button><span class="text-muted-foreground mt-1 block text-[10px]">{{ result.client.city }}</span>
                </td><td class="px-4 py-4">
                  <Badge
                    :variant="result.status === 'recommended' ? 'default' : result.status === 'error' ? 'destructive' : 'secondary'"
                    class="text-[9px]"
                  >
                    {{ statusLabels[result.status] }}
                  </Badge>
                </td><td class="text-muted-foreground max-w-48 truncate px-4 py-4">
                  {{ result.profiles.map(profile => profile.label).join(', ') || '—' }}
                </td><td class="px-4 py-4 tabular-nums">
                  {{ result.ads.length }}
                </td><td class="px-4 py-4 whitespace-nowrap tabular-nums">
                  {{ duration(result.metrics.duration_ms) }}
                </td><td class="px-5 py-4 text-right whitespace-nowrap tabular-nums">
                  {{ dollars(result.metrics.estimated_cost_usd) }}
                </td>
              </tr><tr v-if="!visibleResults.length">
                <td
                  colspan="6"
                  class="text-muted-foreground py-10 text-center"
                >
                  {{ running ? 'Waiting for the first matching result…' : 'No results in this view.' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="text-muted-foreground flex items-center justify-between border-t px-5 py-3 text-xs">
          <span>{{ number(filteredResults.length) }} results</span><div class="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              :disabled="page === 0"
              @click="page--"
            >
              Previous
            </Button><Button
              variant="ghost"
              size="sm"
              :disabled="(page + 1) * 20 >= filteredResults.length"
              @click="page++"
            >
              Next
            </Button>
          </div>
        </div>
      </section>
      <p class="text-muted-foreground text-xs leading-relaxed">
        Measured for this run only; throughput is not a capacity guarantee. Cost uses configured token rates and may include estimates, retries and category discovery. Partial or stopped runs are reported as measured.
      </p>
    </template>
    <section
      v-else
      class="flex flex-col items-center rounded-xl border border-dashed px-6 py-16 text-center"
    >
      <div class="bg-primary/10 text-primary mb-5 rounded-2xl p-4">
        <IconBolt class="size-7" />
      </div><h2 class="mb-2 text-lg font-medium">
        A real answer to “does it scale?”
      </h2><p class="text-muted-foreground max-w-md text-sm leading-relaxed">
        Choose a batch size and launch the workflow. Live metrics and individual outcomes will appear here.
      </p>
    </section>
    <Sheet v-model:open="sheetOpen">
      <SheetContent
        side="right"
        class="w-full overflow-y-auto p-6 sm:max-w-4xl"
      >
        <SheetHeader class="mb-5 p-0 pr-8">
          <SheetTitle>Inspect a client result</SheetTitle><SheetDescription>Evidence, decisions and advertisements from this benchmark run.</SheetDescription>
        </SheetHeader><AnalysisResult
          v-if="selectedResult"
          :analysis="selectedResult"
          show-client
        />
      </SheetContent>
    </Sheet>
  </div>
</template>
