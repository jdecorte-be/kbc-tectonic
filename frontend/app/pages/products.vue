<script setup lang="ts">
import { IconGift, IconLoader2, IconSearch } from '@tabler/icons-vue'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { errorMessage } from '@/lib/api'

definePageMeta({ title: 'Product catalogue' })
const api = useKbcApi()
const products = ref<Awaited<ReturnType<typeof api.products>>['items']>([])
const loading = ref(true)
const error = ref('')
const search = ref('')
const filtered = computed(() => products.value.filter(product => `${product.name} ${product.description}`.toLowerCase().includes(search.value.toLowerCase())))
async function load() {
  loading.value = true
  error.value = ''
  try {
    products.value = (await api.products()).items
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
    <div>
      <p class="text-primary mb-2 text-[10px] font-semibold tracking-[0.2em] uppercase">
        Recommendations grounded in the catalogue
      </p><h1 class="text-3xl font-semibold tracking-tight">
        Product catalogue
      </h1><p class="text-muted-foreground mt-2 max-w-2xl text-sm leading-relaxed">
        The workflow compares observed customer needs with these product descriptions. Only relevant products can become an advertisement.
      </p>
    </div>
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="relative w-full max-w-sm">
        <IconSearch class="text-muted-foreground absolute top-2.5 left-3 size-4" /><Input
          v-model="search"
          placeholder="Search products…"
          aria-label="Search products"
          class="h-9 pl-9"
        />
      </div><Badge variant="outline">
        {{ products.length }} products
      </Badge>
    </div>
    <div
      v-if="loading"
      class="text-muted-foreground flex items-center justify-center gap-2 p-12 text-sm"
    >
      <IconLoader2 class="size-4 animate-spin" /> Loading products…
    </div>
    <div
      v-else-if="error"
      role="alert"
      class="text-destructive rounded-xl border p-5 text-sm"
    >
      {{ error }}<Button
        class="ml-3"
        variant="outline"
        size="sm"
        @click="load"
      >
        Retry
      </Button>
    </div>
    <div
      v-else
      class="grid gap-4 md:grid-cols-2 xl:grid-cols-3"
    >
      <article
        v-for="product in filtered"
        :key="product.id"
        class="bg-card rounded-xl border p-5"
      >
        <div class="mb-5 flex items-center justify-between gap-2">
          <span class="bg-primary/10 text-primary rounded-lg p-2.5"><IconGift class="size-5" /></span><span class="text-muted-foreground font-mono text-[9px]">{{ product.id }}</span>
        </div><h2 class="mb-3 font-semibold">
          {{ product.name }}
        </h2><p class="text-muted-foreground text-xs leading-relaxed">
          {{ product.description }}
        </p>
      </article><p
        v-if="!filtered.length"
        class="text-muted-foreground py-8 text-sm"
      >
        No products match your search.
      </p>
    </div>
  </div>
</template>
