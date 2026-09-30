<script setup lang="ts">
import { IconArrowUpRight, IconChevronLeft, IconChevronRight, IconLoader2, IconSearch, IconUsers } from '@tabler/icons-vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableEmpty, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { ageLabel, countryName, errorMessage, euros, number, type ClientSummary } from '@/lib/api'

definePageMeta({ title: 'Synthetic clients' })
const api = useKbcApi()
const clients = ref<ClientSummary[]>([])
const total = ref(0)
const search = ref('')
const offset = ref(0)
const loading = ref(true)
const error = ref('')
let requestId = 0
let debounce: ReturnType<typeof setTimeout> | undefined
async function load() {
  const id = ++requestId
  loading.value = true
  error.value = ''
  try {
    const response = await api.clients(search.value, 30, offset.value)
    if (id === requestId) {
      clients.value = response.items
      total.value = response.total
    }
  } catch (cause) {
    if (id === requestId)
      error.value = errorMessage(cause)
  } finally {
    if (id === requestId)
      loading.value = false
  }
}
function next(direction: number) {
  offset.value = Math.max(0, offset.value + direction * 30)
  void load()
}
watch(search, () => {
  clearTimeout(debounce)
  debounce = setTimeout(() => {
    offset.value = 0
    void load()
  }, 250)
})
onMounted(load)
onBeforeUnmount(() => {
  clearTimeout(debounce)
  ++requestId
})
</script>

<template>
  <div class="flex flex-col gap-4 md:gap-6">
    <Card>
      <CardHeader class="flex flex-col gap-2 sm:flex-row sm:items-center">
        <div class="grid flex-1 gap-1">
          <CardTitle>Synthetic clients</CardTitle>
          <CardDescription>Select a client to inspect their banking history and run the profiling workflow.</CardDescription>
        </div>
        <Badge variant="outline">
          <IconUsers /> {{ number(total) }} clients
        </Badge>
      </CardHeader>
      <div class="px-4">
        <div class="flex max-w-sm flex-col gap-1.5">
          <label
            for="client-search"
            class="text-muted-foreground text-xs font-medium"
          >Search</label>
          <div class="relative">
            <IconSearch class="text-muted-foreground pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2" />
            <Input
              id="client-search"
              v-model="search"
              placeholder="Name, client ID or city…"
              class="pl-8"
            />
          </div>
        </div>
      </div>
      <CardContent>
        <p
          v-if="error"
          role="alert"
          class="text-destructive py-6 text-sm"
        >
          {{ error }}
          <Button
            variant="outline"
            size="sm"
            class="ml-3"
            @click="load"
          >
            Retry
          </Button>
        </p>
        <div
          v-else-if="loading"
          class="text-muted-foreground flex items-center justify-center gap-2 py-12 text-sm"
        >
          <IconLoader2 class="size-4 animate-spin" /> Loading clients…
        </div>
        <Table v-else>
          <TableHeader>
            <TableRow>
              <TableHead>Client</TableHead>
              <TableHead>Location</TableHead>
              <TableHead class="text-right">
                Balance
              </TableHead>
              <TableHead class="text-right">
                Transactions
              </TableHead>
              <TableHead>Personalization</TableHead>
              <TableHead class="text-right">
                Workflow
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow
              v-for="client in clients"
              :key="client.id"
            >
              <TableCell>
                <NuxtLink
                  :to="`/client/${client.id}`"
                  class="font-medium hover:underline"
                >
                  {{ client.name }}
                </NuxtLink>
                <div class="text-muted-foreground text-xs">
                  {{ client.id }} · {{ ageLabel(client.age) }}
                </div>
              </TableCell>
              <TableCell>
                {{ client.city }}
                <div class="text-muted-foreground text-xs">
                  {{ countryName(client.country) }}
                </div>
              </TableCell>
              <TableCell class="text-right tabular-nums">
                {{ euros(client.balance) }}
              </TableCell>
              <TableCell class="text-right tabular-nums">
                {{ number(client.transaction_count) }}
              </TableCell>
              <TableCell>
                <Badge
                  variant="outline"
                  :class="!client.personalization_allowed && 'text-muted-foreground'"
                >
                  {{ client.personalization_allowed ? 'Allowed' : 'Declined' }}
                </Badge>
              </TableCell>
              <TableCell class="text-right">
                <Button
                  as-child
                  variant="ghost"
                  size="sm"
                >
                  <NuxtLink :to="`/client/${client.id}`">Analyze <IconArrowUpRight /></NuxtLink>
                </Button>
              </TableCell>
            </TableRow>
            <TableEmpty
              v-if="!clients.length"
              :colspan="6"
            >
              No clients match your search.
            </TableEmpty>
          </TableBody>
        </Table>
      </CardContent>
      <CardFooter class="flex flex-wrap justify-between gap-3">
        <span class="text-muted-foreground text-xs">{{ total ? offset + 1 : 0 }}–{{ Math.min(offset + 30, total) }} of {{ number(total) }} clients</span>
        <div class="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            :disabled="offset === 0 || loading"
            @click="next(-1)"
          >
            <IconChevronLeft /> Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            :disabled="offset + 30 >= total || loading"
            @click="next(1)"
          >
            Next <IconChevronRight />
          </Button>
        </div>
      </CardFooter>
    </Card>
    <p class="text-muted-foreground text-xs">
      All clients, transactions, balances and commercial preferences are synthetic. Generator scenario labels are excluded from the profiling evidence.
    </p>
  </div>
</template>
