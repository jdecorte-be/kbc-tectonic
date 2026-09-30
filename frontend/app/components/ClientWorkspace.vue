<script setup lang="ts">
import { IconArrowRight, IconCheck, IconChevronLeft, IconChevronRight, IconDatabase, IconFingerprint, IconLoader2, IconPlayerPlay, IconSearch, IconShieldCheck, IconSparkles } from '@tabler/icons-vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { countryName, duration, errorMessage, number, type Analysis, type ClientDetail, type ClientSummary } from '@/lib/api'

const props = defineProps<{
  initialClientId?: string
}>()
const api = useKbcApi()
const healthFailed = ref(false)
const health = ref<Awaited<ReturnType<typeof api.health>> | null>(null)
const clients = ref<ClientSummary[]>([])
const total = ref(0)
const search = ref('')
const offset = ref(0)
const listLoading = ref(true)
const detailLoading = ref(false)
const detail = ref<ClientDetail | null>(null)
const selectedId = ref(props.initialClientId ?? '')
const analysis = ref<Analysis | null>(null)
const running = ref(false)
const elapsed = ref(0)
const error = ref('')
const listError = ref('')
let listRequest = 0
let detailRequest = 0
let debounce: ReturnType<typeof setTimeout> | undefined
let timer: ReturnType<typeof setInterval> | undefined
async function loadClients() {
  const request = ++listRequest
  listLoading.value = true
  listError.value = ''
  try {
    const response = await api.clients(search.value, 30, offset.value)
    if (request !== listRequest)
      return
    clients.value = response.items
    total.value = response.total
    if (!selectedId.value && response.items[0])
      await selectClient(response.items[0].id)
  } catch (cause) {
    if (request === listRequest)
      listError.value = errorMessage(cause)
  } finally {
    if (request === listRequest)
      listLoading.value = false
  }
}
async function selectClient(id: string) {
  if (running.value)
    return
  selectedId.value = id
  analysis.value = null
  detail.value = null
  error.value = ''
  detailLoading.value = true
  const request = ++detailRequest
  try {
    const response = await api.client(id)
    if (request === detailRequest)
      detail.value = response
  } catch (cause) {
    if (request === detailRequest)
      error.value = errorMessage(cause)
  } finally {
    if (request === detailRequest)
      detailLoading.value = false
  }
}
async function run() {
  if (!detail.value || running.value)
    return
  running.value = true
  error.value = ''
  analysis.value = null
  elapsed.value = 0
  const started = Date.now()
  timer = setInterval(() => {
    elapsed.value = Date.now() - started
  }, 100)
  try {
    analysis.value = await api.analyze(detail.value.client.id)
  } catch (cause) {
    error.value = errorMessage(cause)
  } finally {
    running.value = false
    clearInterval(timer)
  }
}
function changePage(direction: number) {
  offset.value = Math.max(0, offset.value + direction * 30)
  void loadClients()
}
watch(search, () => {
  clearTimeout(debounce)
  debounce = setTimeout(() => {
    offset.value = 0
    void loadClients()
  }, 250)
})
onMounted(async () => {
  await Promise.allSettled([
    api.health().then((value) => {
      health.value = value
    }).catch((cause) => {
      healthFailed.value = true
      error.value = errorMessage(cause)
    }),
    loadClients(),
    ...(props.initialClientId ? [selectClient(props.initialClientId)] : [])
  ])
})
onBeforeUnmount(() => {
  clearTimeout(debounce)
  clearInterval(timer)
  ++listRequest
  ++detailRequest
})
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex flex-wrap items-start justify-between gap-4">
      <div>
        <p class="text-primary mb-2 text-[10px] font-semibold tracking-[0.2em] uppercase">
          Customer intelligence
        </p><h1 class="text-3xl font-semibold tracking-tight">
          Understand. Match. Recommend.
        </h1><p class="text-muted-foreground mt-2 max-w-2xl text-sm leading-relaxed">
          Turn a synthetic client’s transaction history into an explained profile and relevant product offers.
        </p>
      </div>
      <div class="bg-card flex items-center gap-2 rounded-full border px-3 py-2 text-xs">
        <span
          class="size-1.5 rounded-full"
          :class="health?.jev_configured ? 'bg-primary' : 'bg-muted-foreground'"
        />{{ health ? (health.jev_configured ? 'Jev connected' : 'Jev not configured') : healthFailed ? 'API unavailable' : 'Connecting to API…' }}
      </div>
    </div>

    <div class="bg-card grid grid-cols-1 rounded-xl border sm:grid-cols-3">
      <div
        v-for="(step, index) in [{ icon: IconDatabase, label: 'Read the evidence', caption: 'Balance, transactions & recurring habits' }, { icon: IconFingerprint, label: 'Build the profile', caption: 'Jev classification & category discovery' }, { icon: IconSparkles, label: 'Select relevant offers', caption: 'Product fit, confidence & clear reasoning' }]"
        :key="step.label"
        class="flex items-center gap-3 px-5 py-4"
        :class="index ? 'border-t sm:border-t-0 sm:border-l' : ''"
      >
        <span class="bg-primary/10 text-primary flex size-9 shrink-0 items-center justify-center rounded-lg"><component
          :is="step.icon"
          class="size-4"
        /></span><div>
          <p class="text-xs font-medium">
            <span class="text-muted-foreground mr-1.5">0{{ index + 1 }}</span>{{ step.label }}
          </p><p class="text-muted-foreground mt-1 text-[11px]">
            {{ step.caption }}
          </p>
        </div>
      </div>
    </div>

    <div
      v-if="error"
      role="alert"
      class="border-destructive/30 bg-destructive/10 text-destructive rounded-xl border p-4 text-sm"
    >
      {{ error }}
    </div>
    <div class="grid items-start gap-5 xl:grid-cols-[280px_1fr]">
      <section class="bg-card overflow-hidden rounded-xl border">
        <div class="border-b p-4">
          <div class="mb-3 flex items-center justify-between">
            <h2 class="text-sm font-semibold">
              Select a client
            </h2><span class="text-muted-foreground text-xs tabular-nums">{{ number(total) }}</span>
          </div><div class="relative">
            <IconSearch class="text-muted-foreground absolute top-2.5 left-3 size-4" /><Input
              v-model="search"
              placeholder="Search name, ID or city…"
              aria-label="Search clients"
              class="h-9 pl-9"
              :disabled="running"
            />
          </div>
        </div>
        <p
          v-if="listError"
          role="alert"
          class="text-destructive p-4 text-xs"
        >
          {{ listError }}<Button
            class="mt-3"
            variant="outline"
            size="sm"
            @click="loadClients"
          >
            Retry
          </Button>
        </p>
        <div
          v-else-if="listLoading"
          class="text-muted-foreground flex justify-center gap-2 p-8 text-xs"
        >
          <IconLoader2 class="size-4 animate-spin" /> Loading clients…
        </div>
        <div
          v-else-if="!clients.length"
          class="text-muted-foreground p-8 text-center text-sm"
        >
          No matching clients.
        </div>
        <div
          v-else
          class="max-h-100 overflow-y-auto p-2 xl:max-h-115"
        >
          <button
            v-for="client in clients"
            :key="client.id"
            :disabled="running"
            :aria-pressed="selectedId === client.id"
            class="hover:bg-muted/50 flex w-full items-center gap-3 rounded-lg border border-transparent px-3 py-3 text-left transition disabled:opacity-60"
            :class="selectedId === client.id ? 'bg-primary/10 border-primary/20!' : ''"
            @click="selectClient(client.id)"
          >
            <span
              class="bg-muted text-muted-foreground flex size-9 shrink-0 items-center justify-center rounded-full text-xs font-medium"
              :class="selectedId === client.id ? 'bg-primary/15! text-primary!' : ''"
            >{{ client.name.split(' ').map(word => word[0]).slice(0, 2).join('') }}</span>
            <span class="min-w-0 flex-1"><span class="block truncate text-xs font-medium">{{ client.name }}</span><span class="text-muted-foreground mt-1 block truncate text-[11px]">{{ client.city }} · {{ client.transaction_count }} transactions</span></span><IconCheck
              v-if="selectedId === client.id"
              class="text-primary size-3.5 shrink-0"
            />
          </button>
        </div>
        <div class="text-muted-foreground flex items-center justify-between border-t px-4 py-2 text-[10px]">
          <span>{{ total ? offset + 1 : 0 }}–{{ Math.min(offset + 30, total) }} of {{ number(total) }}</span><div class="flex gap-1">
            <Button
              variant="ghost"
              size="icon"
              class="size-7"
              :disabled="offset === 0 || running || listLoading"
              aria-label="Previous clients"
              @click="changePage(-1)"
            >
              <IconChevronLeft class="size-3.5" />
            </Button><Button
              variant="ghost"
              size="icon"
              class="size-7"
              :disabled="offset + 30 >= total || running || listLoading"
              aria-label="Next clients"
              @click="changePage(1)"
            >
              <IconChevronRight class="size-3.5" />
            </Button>
          </div>
        </div>
      </section>

      <section class="bg-card flex min-h-115 flex-col rounded-xl border p-5 sm:p-6">
        <div
          v-if="detailLoading"
          class="text-muted-foreground flex flex-1 items-center justify-center gap-2 text-sm"
        >
          <IconLoader2 class="size-5 animate-spin" /> Reading client history…
        </div>
        <template v-else-if="detail">
          <div class="mb-6 flex flex-wrap items-start justify-between gap-3">
            <div>
              <div class="mb-1 flex flex-wrap items-center gap-2">
                <h2 class="text-xl font-semibold tracking-tight">
                  {{ detail.client.name }}
                </h2><Badge
                  variant="outline"
                  class="text-[9px]"
                >
                  Synthetic client
                </Badge>
              </div><p class="text-muted-foreground text-xs">
                {{ detail.client.age }} years · {{ detail.client.city }}, {{ countryName(detail.client.country) }}
              </p><p class="text-muted-foreground/60 mt-1 font-mono text-[10px]">
                {{ detail.client.id }}
              </p>
            </div><Badge
              :variant="detail.client.personalization_allowed ? 'secondary' : 'outline'"
              class="gap-1 text-[10px]"
            >
              <IconShieldCheck class="size-3" />{{ detail.client.personalization_allowed ? 'Personalization allowed' : 'Personalization declined' }}
            </Badge>
          </div>
          <ClientFacts :detail="detail" />
          <div class="mt-5 flex flex-wrap items-center justify-between gap-3 border-t pt-5">
            <p class="text-muted-foreground max-w-sm text-xs leading-relaxed">
              {{ detail.client.personalization_allowed ? 'The workflow checks the available evidence and can choose to withhold a recommendation.' : 'The workflow will respect this preference and return no personalized advertising.' }}
            </p><Button
              :disabled="running || detailLoading || (health !== null && !health.jev_configured && detail.client.personalization_allowed)"
              class="h-10 px-5"
              @click="run"
            >
              <IconLoader2
                v-if="running"
                class="size-4 animate-spin"
              /><IconPlayerPlay
                v-else
                class="size-4"
              />{{ running ? 'Analyzing…' : analysis ? 'Run again' : 'Run analysis' }}<IconArrowRight
                v-if="!running"
                class="size-4"
              />
            </Button>
          </div>
        </template>
        <div
          v-else
          class="text-muted-foreground flex flex-1 flex-col items-center justify-center gap-3 text-sm"
        >
          <IconFingerprint class="size-8 opacity-40" /> Select a client to start the workflow.
        </div>
      </section>
    </div>

    <div
      v-if="running"
      class="border-primary/30 bg-primary/5 flex items-center gap-4 rounded-xl border p-5"
      role="status"
    >
      <IconLoader2 class="text-primary size-6 shrink-0 animate-spin" /><div class="flex-1">
        <p class="text-sm font-medium">
          Analyzing evidence and evaluating product relevance
        </p><p class="text-muted-foreground mt-1 text-xs">
          The full workflow is running. Results and measured stages will appear when it finishes.
        </p>
      </div><span class="text-primary font-mono text-sm tabular-nums">{{ duration(elapsed) }}</span>
    </div>
    <AnalysisResult
      v-if="analysis"
      :analysis="analysis"
    />
    <div
      v-else-if="!running"
      class="text-muted-foreground flex items-start gap-2 text-xs leading-relaxed"
    >
      <IconShieldCheck class="mt-0.5 size-4 shrink-0" /><p>Every recommendation includes its supporting evidence. Limited data, unsuitable products and declined personalization are valid outcomes.</p>
    </div>
  </div>
</template>
