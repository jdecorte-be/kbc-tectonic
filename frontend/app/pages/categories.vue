<script setup lang="ts">
import { IconArrowRight, IconFingerprint, IconLoader2, IconRefresh, IconSparkles } from '@tabler/icons-vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { errorMessage, number } from '@/lib/api'

definePageMeta({ title: 'Category registry' })
const api = useKbcApi()
const registry = ref<Awaited<ReturnType<typeof api.categories>> | null>(null)
const loading = ref(true)
const error = ref('')
const discovered = computed(() => registry.value?.items.filter(category => category.source === 'openai').length ?? 0)
async function load() {
  loading.value = true
  error.value = ''
  try {
    registry.value = await api.categories()
  } catch (cause) {
    error.value = errorMessage(cause)
  } finally {
    loading.value = false
  }
}
onMounted(load)
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="text-primary mb-2 text-[10px] font-semibold tracking-[0.2em] uppercase">
          A vocabulary that grows with the evidence
        </p><h1 class="text-3xl font-semibold tracking-tight">
          Category registry
        </h1><p class="text-muted-foreground mt-2 max-w-2xl text-sm leading-relaxed">
          Jev selects a known category or returns Unknown. OpenAI can then infer a new category, save it and make it available to future analyses.
        </p>
      </div><Button
        variant="outline"
        size="sm"
        :disabled="loading"
        @click="load"
      >
        <IconRefresh
          class="size-3.5"
          :class="loading ? 'animate-spin' : ''"
        /> Refresh registry
      </Button>
    </div>
    <div class="bg-card flex flex-wrap items-center gap-3 rounded-xl border p-5 text-xs">
      <span class="bg-primary/10 text-primary rounded-lg px-3 py-2 font-medium">Jev classification</span><IconArrowRight class="text-muted-foreground size-4" /><span class="bg-muted rounded-lg px-3 py-2">Unknown category</span><IconArrowRight class="text-muted-foreground size-4" /><span class="bg-primary/10 text-primary rounded-lg px-3 py-2 font-medium">OpenAI discovery</span><IconArrowRight class="text-muted-foreground size-4" /><span class="bg-muted rounded-lg px-3 py-2">Saved for the next client</span>
    </div>
    <div
      v-if="error"
      role="alert"
      class="text-destructive rounded-xl border p-5 text-sm"
    >
      {{ error }}
    </div>
    <div
      v-if="loading && !registry"
      class="text-muted-foreground flex items-center justify-center gap-2 p-12 text-sm"
    >
      <IconLoader2 class="size-4 animate-spin" /> Loading category registry…
    </div>
    <template v-if="registry">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <h2 class="font-semibold">
          {{ number(registry.items.length) }} available categories
        </h2><Badge
          variant="outline"
          class="gap-1.5"
        >
          <IconSparkles class="text-primary size-3.5" /> {{ discovered }} discovered by OpenAI
        </Badge>
      </div>
      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <article
          v-for="category in registry.items"
          :key="category.id"
          class="bg-card rounded-xl border p-5"
        >
          <div class="mb-4 flex items-center justify-between gap-2">
            <IconFingerprint class="text-primary size-5" /><Badge
              :variant="category.source === 'openai' ? 'default' : 'secondary'"
              class="text-[9px]"
            >
              {{ category.source === 'openai' ? 'Learned by OpenAI' : 'Initial category' }}
            </Badge>
          </div><h3 class="mb-2 font-semibold">
            {{ category.label }}
          </h3><p class="text-muted-foreground min-h-12 text-xs leading-relaxed">
            {{ category.description }}
          </p><div class="text-muted-foreground mt-5 flex items-center justify-between border-t pt-3 text-[10px]">
            <span>{{ number(category.client_count) }} assigned clients</span><span>{{ new Date(category.created_at).toLocaleDateString('en-BE') }}</span>
          </div>
        </article>
      </div>
      <details
        v-if="registry.questions.length"
        class="bg-card rounded-xl border p-5"
      >
        <summary class="cursor-pointer text-sm font-medium">
          Classification instructions
        </summary><div class="mt-4 space-y-4">
          <div
            v-for="question in registry.questions"
            :key="question.id"
          >
            <p class="text-primary mb-2 font-mono text-[10px]">
              {{ question.id }}
            </p><p class="text-muted-foreground text-xs leading-relaxed whitespace-pre-line">
              {{ question.instructions }}
            </p>
          </div>
        </div>
      </details>
    </template>
  </div>
</template>
