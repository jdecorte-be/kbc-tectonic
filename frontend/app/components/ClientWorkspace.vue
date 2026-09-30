<script setup lang="ts">
import { IconCalendar, IconChevronLeft, IconChevronRight, IconCreditCard, IconFingerprint, IconLoader2, IconPlayerPlay, IconSearch, IconShieldCheck, IconShoppingBag, IconWallet } from '@tabler/icons-vue'
import ClientContext from '@/components/ClientContext.vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Card, CardAction, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { ageLabel, analysisSchema, countryName, duration, errorMessage, euros, number, type Analysis, type ClientDetail, type ClientSummary } from '@/lib/api'

const props = defineProps<{
  initialClientId?: string
}>()
const api = useKbcApi()
const healthFailed = ref(false)
const health = ref<Awaited<ReturnType<typeof api.health>> | null>(null)
const clients = ref<ClientSummary[]>([])
const total = ref(0)
const search = ref('')
const optInOnly = ref(false)
const offset = ref(0)
const listLoading = ref(true)
const detailLoading = ref(false)
const detail = ref<ClientDetail | null>(null)
const selectedId = ref(props.initialClientId ?? '')
const analysis = ref<Analysis | null>(null)
const running = ref(false)
const savedLoading = ref(false)
const historyError = ref('')
const historyRefresh = ref(0)
const elapsed = ref(0)
const error = ref('')
const listError = ref('')
const cards = computed(() => [
  { label: 'Account balance', value: detail.value ? euros(detail.value.client.balance) : '—', badge: 'Current', icon: IconWallet, title: detail.value?.client.name ?? 'Select a client', hint: 'Observed balance on this account' },
  { label: 'Transactions', value: detail.value ? number(detail.value.client.transaction_count) : '—', badge: 'Observed', icon: IconCreditCard, title: 'Payments, transfers and income', hint: 'Evidence used to build the profile' },
  { label: 'Available history', value: detail.value ? `${detail.value.facts.observation_days ?? '—'} days` : '—', badge: 'History', icon: IconCalendar, title: 'Habits across the observed period', hint: 'Short histories can limit confidence' },
  { label: 'Available products', value: health.value ? number(health.value.product_count) : '—', badge: 'Catalog', icon: IconShoppingBag, title: 'Offers checked for relevance', hint: 'Recommendations require supporting evidence' }
])
let listRequest = 0
let detailRequest = 0
let analysisRequest = 0
let debounce: ReturnType<typeof setTimeout> | undefined
let timer: ReturnType<typeof setInterval> | undefined
async function loadClients() {
  const request = ++listRequest
  listLoading.value = true
  listError.value = ''
  try {
    const response = await api.clients(search.value, 30, offset.value, optInOnly.value)
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
  ++analysisRequest
  savedLoading.value = false
  historyError.value = ''
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
  if (!detail.value || running.value || savedLoading.value)
    return
  const clientId = detail.value.client.id
  const request = ++analysisRequest
  running.value = true
  error.value = ''
  historyError.value = ''
  elapsed.value = 0
  const started = Date.now()
  timer = setInterval(() => {
    elapsed.value = Date.now() - started
  }, 100)
  try {
    const result = await api.analyze(clientId)
    if (request === analysisRequest && selectedId.value === clientId)
      analysis.value = result
  } catch (cause) {
    if (request === analysisRequest)
      error.value = errorMessage(cause)
  } finally {
    if (request === analysisRequest) {
      running.value = false
      ++historyRefresh.value
    }
    clearInterval(timer)
  }
}
async function loadSavedAnalysis(id: string) {
  if (running.value) {
    historyError.value = 'Wait for the current analysis to finish before opening a saved result.'
    return
  }
  const clientId = selectedId.value
  const request = ++analysisRequest
  savedLoading.value = true
  historyError.value = ''
  try {
    const result = analysisSchema.parse(await $fetch(`/api/analyses/${encodeURIComponent(id)}`))
    if (request !== analysisRequest || selectedId.value !== clientId)
      return
    if (result.client.id !== clientId)
      throw new Error('This saved result belongs to another client. Refresh the history and try again.')
    analysis.value = result
  } catch (cause) {
    if (request === analysisRequest)
      historyError.value = `Could not load the saved result: ${errorMessage(cause)}`
  } finally {
    if (request === analysisRequest)
      savedLoading.value = false
  }
}
function changePage(direction: number) {
  offset.value = Math.max(0, offset.value + direction * 30)
  void loadClients()
}
watch(search, () => {
  ++listRequest
  clearTimeout(debounce)
  debounce = setTimeout(() => {
    offset.value = 0
    void loadClients()
  }, 250)
})
watch(optInOnly, () => {
  clearTimeout(debounce)
  offset.value = 0
  void loadClients()
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
  ++analysisRequest
})
</script>

<template>
  <div class="flex flex-col gap-4 md:gap-6">
    <div class="*:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card dark:*:data-[slot=card]:bg-card grid grid-cols-1 gap-4 *:data-[slot=card]:bg-gradient-to-t *:data-[slot=card]:shadow-xs @xl/main:grid-cols-2 @5xl/main:grid-cols-4">
      <Card
        v-for="card in cards"
        :key="card.label"
        class="@container/card"
      >
        <CardHeader>
          <CardDescription>{{ card.label }}</CardDescription>
          <CardTitle class="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
            {{ card.value }}
          </CardTitle>
          <CardAction>
            <Badge variant="outline">
              <component :is="card.icon" />
              {{ card.badge }}
            </Badge>
          </CardAction>
        </CardHeader>
        <CardFooter class="flex-col items-start gap-1.5 text-sm">
          <div class="line-clamp-1 font-medium">
            {{ card.title }}
          </div>
          <div class="text-muted-foreground">
            {{ card.hint }}
          </div>
        </CardFooter>
      </Card>
    </div>

    <div
      v-if="error"
      role="alert"
      class="border-destructive/30 bg-destructive/10 text-destructive rounded-xl border p-4 text-sm"
    >
      {{ error }}
    </div>

    <div class="grid items-start gap-4 @3xl/main:grid-cols-[300px_minmax(0,1fr)]">
      <Card>
        <CardHeader>
          <CardTitle>Clients</CardTitle>
          <CardDescription>Select a client to explore their history.</CardDescription>
          <CardAction>
            <Badge variant="outline">
              {{ number(total) }}
            </Badge>
          </CardAction>
        </CardHeader>
        <CardContent class="grid gap-4">
          <div class="relative">
            <IconSearch class="text-muted-foreground pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2" />
            <Input
              v-model="search"
              placeholder="Name, ID or city…"
              aria-label="Search clients"
              class="pl-8"
              :disabled="running"
            />
          </div>
          <label
            for="workspace-opt-in"
            class="flex cursor-pointer items-center gap-2 text-sm"
          >
            <Checkbox
              id="workspace-opt-in"
              :model-value="optInOnly"
              :disabled="running"
              @update:model-value="optInOnly = $event === true"
            />
            Opt-in only
          </label>
          <div
            v-if="listError"
            role="alert"
            class="text-destructive grid gap-3 py-4 text-sm"
          >
            {{ listError }}
            <Button
              variant="outline"
              size="sm"
              class="justify-self-start"
              @click="loadClients"
            >
              Retry
            </Button>
          </div>
          <div
            v-else-if="listLoading"
            class="text-muted-foreground flex justify-center gap-2 py-10 text-sm"
          >
            <IconLoader2 class="size-4 animate-spin" /> Loading clients…
          </div>
          <div
            v-else-if="!clients.length"
            class="text-muted-foreground py-10 text-center text-sm"
          >
            No matching clients.
          </div>
          <div
            v-else
            class="max-h-100 overflow-y-auto"
          >
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Client</TableHead>
                  <TableHead class="text-right">
                    Transactions
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow
                  v-for="client in clients"
                  :key="client.id"
                  :data-state="selectedId === client.id ? 'selected' : undefined"
                  class="cursor-pointer"
                  @click="selectClient(client.id)"
                >
                  <TableCell>
                    <button
                      :disabled="running"
                      :aria-pressed="selectedId === client.id"
                      class="text-left font-medium disabled:opacity-60"
                      @click.stop="selectClient(client.id)"
                    >
                      {{ client.name }}
                    </button>
                    <div class="text-muted-foreground text-xs">
                      {{ ageLabel(client.age) }} · {{ client.city }}
                    </div>
                  </TableCell>
                  <TableCell class="text-right tabular-nums">
                    {{ number(client.transaction_count) }}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
        </CardContent>
        <CardFooter class="justify-between gap-2">
          <span class="text-muted-foreground text-xs tabular-nums">{{ total ? offset + 1 : 0 }}–{{ Math.min(offset + 30, total) }} of {{ number(total) }}</span>
          <div class="flex gap-1">
            <Button
              variant="outline"
              size="icon"
              class="size-8"
              :disabled="offset === 0 || running || listLoading"
              aria-label="Previous clients"
              @click="changePage(-1)"
            >
              <IconChevronLeft class="size-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              class="size-8"
              :disabled="offset + 30 >= total || running || listLoading"
              aria-label="Next clients"
              @click="changePage(1)"
            >
              <IconChevronRight class="size-4" />
            </Button>
          </div>
        </CardFooter>
      </Card>

      <div class="grid min-w-0 gap-4">
        <Card
          v-if="detailLoading"
          class="min-h-80 items-center justify-center"
        >
          <div class="text-muted-foreground flex items-center gap-2 text-sm">
            <IconLoader2 class="size-5 animate-spin" /> Reading client history…
          </div>
        </Card>
        <template v-else-if="detail">
          <Card>
            <CardHeader class="flex flex-wrap items-center justify-between gap-4">
              <div class="grid gap-1.5">
                <div class="flex flex-wrap items-center gap-2">
                  <h2 class="text-lg font-semibold">
                    {{ detail.client.name }}
                  </h2>
                  <Badge variant="outline">
                    Synthetic client
                  </Badge>
                </div>
                <CardDescription>{{ ageLabel(detail.client.age) }} · {{ detail.client.city }}, {{ countryName(detail.client.country) }}</CardDescription>
                <p class="text-muted-foreground text-xs">
                  {{ detail.client.id }}
                </p>
              </div>
              <Button
                :disabled="running || savedLoading || detailLoading || (health !== null && !health.jev_configured && detail.client.personalization_allowed)"
                @click="run"
              >
                <IconLoader2
                  v-if="running"
                  class="animate-spin"
                />
                <IconPlayerPlay v-else />
                {{ running ? 'Analyzing…' : analysis ? 'Run again' : 'Run analysis' }}
              </Button>
            </CardHeader>
            <CardFooter class="flex-wrap justify-between gap-2">
              <Badge variant="outline">
                <IconShieldCheck />
                {{ detail.client.personalization_allowed ? 'Personalization allowed' : 'Personalization declined' }}
              </Badge>
              <span class="text-muted-foreground flex items-center gap-2 text-xs">
                <span
                  class="size-1.5 rounded-full"
                  :class="health?.jev_configured ? 'bg-primary' : 'bg-muted-foreground'"
                />
                {{ health ? (health.jev_configured ? 'Jev connected' : 'Jev not configured') : healthFailed ? 'API unavailable' : 'Connecting to API…' }}
              </span>
            </CardFooter>
          </Card>
          <ClientContext
            :client-id="selectedId"
            :refresh-key="historyRefresh"
            :loading-saved="savedLoading"
            :running="running"
            @open-analysis="loadSavedAnalysis"
          />
          <ClientFacts :detail="detail" />
        </template>
        <Card
          v-else
          class="text-muted-foreground min-h-80 items-center justify-center gap-3"
        >
          <IconFingerprint class="size-8" />
          Select a client to start the workflow.
        </Card>
      </div>
    </div>

    <Card
      v-if="running"
      role="status"
    >
      <CardContent class="flex items-center gap-3">
        <IconLoader2 class="text-primary size-5 shrink-0 animate-spin" />
        <div class="flex-1">
          <p class="font-medium">
            Analyzing client evidence
          </p>
          <p class="text-muted-foreground mt-1 text-sm">
            Building the profile and checking which products are relevant.
          </p>
        </div>
        <Badge variant="outline">
          {{ duration(elapsed) }}
        </Badge>
      </CardContent>
    </Card>
    <AnalysisResult
      v-if="analysis"
      :analysis="analysis"
    />
    <p
      v-else-if="!running"
      class="text-muted-foreground flex items-start gap-2 text-sm"
    >
      <IconShieldCheck class="mt-0.5 size-4 shrink-0" />
      Recommendations include supporting evidence. The workflow can return no offer when information is insufficient.
    </p>
    <p
      v-if="savedLoading"
      role="status"
      class="text-muted-foreground flex items-center gap-2 text-sm"
    >
      <IconLoader2 class="size-4 animate-spin" /> Loading saved analysis…
    </p>
    <p
      v-if="historyError"
      role="alert"
      class="text-destructive text-sm"
    >
      {{ historyError }}
    </p>
    <RunHistory
      v-if="selectedId"
      kind="analysis"
      :client-id="selectedId"
      :refresh-key="historyRefresh"
      @select="loadSavedAnalysis"
    />
  </div>
</template>
