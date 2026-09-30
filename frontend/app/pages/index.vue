<script setup lang="ts">
import { IconArrowUpRight, IconChartBar, IconCheck, IconChevronLeft, IconChevronRight, IconGift, IconLoader2, IconRefresh, IconSearch, IconShieldCheck, IconUsers, IconX } from '@tabler/icons-vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardAction, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableEmpty, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { ageLabel, errorMessage, euros, number, statusLabels } from '@/lib/api'
import { dashboardSchema, type Dashboard, type DashboardClient } from '@/lib/dashboard'

definePageMeta({ title: 'Dashboard', alias: ['/dashboard'] })
const data = ref<Dashboard | null>(null)
const loading = ref(true)
const error = ref('')
const search = ref('')
const optInOnly = ref(false)
const segment = ref('all')
const outcome = ref('all')
const product = ref('')
const selectedProductName = ref('')
const offset = ref(0)
const pageSize = 25
let requestId = 0
let debounce: ReturnType<typeof setTimeout> | undefined

const filtered = computed(() => Boolean(search.value || optInOnly.value || segment.value !== 'all' || outcome.value !== 'all' || product.value))
const summary = computed(() => data.value?.summary)
const profiles = computed(() => [...(data.value?.segments ?? [])].sort((a, b) => b.count - a.count))
const maxProfileCount = computed(() => Math.max(1, ...profiles.value.map(item => item.count)))
const selectedProducts = computed(() => [...(data.value?.products ?? [])].filter(item => item.count > 0).sort((a, b) => b.count - a.count))
const maxProductCount = computed(() => Math.max(1, ...selectedProducts.value.map(item => item.count)))
const coverage = computed(() => summary.value?.total_clients ? Math.round(summary.value.analyzed_count / summary.value.total_clients * 100) : 0)
const optInRate = computed(() => summary.value?.total_clients ? Math.round(summary.value.opt_in_count / summary.value.total_clients * 100) : 0)
const updatedAt = computed(() => data.value ? new Date(data.value.generated_at).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) : '')
const compactEuro = (cents: number) => new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'EUR', notation: 'compact', maximumFractionDigits: 1 }).format(cents / 100)
const outcomeColors: Record<string, string> = {
  recommended: 'var(--chart-1)',
  insufficient_information: 'var(--chart-3)',
  no_match: 'var(--chart-4)',
  opt_out: 'var(--chart-2)',
  error: 'var(--destructive)',
  not_analyzed: 'var(--muted)'
}
const outcomeRing = computed(() => {
  const total = summary.value?.total_clients ?? 0
  if (!total)
    return 'var(--muted)'
  let position = 0
  const stops = (data.value?.outcomes ?? []).filter(item => item.count > 0).map((item) => {
    const start = position
    position += item.count / total * 100
    return `${outcomeColors[item.id] ?? 'var(--muted)'} ${start}% ${position}%`
  })
  return `conic-gradient(${stops.join(', ')})`
})
const outcomeLabel = (status: DashboardClient['analysis']['status']) => status === 'not_analyzed' ? 'Not analyzed yet' : statusLabels[status]
const savedDate = (value: string | null) => value ? new Date(value).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' }) : ''

async function load() {
  clearTimeout(debounce)
  const id = ++requestId
  loading.value = true
  error.value = ''
  try {
    const response = dashboardSchema.parse(await $fetch('/api/dashboard', {
      query: {
        q: search.value,
        opt_in_only: optInOnly.value,
        segment: segment.value === 'all' ? '' : segment.value,
        outcome: outcome.value === 'all' ? '' : outcome.value,
        product: product.value,
        limit: pageSize,
        offset: offset.value
      }
    }))
    if (id === requestId)
      data.value = response
  } catch (cause) {
    if (id === requestId)
      error.value = errorMessage(cause)
  } finally {
    if (id === requestId)
      loading.value = false
  }
}
function resetFilters() {
  search.value = ''
  optInOnly.value = false
  segment.value = 'all'
  outcome.value = 'all'
  product.value = ''
  selectedProductName.value = ''
}
function selectProduct(id: string, name: string) {
  product.value = product.value === id ? '' : id
  selectedProductName.value = product.value ? name : ''
}
function changePage(direction: number) {
  offset.value = Math.max(0, offset.value + direction * pageSize)
  void load()
}
watch([search, optInOnly, segment, outcome, product], (values, previous) => {
  clearTimeout(debounce)
  ++requestId
  offset.value = 0
  loading.value = true
  const searchOnly = values[0] !== previous[0] && values.slice(1).every((value, index) => value === previous[index + 1])
  debounce = setTimeout(load, searchOnly ? 300 : 0)
})
onMounted(load)
onBeforeUnmount(() => {
  clearTimeout(debounce)
  ++requestId
})
</script>

<template>
  <div class="flex min-w-0 flex-col gap-4 md:gap-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="text-lg font-semibold tracking-tight">
          Customer intelligence
        </h2>
        <p class="text-muted-foreground mt-1 text-sm">
          Understand your customers, their habits and the offers selected for them.
        </p>
      </div>
      <div class="flex items-center gap-2">
        <span
          v-if="updatedAt"
          class="text-muted-foreground hidden text-xs sm:inline"
        >Updated {{ updatedAt }}</span>
        <Button
          variant="outline"
          size="sm"
          :disabled="loading"
          @click="load"
        >
          <IconRefresh :class="loading && 'animate-spin'" /> Refresh
        </Button>
        <Button
          as-child
          size="sm"
        >
          <NuxtLink to="/benchmark"><IconChartBar /> Run benchmark</NuxtLink>
        </Button>
      </div>
    </div>

    <Card>
      <CardContent class="flex flex-wrap items-end gap-3">
        <div class="grid min-w-48 flex-1 gap-1.5">
          <label
            for="dashboard-search"
            class="text-muted-foreground text-xs font-medium"
          >Search customers</label>
          <div class="relative">
            <IconSearch class="text-muted-foreground pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2" />
            <Input
              id="dashboard-search"
              v-model="search"
              placeholder="Name, city or customer ID…"
              class="pl-8"
            />
          </div>
        </div>
        <div class="grid min-w-44 gap-1.5">
          <label
            for="dashboard-profile"
            class="text-muted-foreground text-xs font-medium"
          >Observed profile</label>
          <Select v-model="segment">
            <SelectTrigger
              id="dashboard-profile"
              class="w-full"
            >
              <SelectValue placeholder="All profiles" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">
                All profiles
              </SelectItem>
              <SelectItem
                v-for="item in data?.segments ?? []"
                :key="item.id"
                :value="item.id"
              >
                {{ item.label }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div class="grid min-w-44 gap-1.5">
          <label
            for="dashboard-outcome"
            class="text-muted-foreground text-xs font-medium"
          >Recommendation outcome</label>
          <Select v-model="outcome">
            <SelectTrigger
              id="dashboard-outcome"
              class="w-full"
            >
              <SelectValue placeholder="All outcomes" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">
                All outcomes
              </SelectItem>
              <SelectItem
                v-for="item in data?.outcomes ?? []"
                :key="item.id"
                :value="item.id"
              >
                {{ item.label }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
        <label
          for="dashboard-opt-in"
          class="border-input flex h-8 cursor-pointer items-center gap-2 rounded-md border px-3 text-sm"
        >
          <Checkbox
            id="dashboard-opt-in"
            v-model="optInOnly"
          />
          Opt-in only
        </label>
        <Button
          v-if="filtered"
          variant="ghost"
          size="sm"
          @click="resetFilters"
        >
          <IconX /> Reset
        </Button>
      </CardContent>
      <CardFooter
        v-if="product"
        class="gap-2 py-2"
      >
        <span class="text-muted-foreground text-xs">Selected offer</span>
        <Button
          variant="secondary"
          size="sm"
          @click="product = ''; selectedProductName = ''"
        >
          {{ selectedProductName }} <IconX />
        </Button>
      </CardFooter>
    </Card>

    <div
      v-if="error"
      role="alert"
      class="border-destructive/30 bg-destructive/5 text-destructive flex flex-wrap items-center justify-between gap-3 rounded-xl border p-4 text-sm"
    >
      <p>{{ error }} <span v-if="data">The last loaded overview is shown below.</span></p>
      <Button
        variant="outline"
        size="sm"
        @click="load"
      >
        Retry
      </Button>
    </div>

    <template v-if="!data && loading">
      <div class="grid grid-cols-2 gap-4 xl:grid-cols-4">
        <Skeleton
          v-for="item in 4"
          :key="item"
          class="h-36 rounded-xl"
        />
      </div>
      <Skeleton class="h-72 rounded-xl" />
      <Skeleton class="h-96 rounded-xl" />
      <p
        role="status"
        class="text-muted-foreground flex items-center justify-center gap-2 text-sm"
      >
        <IconLoader2 class="size-4 animate-spin" /> Loading customer intelligence…
      </p>
    </template>

    <div
      v-else-if="data && summary"
      :aria-busy="loading"
      class="flex min-w-0 flex-col gap-4 md:gap-6"
      :class="loading && 'opacity-60'"
    >
      <div class="grid grid-cols-1 gap-4 @xl/main:grid-cols-2 @5xl/main:grid-cols-4">
        <Card class="@container/card">
          <CardHeader>
            <CardDescription>{{ filtered ? 'Customers in this view' : 'Total customers' }}</CardDescription>
            <CardTitle class="text-3xl font-semibold tabular-nums">
              {{ number(summary.total_clients) }}
            </CardTitle>
            <CardAction>
              <Badge variant="outline">
                <IconUsers /> {{ optInRate }}% opt-in
              </Badge>
            </CardAction>
          </CardHeader>
          <CardFooter class="flex-col items-start gap-1 text-sm">
            <div class="font-medium">
              {{ number(summary.opt_in_count) }} opted in · {{ number(summary.opt_out_count) }} opted out
            </div>
            <div class="text-muted-foreground text-xs">
              Commercial personalization preferences
            </div>
          </CardFooter>
        </Card>
        <Card class="@container/card">
          <CardHeader>
            <CardDescription>Analysis coverage</CardDescription>
            <CardTitle class="text-3xl font-semibold tabular-nums">
              {{ coverage }}<span class="text-muted-foreground text-xl">%</span>
            </CardTitle>
            <CardAction>
              <Badge variant="outline">
                <IconCheck /> {{ number(summary.analyzed_count) }} analyzed
              </Badge>
            </CardAction>
          </CardHeader>
          <CardFooter class="flex-col items-start gap-1 text-sm">
            <div class="font-medium">
              {{ number(summary.not_analyzed_count) }} awaiting analysis
            </div>
            <div class="text-muted-foreground text-xs">
              Latest saved result for each customer
            </div>
          </CardFooter>
        </Card>
        <Card class="@container/card">
          <CardHeader>
            <CardDescription>Customers with offers</CardDescription>
            <CardTitle class="text-3xl font-semibold tabular-nums">
              {{ number(summary.recommended_count) }}
            </CardTitle>
            <CardAction>
              <Badge variant="outline">
                <IconGift /> {{ number(summary.selected_ad_count) }} ads
              </Badge>
            </CardAction>
          </CardHeader>
          <CardFooter class="flex-col items-start gap-1 text-sm">
            <div class="font-medium">
              {{ number(summary.abstained_count) }} with no offer selected
            </div>
            <div class="text-muted-foreground text-xs">
              {{ number(summary.error_count) }} technical errors to review
            </div>
          </CardFooter>
        </Card>
        <Card class="@container/card">
          <CardHeader>
            <CardDescription>Combined balance</CardDescription>
            <CardTitle
              class="text-3xl font-semibold tabular-nums"
              :title="euros(summary.total_balance_cents / 100)"
            >
              {{ compactEuro(summary.total_balance_cents) }}
            </CardTitle>
            <CardAction>
              <Badge variant="outline">
                <IconShieldCheck /> Synthetic
              </Badge>
            </CardAction>
          </CardHeader>
          <CardFooter class="flex-col items-start gap-1 text-sm">
            <div class="font-medium">
              {{ number(summary.total_transactions) }} observed transactions
            </div>
            <div class="text-muted-foreground text-xs">
              Across all customers in the current view
            </div>
          </CardFooter>
        </Card>
      </div>

      <div class="grid min-w-0 gap-4 lg:grid-cols-2 2xl:grid-cols-3">
        <Card class="min-w-0">
          <CardHeader>
            <CardTitle>Observed profiles</CardTitle>
            <CardDescription>Patterns from banking activity. Click a profile to explore.</CardDescription>
          </CardHeader>
          <CardContent class="max-h-60 space-y-3 overflow-y-auto">
            <button
              v-for="item in profiles"
              :key="item.id"
              type="button"
              :aria-pressed="segment === item.id"
              :disabled="loading"
              :title="item.description"
              class="hover:bg-muted/50 focus-visible:ring-ring -m-1 block w-full rounded-md p-1 text-left outline-none focus-visible:ring-2"
              @click="segment = segment === item.id ? 'all' : item.id"
            >
              <span class="mb-1.5 flex items-center justify-between gap-3 text-xs">
                <span :class="segment === item.id ? 'text-primary font-semibold' : 'font-medium'">{{ item.label }}</span>
                <span class="text-muted-foreground tabular-nums">{{ number(item.count) }}</span>
              </span>
              <span class="bg-muted block h-1.5 overflow-hidden rounded-full">
                <span
                  class="bg-primary block h-full rounded-full"
                  :class="segment !== 'all' && segment !== item.id && 'opacity-40'"
                  :style="{ width: `${item.count / maxProfileCount * 100}%` }"
                />
              </span>
            </button>
          </CardContent>
          <CardFooter class="text-muted-foreground text-xs">
            Counts follow search and consent. Profiles can overlap.
          </CardFooter>
        </Card>

        <Card class="min-w-0">
          <CardHeader>
            <CardTitle>Recommendation outcomes</CardTitle>
            <CardDescription>Latest saved outcomes and current consent preferences.</CardDescription>
          </CardHeader>
          <CardContent class="flex flex-1 flex-wrap items-center justify-center gap-5">
            <div
              class="relative flex size-32 shrink-0 items-center justify-center rounded-full"
              :style="{ background: outcomeRing }"
              role="img"
              :aria-label="`${coverage}% of customers in this view have a saved analysis`"
            >
              <div class="bg-card flex size-24 flex-col items-center justify-center rounded-full">
                <span class="text-2xl font-semibold tabular-nums">{{ coverage }}%</span>
                <span class="text-muted-foreground text-xs">analyzed</span>
              </div>
            </div>
            <div class="min-w-40 flex-1 space-y-1">
              <button
                v-for="item in data.outcomes"
                :key="item.id"
                type="button"
                :disabled="loading"
                :aria-pressed="outcome === item.id"
                class="hover:bg-muted/50 focus-visible:ring-ring flex w-full items-center gap-2 rounded-md p-1.5 text-left text-xs outline-none focus-visible:ring-2"
                @click="outcome = outcome === item.id ? 'all' : item.id"
              >
                <span
                  class="size-2 shrink-0 rounded-full"
                  :style="{ backgroundColor: outcomeColors[item.id] }"
                />
                <span
                  class="flex-1"
                  :class="outcome === item.id && 'text-primary font-medium'"
                >{{ item.label }}</span>
                <span class="font-medium tabular-nums">{{ number(item.count) }}</span>
              </button>
            </div>
          </CardContent>
        </Card>

        <Card class="min-w-0 lg:col-span-2 2xl:col-span-1">
          <CardHeader>
            <CardTitle>Monthly cash flow</CardTitle>
            <CardDescription>All observed credits and debits in the current view.</CardDescription>
          </CardHeader>
          <CardContent class="px-2">
            <DashboardCashflow :cashflow="data.cashflow" />
          </CardContent>
          <CardFooter class="text-muted-foreground text-xs">
            Includes transfers. {{ data.cashflow.length }} months of observed activity.
          </CardFooter>
        </Card>
      </div>

      <div class="grid min-w-0 items-start gap-4 xl:grid-cols-[minmax(0,1.6fr)_minmax(280px,1fr)]">
        <CustomerNetwork :network="data.network" />
        <Card class="min-w-0">
          <CardHeader>
            <CardTitle>Selected offers</CardTitle>
            <CardDescription>Customers matched to each product in their latest analysis.</CardDescription>
            <CardAction>
              <Badge variant="outline">
                {{ number(summary.selected_ad_count) }} ads
              </Badge>
            </CardAction>
          </CardHeader>
          <CardContent
            v-if="selectedProducts.length"
            class="max-h-80 space-y-4 overflow-y-auto"
          >
            <button
              v-for="item in selectedProducts"
              :key="item.id"
              type="button"
              :disabled="loading"
              :aria-pressed="product === item.id"
              class="hover:bg-muted/50 focus-visible:ring-ring -m-1 block w-full rounded-md p-1 text-left outline-none focus-visible:ring-2"
              @click="selectProduct(item.id, item.name)"
            >
              <span class="mb-2 flex items-start justify-between gap-3 text-sm">
                <span class="font-medium">{{ item.name }}</span>
                <span class="text-muted-foreground shrink-0 text-xs tabular-nums">{{ number(item.count) }} {{ item.count === 1 ? 'customer' : 'customers' }}</span>
              </span>
              <span class="bg-muted block h-2 overflow-hidden rounded-full">
                <span
                  class="bg-chart-3 block h-full rounded-full"
                  :style="{ width: `${item.count / maxProductCount * 100}%` }"
                />
              </span>
            </button>
          </CardContent>
          <CardContent
            v-else
            class="flex min-h-56 flex-col items-center justify-center gap-3 px-6 text-center"
          >
            <div class="bg-muted text-muted-foreground flex size-10 items-center justify-center rounded-lg">
              <IconGift class="size-5" />
            </div>
            <div>
              <p class="font-medium">
                No offers selected in this view
              </p>
              <p class="text-muted-foreground mt-1 max-w-72 text-xs leading-relaxed">
                {{ summary.analyzed_count ? 'Some customers have too little information, no suitable product or personalization turned off.' : 'Run an individual analysis or a benchmark to see the products selected by the workflow.' }}
              </p>
            </div>
            <div class="flex gap-2">
              <Button
                as-child
                variant="outline"
                size="sm"
              >
                <NuxtLink to="/client">Analyze a customer <IconArrowUpRight /></NuxtLink>
              </Button>
            </div>
          </CardContent>
          <CardFooter class="text-muted-foreground text-xs">
            {{ selectedProducts.length ? 'Click a product to see its customers. A customer can receive several offers.' : 'Only saved workflow results appear here.' }}
          </CardFooter>
        </Card>
      </div>

      <Card class="min-w-0">
        <CardHeader class="flex flex-wrap items-center justify-between gap-3">
          <div class="grid gap-1">
            <CardTitle>Customer overview</CardTitle>
            <CardDescription>Observed context, commercial preferences and the latest selected ads.</CardDescription>
          </div>
          <Badge variant="outline">
            <IconUsers /> {{ number(data.clients.total) }} customers
          </Badge>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Customer</TableHead>
                <TableHead>Profile & context</TableHead>
                <TableHead>Banking activity</TableHead>
                <TableHead>Consent</TableHead>
                <TableHead>Selected ads</TableHead>
                <TableHead class="text-right">
                  Details
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow
                v-for="row in data.clients.items"
                :key="row.client.id"
              >
                <TableCell class="min-w-40 align-top">
                  <NuxtLink
                    :to="`/client/${row.client.id}`"
                    class="font-medium hover:underline"
                  >
                    {{ row.client.name }}
                  </NuxtLink>
                  <div class="text-muted-foreground mt-1 text-xs">
                    {{ ageLabel(row.client.age) }} · {{ row.client.city }}
                  </div>
                  <div class="text-muted-foreground mt-1 text-xs">
                    {{ row.client.id }}
                  </div>
                </TableCell>
                <TableCell class="min-w-56 max-w-80 align-top whitespace-normal">
                  <div class="flex flex-wrap gap-1">
                    <Badge
                      v-for="item in row.segments.slice(0, 2)"
                      :key="item.id"
                      variant="secondary"
                      :title="item.evidence.join(' · ') || item.description"
                    >
                      {{ item.label }}
                    </Badge>
                    <Badge
                      v-if="row.segments.length > 2"
                      variant="outline"
                      :title="row.segments.slice(2).map(item => item.label).join(', ')"
                    >
                      +{{ row.segments.length - 2 }}
                    </Badge>
                    <span
                      v-if="!row.segments.length"
                      class="text-muted-foreground text-xs"
                    >{{ row.client.personalization_allowed ? 'Not enough evidence' : 'Personalization off' }}</span>
                  </div>
                  <p
                    class="text-muted-foreground mt-1.5 line-clamp-2 text-xs leading-relaxed"
                    :title="row.context.summary"
                  >
                    {{ row.context.summary }}
                  </p>
                  <p
                    v-if="row.analysis.category"
                    class="mt-1 text-xs"
                  >
                    <span class="text-muted-foreground">AI profile:</span> {{ row.analysis.category.label }}
                  </p>
                </TableCell>
                <TableCell class="min-w-40 align-top">
                  <div class="font-medium tabular-nums">
                    {{ euros(row.client.balance) }}
                  </div>
                  <div class="text-muted-foreground mt-1 text-xs tabular-nums">
                    {{ row.context.monthly_income_cents > 0 ? `${compactEuro(row.context.monthly_income_cents)} income / mo.` : 'No income observed' }}
                  </div>
                  <div class="text-muted-foreground mt-1 text-xs">
                    {{ number(row.client.transaction_count) }} transactions · {{ row.context.observation_days }} days
                  </div>
                </TableCell>
                <TableCell class="align-top">
                  <Badge
                    variant="outline"
                    :class="row.client.personalization_allowed ? 'text-primary' : 'text-muted-foreground'"
                  >
                    {{ row.client.personalization_allowed ? 'Opted in' : 'Opted out' }}
                  </Badge>
                </TableCell>
                <TableCell class="min-w-60 max-w-80 align-top whitespace-normal">
                  <template v-if="row.analysis.ads.length">
                    <div
                      v-for="ad in row.analysis.ads"
                      :key="ad.product_id"
                      class="mb-2 last:mb-0"
                      :title="`${ad.reason} · ${Math.round(ad.confidence * 100)}% confidence`"
                    >
                      <div class="flex items-start gap-1.5 text-xs font-medium">
                        <IconGift class="text-primary mt-0.5 size-3.5 shrink-0" />
                        {{ ad.product_name }}
                      </div>
                      <p class="text-muted-foreground mt-0.5 pl-5 text-xs">
                        {{ ad.title }}
                      </p>
                    </div>
                  </template>
                  <template v-else>
                    <div class="text-xs font-medium">
                      {{ outcomeLabel(row.analysis.status) }}
                    </div>
                    <p
                      v-if="row.analysis.summary"
                      class="text-muted-foreground mt-1 line-clamp-2 text-xs leading-relaxed"
                      :title="row.analysis.summary"
                    >
                      {{ row.analysis.summary }}
                    </p>
                  </template>
                  <p
                    v-if="row.analysis.created_at"
                    class="text-muted-foreground mt-1.5 text-xs"
                  >
                    {{ row.analysis.source === 'benchmark' ? 'Benchmark' : 'Individual analysis' }} · {{ savedDate(row.analysis.created_at) }}
                  </p>
                </TableCell>
                <TableCell class="text-right align-top">
                  <Button
                    as-child
                    variant="ghost"
                    size="icon-sm"
                  >
                    <NuxtLink
                      :to="`/client/${row.client.id}`"
                      :aria-label="`View ${row.client.name}`"
                    ><IconArrowUpRight /></NuxtLink>
                  </Button>
                </TableCell>
              </TableRow>
              <TableEmpty
                v-if="!data.clients.items.length"
                :colspan="6"
              >
                <p>No customers match these filters.</p>
                <Button
                  variant="outline"
                  size="sm"
                  class="mt-3"
                  @click="resetFilters"
                >
                  Clear filters
                </Button>
              </TableEmpty>
            </TableBody>
          </Table>
        </CardContent>
        <CardFooter class="flex flex-wrap items-center justify-between gap-3">
          <span class="text-muted-foreground text-xs">{{ data.clients.total ? offset + 1 : 0 }}–{{ Math.min(offset + pageSize, data.clients.total) }} of {{ number(data.clients.total) }} customers</span>
          <div class="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              :disabled="offset === 0 || loading"
              @click="changePage(-1)"
            >
              <IconChevronLeft /> Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              :disabled="offset + pageSize >= data.clients.total || loading"
              @click="changePage(1)"
            >
              Next <IconChevronRight />
            </Button>
          </div>
        </CardFooter>
      </Card>
      <p class="text-muted-foreground text-xs leading-relaxed">
        All customer data is synthetic. Observed profiles describe transaction signals, not confirmed life situations. Ads and AI profiles come only from saved analyses. Refresh after running a workflow to see its results.
      </p>
    </div>
  </div>
</template>
