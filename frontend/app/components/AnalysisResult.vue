<script setup lang="ts">
import { IconArrowUpRight, IconCheck, IconClock, IconEyeOff, IconFingerprint, IconInfoCircle, IconSparkles } from '@tabler/icons-vue'
import { Badge } from '@/components/ui/badge'
import { confidence, dollars, duration, number, statusLabels, type Analysis } from '@/lib/api'

defineProps<{ analysis: Analysis, showClient?: boolean }>()
const stageLabel = (name: string) => ({ facts: 'Read customer data', consent: 'Consent', profile: 'Jev profiling', profiling: 'Jev profiling', products: 'Product selection', matching: 'Product selection', advertising: 'Ad generation', recommendations: 'Recommendations', eligibility: 'Eligibility', validation: 'Validation' }[name] ?? name)
</script>

<template>
  <section
    class="flex flex-col gap-5"
    aria-live="polite"
  >
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p class="text-primary mb-1 text-[10px] font-semibold tracking-[0.18em] uppercase">
          Workflow result
        </p><h2 class="text-xl font-semibold">
          {{ showClient ? analysis.client.name : 'From transaction history to relevant offers' }}
        </h2>
      </div>
      <Badge
        :variant="analysis.status === 'recommended' ? 'default' : analysis.status === 'error' ? 'destructive' : 'secondary'"
        class="px-3 py-1.5"
      >
        {{ statusLabels[analysis.status] }}
      </Badge>
    </div>

    <div class="bg-card grid gap-5 rounded-xl border p-5 lg:grid-cols-[1fr_280px]">
      <div class="flex gap-3">
        <div class="bg-primary/10 text-primary flex size-10 shrink-0 items-center justify-center rounded-lg">
          <IconFingerprint class="size-5" />
        </div><div>
          <h3 class="mb-2 text-sm font-semibold">
            Observed situation
          </h3><p class="text-muted-foreground text-sm leading-relaxed">
            {{ analysis.summary }}
          </p><p
            v-if="analysis.error"
            class="text-destructive mt-2 text-sm"
          >
            {{ analysis.error }}
          </p>
        </div>
      </div>
      <div class="grid grid-cols-2 gap-x-4 gap-y-3 border-t pt-4 text-xs lg:border-t-0 lg:border-l lg:pt-0 lg:pl-5">
        <div><span class="text-muted-foreground block">Processing time</span><span class="mt-1 block text-sm font-medium tabular-nums">{{ duration(analysis.metrics.duration_ms) }}</span></div><div><span class="text-muted-foreground block">Estimated cost</span><span class="mt-1 block text-sm font-medium tabular-nums">{{ dollars(analysis.metrics.estimated_cost_usd) }}</span></div><div><span class="text-muted-foreground block">Provider calls</span><span class="mt-1 block font-medium">{{ analysis.metrics.api_calls }}</span></div><div><span class="text-muted-foreground block">Input / output tokens</span><span class="mt-1 block font-medium tabular-nums">{{ number(analysis.metrics.input_tokens) }} / {{ number(analysis.metrics.output_tokens) }}</span></div>
      </div>
    </div>

    <div
      v-if="analysis.category"
      class="border-primary/25 bg-primary/5 flex flex-wrap items-start gap-4 rounded-xl border p-5"
    >
      <div class="flex-1">
        <p class="text-primary mb-2 text-[10px] font-semibold tracking-[0.16em] uppercase">
          Customer category
        </p><div class="flex flex-wrap items-center gap-2">
          <h3 class="text-lg font-semibold">
            {{ analysis.category.label }}
          </h3><Badge
            v-if="analysis.category.source === 'openai'"
            variant="outline"
            class="text-primary gap-1 text-[9px]"
          >
            <IconSparkles class="size-3" /> {{ analysis.category.created ? 'New category learned by OpenAI' : 'Verified by OpenAI' }}
          </Badge><Badge
            v-else
            variant="outline"
            class="text-[9px]"
          >
            {{ analysis.category.source === 'jev' ? 'Selected by Jev' : 'Unknown · insufficient evidence' }}
          </Badge>
        </div><ul
          v-if="analysis.category.evidence.length"
          class="text-muted-foreground mt-3 space-y-1.5 text-xs leading-relaxed"
        >
          <li
            v-for="item in analysis.category.evidence"
            :key="item"
          >
            {{ item }}
          </li>
        </ul><p
          v-if="analysis.category.created"
          class="text-primary mt-3 text-xs"
        >
          Saved to the category registry and available as a Jev choice for the next client.
        </p>
      </div><span class="text-primary text-sm font-semibold tabular-nums">{{ confidence(analysis.category.confidence) }} confidence</span>
    </div>

    <div
      v-if="analysis.profiles.length"
      class="grid gap-4 md:grid-cols-2 xl:grid-cols-3"
    >
      <article
        v-for="profile in analysis.profiles"
        :key="profile.id"
        class="bg-card rounded-xl border p-5"
      >
        <div class="mb-3 flex items-center justify-between gap-3">
          <h3 class="font-medium">
            {{ profile.label }}
          </h3><span class="text-primary text-sm font-semibold tabular-nums">{{ confidence(profile.confidence) }}</span>
        </div>
        <div class="bg-muted mb-3 h-1 overflow-hidden rounded-full">
          <div
            class="bg-primary h-full rounded-full"
            :style="{ width: confidence(profile.confidence) }"
          />
        </div>
        <p class="text-muted-foreground mb-3 text-[10px] tracking-wide uppercase">
          Model confidence · observed evidence
        </p>
        <ul class="space-y-2">
          <li
            v-for="evidence in profile.evidence"
            :key="evidence"
            class="text-muted-foreground flex gap-2 text-xs leading-relaxed"
          >
            <IconCheck class="text-primary mt-0.5 size-3.5 shrink-0" /><span>{{ evidence }}</span>
          </li>
        </ul>
      </article>
    </div>

    <div v-if="analysis.ads.length">
      <div class="mb-4 flex flex-wrap items-end justify-between gap-2">
        <h3 class="flex items-center gap-2 text-base font-semibold">
          <IconSparkles class="text-primary size-4" /> Relevant advertisements <span class="text-muted-foreground font-normal">({{ analysis.ads.length }})</span>
        </h3><span class="text-muted-foreground text-xs">{{ analysis.products_evaluated }} products evaluated · demo previews</span>
      </div>
      <div class="grid gap-4 lg:grid-cols-2">
        <article
          v-for="(ad, index) in analysis.ads"
          :key="ad.product_id"
          class="bg-card overflow-hidden rounded-xl border"
        >
          <div class="from-primary/15 to-card relative min-h-52 bg-gradient-to-br p-6">
            <div class="mb-7 flex items-center justify-between">
              <span class="text-primary text-[10px] font-semibold tracking-[0.2em] uppercase">KBC · for you</span><span class="border-primary/20 text-primary rounded-full border px-2 py-1 text-[10px]">{{ ad.product_name }}</span>
            </div>
            <div class="max-w-[90%]">
              <h4 class="mb-3 text-2xl leading-tight font-semibold tracking-tight">
                {{ ad.title }}
              </h4><p class="text-muted-foreground text-sm leading-relaxed">
                {{ ad.body }}
              </p>
            </div>
            <IconArrowUpRight class="text-primary/40 absolute right-5 bottom-5 size-8" />
            <span class="text-primary/20 absolute right-5 top-16 text-6xl font-semibold">0{{ index + 1 }}</span>
          </div>
          <div class="border-t p-5">
            <div class="mb-2 flex items-center justify-between">
              <h5 class="text-xs font-medium">
                Why this offer?
              </h5><Badge
                variant="outline"
                class="text-primary text-[10px]"
              >
                {{ confidence(ad.confidence) }} confidence
              </Badge>
            </div><p class="text-muted-foreground text-xs leading-relaxed">
              {{ ad.reason }}
            </p><details
              v-if="ad.evidence.length"
              class="mt-3"
            >
              <summary class="text-primary cursor-pointer text-xs">
                View supporting evidence
              </summary><ul class="text-muted-foreground mt-3 space-y-2 text-xs leading-relaxed">
                <li
                  v-for="evidence in ad.evidence"
                  :key="evidence"
                >
                  {{ evidence }}
                </li>
              </ul>
            </details>
          </div>
        </article>
      </div>
    </div>
    <div
      v-else
      class="bg-muted/25 flex flex-col items-center rounded-xl border border-dashed px-6 py-9 text-center"
    >
      <div class="bg-muted text-muted-foreground mb-4 rounded-full p-3">
        <IconEyeOff class="size-6" />
      </div>
      <h3 class="mb-2 text-lg font-medium">
        {{ analysis.status === 'opt_out' ? 'The client’s choice is respected' : analysis.status === 'error' ? 'The workflow could not complete' : 'Sometimes, the right offer is no offer' }}
      </h3>
      <p class="text-muted-foreground max-w-xl text-sm leading-relaxed">
        {{ analysis.status === 'opt_out' ? 'Personalization is disabled for this client. No advertising was generated.' : analysis.status === 'error' ? 'This failure is counted separately from deliberate decisions to withhold a recommendation.' : 'No advertisement was selected. The workflow abstains when evidence is insufficient or no product fits the observed situation.' }}
      </p>
    </div>

    <div
      v-if="analysis.missing_information.length"
      class="bg-muted/30 flex gap-3 rounded-xl border p-4"
    >
      <IconInfoCircle class="text-muted-foreground mt-0.5 size-4 shrink-0" /><div>
        <h3 class="mb-2 text-sm font-medium">
          What we still need to know
        </h3><ul class="text-muted-foreground space-y-1.5 text-xs leading-relaxed">
          <li
            v-for="information in analysis.missing_information"
            :key="information"
          >
            {{ information }}
          </li>
        </ul>
      </div>
    </div>
    <details class="rounded-xl border p-4">
      <summary class="text-muted-foreground flex cursor-pointer items-center gap-2 text-xs">
        <IconClock class="size-4" /> Execution details and cost measurement
      </summary><div class="mt-4 grid gap-3 sm:grid-cols-2">
        <div
          v-for="(stage, index) in analysis.stages"
          :key="`${stage.name}-${index}`"
          class="bg-muted/25 rounded-lg p-3"
        >
          <div class="flex items-center justify-between gap-2 text-xs font-medium">
            <span>{{ stageLabel(stage.name) }} · {{ stage.status }}</span><span class="text-muted-foreground shrink-0 tabular-nums">{{ duration(stage.duration_ms) }}</span>
          </div><p class="text-muted-foreground mt-2 text-xs leading-relaxed">
            {{ stage.detail }}
          </p>
        </div>
      </div><div
        v-if="analysis.metrics.providers"
        class="mt-4 grid gap-2 sm:grid-cols-2"
      >
        <div
          v-for="(provider, name) in analysis.metrics.providers"
          :key="name"
          class="bg-muted/30 rounded-lg p-3 text-xs"
        >
          <p class="mb-2 font-medium uppercase">
            {{ name }}
          </p><p class="text-muted-foreground">
            {{ provider.api_calls }} calls · {{ number(provider.input_tokens) }} input / {{ number(provider.output_tokens) }} output tokens · {{ dollars(provider.estimated_cost_usd) }}
          </p>
        </div>
      </div><p class="text-muted-foreground mt-4 text-xs">
        {{ analysis.metrics.usage_source === 'provider' ? 'Token usage reported by the provider.' : analysis.metrics.usage_source === 'estimated' ? 'Token usage estimated from the exchanged data.' : 'No Jev usage recorded.' }} The displayed cost is an estimate calculated using the configured rates.
      </p>
    </details>
  </section>
</template>
