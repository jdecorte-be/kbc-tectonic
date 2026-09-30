<script setup lang="ts">
import { IconClock, IconEyeOff, IconInfoCircle, IconSparkles } from '@tabler/icons-vue'
import { Badge } from '@/components/ui/badge'
import { Card, CardAction, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { confidence, dollars, duration, number, statusLabels, type Analysis } from '@/lib/api'

defineProps<{ analysis: Analysis, showClient?: boolean }>()
const stageLabel = (name: string) => ({ facts: 'Read customer data', consent: 'Consent', profile: 'Jev profiling', profiling: 'Jev profiling', products: 'Product selection', matching: 'Product selection', advertising: 'Ad generation', recommendations: 'Recommendations', eligibility: 'Eligibility', validation: 'Validation' }[name] ?? name)
</script>

<template>
  <section
    class="flex flex-col gap-4"
    aria-live="polite"
  >
    <Card>
      <CardHeader class="flex flex-wrap items-center justify-between gap-3">
        <div class="grid gap-1">
          <CardTitle>{{ showClient ? analysis.client.name : 'Analysis result' }}</CardTitle>
          <CardDescription>Observed situation and product relevance</CardDescription>
        </div>
        <Badge :variant="analysis.status === 'error' ? 'destructive' : 'outline'">
          {{ statusLabels[analysis.status] }}
        </Badge>
      </CardHeader>
      <CardContent>
        <p class="text-muted-foreground text-sm leading-relaxed">
          {{ analysis.summary }}
        </p>
        <p
          v-if="analysis.error"
          class="text-destructive mt-3 text-sm"
        >
          {{ analysis.error }}
        </p>
      </CardContent>
      <CardFooter class="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div>
          <p class="text-muted-foreground text-xs">
            Processing time
          </p>
          <p class="mt-1 font-medium tabular-nums">
            {{ duration(analysis.metrics.duration_ms) }}
          </p>
        </div>
        <div>
          <p class="text-muted-foreground text-xs">
            Estimated cost
          </p>
          <p class="mt-1 font-medium tabular-nums">
            {{ dollars(analysis.metrics.estimated_cost_usd) }}
          </p>
        </div>
        <div>
          <p class="text-muted-foreground text-xs">
            Provider calls
          </p>
          <p class="mt-1 font-medium tabular-nums">
            {{ analysis.metrics.api_calls }}
          </p>
        </div>
        <div>
          <p class="text-muted-foreground text-xs">
            Input / output tokens
          </p>
          <p class="mt-1 font-medium tabular-nums">
            {{ number(analysis.metrics.input_tokens) }} / {{ number(analysis.metrics.output_tokens) }}
          </p>
        </div>
      </CardFooter>
    </Card>

    <Card v-if="analysis.category">
      <CardHeader>
        <CardDescription>Client category</CardDescription>
        <CardTitle>{{ analysis.category.label }}</CardTitle>
        <CardAction>
          <Badge variant="outline">
            {{ confidence(analysis.category.confidence) }} confidence
          </Badge>
        </CardAction>
      </CardHeader>
      <CardContent class="grid gap-3">
        <Badge
          variant="outline"
          class="justify-self-start"
        >
          <IconSparkles v-if="analysis.category.source === 'openai'" />
          {{ analysis.category.source === 'openai' ? (analysis.category.created ? 'New category learned by OpenAI' : 'Verified by OpenAI') : analysis.category.source === 'jev' ? 'Selected by Jev' : 'Unknown · insufficient evidence' }}
        </Badge>
        <ul
          v-if="analysis.category.evidence.length"
          class="text-muted-foreground grid gap-2 text-sm"
        >
          <li
            v-for="item in analysis.category.evidence"
            :key="item"
          >
            {{ item }}
          </li>
        </ul>
      </CardContent>
      <CardFooter v-if="analysis.category.created">
        <p class="text-muted-foreground text-sm">
          Saved to the category registry and available as a Jev choice for the next client.
        </p>
      </CardFooter>
    </Card>

    <div
      v-if="analysis.profiles.length"
      class="grid gap-4 md:grid-cols-2 xl:grid-cols-3"
    >
      <Card
        v-for="profile in analysis.profiles"
        :key="profile.id"
      >
        <CardHeader>
          <CardTitle>{{ profile.label }}</CardTitle>
          <CardDescription>Why this profile</CardDescription>
          <CardAction>
            <Badge variant="outline">
              {{ confidence(profile.confidence) }}
            </Badge>
          </CardAction>
        </CardHeader>
        <CardContent class="grid gap-3">
          <div class="bg-muted h-1.5 overflow-hidden rounded-full">
            <div
              class="bg-primary h-full rounded-full"
              :style="{ width: confidence(profile.confidence) }"
            />
          </div>
          <ul class="text-muted-foreground grid gap-2 text-sm leading-relaxed">
            <li
              v-for="evidence in profile.evidence"
              :key="evidence"
            >
              {{ evidence }}
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>

    <div
      v-if="analysis.ads.length"
      class="grid gap-4"
    >
      <div class="flex flex-wrap items-center justify-between gap-2">
        <h3 class="text-base font-semibold">
          Suggested offers
        </h3>
        <span class="text-muted-foreground text-sm">{{ analysis.products_evaluated }} products evaluated · advertisement previews</span>
      </div>
      <div class="grid gap-4 lg:grid-cols-2">
        <Card
          v-for="ad in analysis.ads"
          :key="ad.product_id"
        >
          <CardHeader>
            <CardDescription>{{ ad.product_name }}</CardDescription>
            <CardTitle class="text-lg">
              {{ ad.title }}
            </CardTitle>
            <CardAction>
              <Badge variant="outline">
                KBC
              </Badge>
            </CardAction>
          </CardHeader>
          <CardContent class="grid gap-4">
            <div class="bg-primary/10 rounded-md p-3 text-sm leading-relaxed">
              {{ ad.body }}
            </div>
            <div class="grid gap-2">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <h4 class="text-sm font-medium">
                  Why this offer
                </h4>
                <Badge variant="outline">
                  {{ confidence(ad.confidence) }} confidence
                </Badge>
              </div>
              <p class="text-muted-foreground text-sm leading-relaxed">
                {{ ad.reason }}
              </p>
            </div>
          </CardContent>
          <CardFooter v-if="ad.evidence.length">
            <details class="w-full">
              <summary class="cursor-pointer text-sm font-medium">
                Supporting evidence
              </summary>
              <ul class="text-muted-foreground mt-3 grid gap-2 text-sm leading-relaxed">
                <li
                  v-for="evidence in ad.evidence"
                  :key="evidence"
                >
                  {{ evidence }}
                </li>
              </ul>
            </details>
          </CardFooter>
        </Card>
      </div>
    </div>
    <Card v-else>
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          <IconEyeOff class="text-muted-foreground size-4" />
          {{ analysis.status === 'opt_out' ? 'Personalization declined' : analysis.status === 'error' ? 'Analysis could not complete' : 'No suitable offer' }}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p class="text-muted-foreground text-sm leading-relaxed">
          {{ analysis.status === 'opt_out' ? 'Personalization is disabled for this client. No advertising was generated.' : analysis.status === 'error' ? 'This failure is counted separately from deliberate decisions to withhold a recommendation.' : 'No advertisement was selected. The workflow abstains when evidence is insufficient or no product fits the observed situation.' }}
        </p>
      </CardContent>
    </Card>

    <Card v-if="analysis.missing_information.length">
      <CardHeader>
        <CardTitle class="flex items-center gap-2">
          <IconInfoCircle class="text-muted-foreground size-4" />
          Missing information
        </CardTitle>
        <CardDescription>Limits of the available evidence</CardDescription>
      </CardHeader>
      <CardContent>
        <ul class="text-muted-foreground grid gap-2 text-sm leading-relaxed">
          <li
            v-for="information in analysis.missing_information"
            :key="information"
          >
            {{ information }}
          </li>
        </ul>
      </CardContent>
    </Card>

    <Card>
      <CardContent>
        <details>
          <summary class="flex cursor-pointer items-center gap-2 text-sm font-medium">
            <IconClock class="size-4" /> Execution details and estimated cost
          </summary>
          <Table class="mt-4">
            <TableHeader>
              <TableRow>
                <TableHead>Stage</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Detail</TableHead>
                <TableHead class="text-right">
                  Time
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow
                v-for="(stage, index) in analysis.stages"
                :key="`${stage.name}-${index}`"
              >
                <TableCell class="font-medium">
                  {{ stageLabel(stage.name) }}
                </TableCell>
                <TableCell>
                  <Badge variant="outline">
                    {{ stage.status }}
                  </Badge>
                </TableCell>
                <TableCell class="text-muted-foreground min-w-64 whitespace-normal">
                  {{ stage.detail }}
                </TableCell>
                <TableCell class="text-right tabular-nums">
                  {{ duration(stage.duration_ms) }}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
          <div
            v-if="analysis.metrics.providers"
            class="mt-4 grid gap-3 sm:grid-cols-2"
          >
            <div
              v-for="(provider, name) in analysis.metrics.providers"
              :key="name"
              class="rounded-lg border p-3"
            >
              <p class="mb-1 font-medium">
                {{ name === 'openai' ? 'OpenAI' : name === 'jev' ? 'Jev' : name }}
              </p>
              <p class="text-muted-foreground text-sm">
                {{ provider.api_calls }} calls · {{ number(provider.input_tokens) }} input / {{ number(provider.output_tokens) }} output tokens · {{ dollars(provider.estimated_cost_usd) }}
              </p>
            </div>
          </div>
          <p class="text-muted-foreground mt-4 text-xs">
            {{ analysis.metrics.usage_source === 'provider' ? 'Token usage reported by the provider.' : analysis.metrics.usage_source === 'estimated' ? 'Token usage estimated from the exchanged data.' : 'No provider usage recorded.' }} The displayed cost is an estimate calculated using the configured rates.
          </p>
        </details>
      </CardContent>
    </Card>
  </section>
</template>
