<script setup lang="ts">
import { IconArrowUpRight, IconChevronDown, IconHistory, IconLoader2, IconRefresh, IconShieldCheck, IconSparkles } from '@tabler/icons-vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { confidence, errorMessage, euros, number, statusLabels } from '@/lib/api'
import type { DashboardClient } from '@/lib/dashboard'

const props = defineProps<{
  clientId: string
  refreshKey?: number
  loadingSaved?: boolean
  running?: boolean
}>()
const emit = defineEmits<{ openAnalysis: [id: string] }>()
const api = useKbcApi()
const context = ref<DashboardClient | null>(null)
const loading = ref(true)
const error = ref('')
let requestId = 0
let mounted = false

const limitedHistory = computed(() => !!context.value && (context.value.context.observation_days < 30 || context.value.client.transaction_count < 8))
const savedStatus = computed(() => {
  const status = context.value?.analysis.status
  return !status || status === 'not_analyzed' ? 'Not analyzed' : statusLabels[status]
})
const metrics = computed(() => {
  const facts = context.value?.context
  if (!facts)
    return []
  return [
    { label: 'Monthly income', value: euros(facts.monthly_income_cents / 100), hint: 'Observed income credits average' },
    { label: 'Savings transfers', value: euros(facts.savings_cents / 100), hint: 'Across the observed period' },
    { label: 'Investment transfers', value: euros(facts.investment_cents / 100), hint: 'Across the observed period' },
    { label: 'Recurring payments', value: number(facts.recurring_payment_count), hint: 'Detected in this history' }
  ]
})

function dateLabel(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat('en-BE', { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

async function load() {
  const request = ++requestId
  loading.value = true
  error.value = ''
  context.value = null
  try {
    const response = await api.clientContext(props.clientId)
    if (request === requestId)
      context.value = response
  } catch (cause) {
    if (request === requestId)
      error.value = errorMessage(cause)
  } finally {
    if (request === requestId)
      loading.value = false
  }
}

watch(() => [props.clientId, props.refreshKey], () => {
  ++requestId
  context.value = null
  if (mounted)
    void load()
})
onMounted(() => {
  mounted = true
  void load()
})
onBeforeUnmount(() => {
  mounted = false
  ++requestId
})
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle class="flex items-center gap-2">
        <IconSparkles class="text-primary size-4" /> Client context
      </CardTitle>
      <CardDescription>Observed habits and the latest saved recommendation.</CardDescription>
      <CardAction>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Refresh client context"
          :disabled="loading"
          @click="load"
        >
          <IconRefresh :class="loading ? 'animate-spin' : ''" />
        </Button>
      </CardAction>
    </CardHeader>
    <CardContent class="grid gap-4">
      <div
        v-if="loading"
        role="status"
        class="text-muted-foreground flex items-center gap-2 py-6 text-sm"
      >
        <IconLoader2 class="size-4 animate-spin" /> Reading client context…
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
          Retry
        </Button>
      </div>
      <template v-else-if="context">
        <div class="grid gap-3">
          <div class="flex flex-wrap items-center gap-2">
            <Badge variant="outline">
              <IconShieldCheck /> {{ context.client.personalization_allowed ? 'Opted in' : 'Opted out' }}
            </Badge>
            <Badge variant="outline">
              <IconHistory /> {{ number(context.context.observation_days) }} days of history
            </Badge>
            <Badge
              v-if="limitedHistory"
              variant="secondary"
            >
              Limited history
            </Badge>
          </div>
          <p class="text-sm leading-relaxed">
            {{ context.context.summary }}
          </p>
        </div>

        <div class="grid grid-cols-2 gap-3 @4xl/main:grid-cols-4">
          <div
            v-for="metric in metrics"
            :key="metric.label"
            class="bg-muted/30 grid gap-1 rounded-lg border p-3"
          >
            <p class="text-muted-foreground text-xs">
              {{ metric.label }}
            </p>
            <p class="text-base font-semibold tabular-nums">
              {{ metric.value }}
            </p>
            <p class="text-muted-foreground text-xs">
              {{ metric.hint }}
            </p>
          </div>
        </div>

        <section class="grid gap-2">
          <h3 class="text-sm font-medium">
            Observed habits
          </h3>
          <template v-if="context.segments.length">
            <div class="flex flex-wrap gap-2">
              <Badge
                v-for="segment in context.segments"
                :key="segment.id"
                variant="secondary"
                class="bg-primary/10 text-primary"
              >
                {{ segment.label }}
              </Badge>
            </div>
            <details class="group text-sm">
              <summary class="text-muted-foreground flex cursor-pointer list-none items-center gap-1.5 py-1 text-xs hover:text-foreground [&::-webkit-details-marker]:hidden">
                <IconChevronDown class="size-3.5 transition-transform group-open:rotate-180" /> Why these habits?
              </summary>
              <div class="mt-2 grid gap-3 rounded-lg border p-3">
                <div
                  v-for="segment in context.segments"
                  :key="segment.id"
                  class="grid gap-1"
                >
                  <p class="font-medium">
                    {{ segment.label }}
                  </p>
                  <p class="text-muted-foreground text-xs leading-relaxed">
                    {{ segment.description }}
                  </p>
                  <ul class="text-muted-foreground ml-4 list-disc space-y-1 text-xs">
                    <li
                      v-for="evidence in segment.evidence"
                      :key="evidence"
                    >
                      {{ evidence }}
                    </li>
                  </ul>
                </div>
              </div>
            </details>
            <p class="text-muted-foreground text-xs">
              Based on observed transaction rules; these habits can overlap and do not replace the saved AI classification.
            </p>
          </template>
          <p
            v-else
            class="text-muted-foreground text-sm"
          >
            {{ context.client.personalization_allowed ? 'No habit has enough supporting evidence yet.' : 'Habit profiles are withheld because this client has opted out.' }}
          </p>
        </section>

        <section class="grid gap-3 border-t pt-4">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <h3 class="text-sm font-medium">
              Latest saved decision
            </h3>
            <Badge variant="outline">
              {{ savedStatus }}
            </Badge>
          </div>
          <template v-if="context.analysis.source">
            <div class="grid gap-2">
              <div class="flex flex-wrap items-center gap-2">
                <Badge
                  v-if="context.analysis.category"
                  variant="secondary"
                >
                  {{ context.analysis.category.label }}
                </Badge>
                <p class="text-muted-foreground text-xs">
                  {{ context.analysis.source === 'benchmark' ? 'Saved benchmark result' : 'Saved analysis' }}
                  <template v-if="context.analysis.created_at">
                    · <time :datetime="context.analysis.created_at">{{ dateLabel(context.analysis.created_at) }}</time>
                  </template>
                </p>
              </div>
              <p class="text-muted-foreground text-sm leading-relaxed">
                {{ context.analysis.summary }}
              </p>
            </div>
            <ul
              v-if="context.analysis.ads.length"
              class="grid gap-2"
            >
              <li
                v-for="ad in context.analysis.ads"
                :key="ad.product_id"
                class="bg-primary/5 grid gap-1.5 rounded-lg border p-3"
              >
                <div class="flex items-start justify-between gap-3">
                  <div class="grid gap-1">
                    <p class="font-medium">
                      {{ ad.title }}
                    </p>
                    <p class="text-primary text-xs">
                      {{ ad.product_name }}
                    </p>
                  </div>
                  <Badge variant="outline">
                    {{ confidence(ad.confidence) }} confidence
                  </Badge>
                </div>
                <p class="text-muted-foreground text-xs leading-relaxed">
                  {{ ad.reason }}
                </p>
              </li>
            </ul>
            <p
              v-else
              class="text-muted-foreground text-xs"
            >
              No advert selected for this client.
            </p>
            <Button
              v-if="context.analysis.source === 'analysis' && context.analysis.id"
              variant="outline"
              size="sm"
              class="justify-self-start"
              :disabled="loadingSaved || running"
              @click="emit('openAnalysis', context.analysis.id)"
            >
              <IconLoader2
                v-if="loadingSaved"
                class="animate-spin"
              />
              <IconArrowUpRight v-else />
              View saved result
            </Button>
          </template>
          <p
            v-else
            class="text-muted-foreground text-sm"
          >
            {{ context.analysis.summary || 'No saved analysis yet. Run the workflow to check relevant offers.' }}
          </p>
        </section>
      </template>
    </CardContent>
  </Card>
</template>
