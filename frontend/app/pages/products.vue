<script setup lang="ts">
import { IconLoader2, IconSearch } from '@tabler/icons-vue'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableEmpty, TableHead, TableHeader, TableRow } from '@/components/ui/table'
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
  <div class="flex flex-col gap-4 md:gap-6">
    <Card>
      <CardHeader class="flex flex-col gap-2 sm:flex-row sm:items-center">
        <div class="grid flex-1 gap-1">
          <CardTitle>Product catalogue</CardTitle>
          <CardDescription>Product descriptions used to match observed client needs with relevant offers.</CardDescription>
        </div>
        <Badge variant="outline">
          {{ filtered.length }} of {{ products.length }} products
        </Badge>
      </CardHeader>
      <div class="px-4">
        <div class="flex max-w-sm flex-col gap-1.5">
          <label
            for="product-search"
            class="text-muted-foreground text-xs font-medium"
          >Search</label>
          <div class="relative">
            <IconSearch class="text-muted-foreground pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2" />
            <Input
              id="product-search"
              v-model="search"
              placeholder="Product name or description…"
              class="pl-8"
            />
          </div>
        </div>
      </div>
      <CardContent>
        <div
          v-if="loading"
          class="text-muted-foreground flex items-center justify-center gap-2 py-12 text-sm"
        >
          <IconLoader2 class="size-4 animate-spin" /> Loading products…
        </div>
        <p
          v-else-if="error"
          role="alert"
          class="text-destructive py-6 text-sm"
        >
          {{ error }}
          <Button
            class="ml-3"
            variant="outline"
            size="sm"
            @click="load"
          >
            Retry
          </Button>
        </p>
        <Table v-else>
          <TableHeader>
            <TableRow>
              <TableHead class="w-1/3">
                Product
              </TableHead>
              <TableHead>Description</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow
              v-for="product in filtered"
              :key="product.id"
            >
              <TableCell class="align-top whitespace-normal">
                <div class="font-medium">
                  {{ product.name }}
                </div>
                <div class="text-muted-foreground mt-1 text-xs">
                  {{ product.id }}
                </div>
              </TableCell>
              <TableCell class="text-muted-foreground min-w-64 whitespace-normal">
                {{ product.description }}
              </TableCell>
            </TableRow>
            <TableEmpty
              v-if="!filtered.length"
              :colspan="2"
            >
              No products match your search.
            </TableEmpty>
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  </div>
</template>
