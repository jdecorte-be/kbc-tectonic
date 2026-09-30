<script setup lang="ts">
import { IconArrowUpRight, IconChevronLeft, IconChevronRight, IconLoader2, IconSearch, IconUsers } from '@tabler/icons-vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { countryName, errorMessage, euros, number, type ClientSummary } from '@/lib/api'

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
  <div class="flex flex-col gap-6">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="text-primary mb-2 text-[10px] font-semibold tracking-[0.2em] uppercase">
          The evidence behind every decision
        </p><h1 class="text-3xl font-semibold tracking-tight">
          Synthetic clients
        </h1><p class="text-muted-foreground mt-2 text-sm">
          Explore generated banking histories and run the complete workflow for any client.
        </p>
      </div><Badge
        variant="outline"
        class="gap-2 py-2"
      >
        <IconUsers class="text-primary size-4" /> {{ number(total) }} clients
      </Badge>
    </div>
    <section class="bg-card overflow-hidden rounded-xl border">
      <div class="border-b p-5">
        <div class="relative max-w-sm">
          <IconSearch class="text-muted-foreground absolute top-2.5 left-3 size-4" /><Input
            v-model="search"
            placeholder="Search by name, client ID or city…"
            aria-label="Search clients"
            class="h-9 pl-9"
          />
        </div>
      </div>
      <p
        v-if="error"
        role="alert"
        class="text-destructive p-5 text-sm"
      >
        {{ error }}<Button
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
        class="text-muted-foreground flex items-center justify-center gap-2 p-12 text-sm"
      >
        <IconLoader2 class="size-4 animate-spin" /> Loading clients…
      </div>
      <div
        v-else
        class="overflow-x-auto"
      >
        <table class="w-full text-left text-sm">
          <thead class="bg-muted/30 text-muted-foreground text-xs">
            <tr>
              <th class="px-5 py-3 font-normal">
                Client
              </th><th class="px-4 py-3 font-normal">
                Location
              </th><th class="px-4 py-3 text-right font-normal">
                Balance
              </th><th class="px-4 py-3 text-right font-normal">
                Transactions
              </th><th class="px-4 py-3 font-normal">
                Personalization
              </th><th class="px-5 py-3 text-right font-normal">
                Workflow
              </th>
            </tr>
          </thead><tbody class="divide-y">
            <tr
              v-for="client in clients"
              :key="client.id"
              class="hover:bg-muted/25"
            >
              <td class="px-5 py-4">
                <NuxtLink
                  :to="`/client/${client.id}`"
                  class="font-medium hover:underline"
                >{{ client.name }}</NuxtLink><span class="text-muted-foreground mt-1 block font-mono text-[10px]">{{ client.id }} · {{ client.age }} years</span>
              </td><td class="px-4 py-4 text-xs">
                {{ client.city }}<span class="text-muted-foreground mt-1 block">{{ countryName(client.country) }}</span>
              </td><td class="px-4 py-4 text-right whitespace-nowrap tabular-nums">
                {{ euros(client.balance) }}
              </td><td class="px-4 py-4 text-right tabular-nums">
                {{ client.transaction_count }}
              </td><td class="px-4 py-4">
                <Badge
                  :variant="client.personalization_allowed ? 'secondary' : 'outline'"
                  class="text-[10px]"
                >
                  {{ client.personalization_allowed ? 'Allowed' : 'Declined' }}
                </Badge>
              </td><td class="px-5 py-4 text-right">
                <Button
                  as-child
                  variant="ghost"
                  size="sm"
                >
                  <NuxtLink :to="`/client/${client.id}`">Analyze <IconArrowUpRight class="size-3.5" /></NuxtLink>
                </Button>
              </td>
            </tr><tr v-if="!clients.length">
              <td
                colspan="6"
                class="text-muted-foreground p-12 text-center"
              >
                No clients match your search.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="text-muted-foreground flex items-center justify-between border-t px-5 py-3 text-xs">
        <span>{{ total ? offset + 1 : 0 }}–{{ Math.min(offset + 30, total) }} of {{ number(total) }} clients</span><div class="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            :disabled="offset === 0 || loading"
            @click="next(-1)"
          >
            <IconChevronLeft class="size-3.5" /> Previous
          </Button><Button
            variant="ghost"
            size="sm"
            :disabled="offset + 30 >= total || loading"
            @click="next(1)"
          >
            Next <IconChevronRight class="size-3.5" />
          </Button>
        </div>
      </div>
    </section>
    <p class="text-muted-foreground text-xs">
      All customers, transactions, balances and commercial preferences are synthetic. Generator scenario labels are excluded from the profiling evidence.
    </p>
  </div>
</template>
