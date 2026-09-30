<script setup lang="ts">
import { IconSearch, IconTrendingDown, IconTrendingUp, IconX } from '@tabler/icons-vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableEmpty, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { primaryProfile } from '@/lib/profileColor'
import { PROFILE_IDS } from '@/types/api'
import type { Client } from '@/types/api'

const emit = defineEmits<{ select: [client: Client] }>()

const clients = await useClients()
const profiles = await useProfiles()
const query = ref('')

interface FilterDef {
  key: string
  label: string
  all: string
  options: { value: string, label: string }[]
}

const filters: FilterDef[] = [
  { key: 'profile', label: 'Profile', all: 'All profiles', options: PROFILE_IDS.map(id => ({ value: id, label: profiles.value[id].label })) },
  { key: 'habit', label: 'Top habit', all: 'All habits', options: [...new Set(clients.value.map(c => c.topHabit))].sort().map(h => ({ value: h, label: h })) },
  {
    key: 'change',
    label: 'Habit change',
    all: 'Any change',
    options: [
      { value: 'stable', label: 'Stable (no change)' },
      { value: 'info', label: 'Info' },
      { value: 'watch', label: 'Watch' },
      { value: 'alert', label: 'Alert' }
    ]
  },
  {
    key: 'age',
    label: 'Age',
    all: 'Any age',
    options: [
      { value: '0-25', label: 'Under 26' },
      { value: '26-40', label: '26–40' },
      { value: '41-60', label: '41–60' },
      { value: '61-200', label: '61+' }
    ]
  },
  {
    key: 'spend',
    label: 'Spend trend',
    all: 'Any trend',
    options: [{ value: 'up', label: 'Spending up' }, { value: 'down', label: 'Spending down' }]
  },
  {
    key: 'confidence',
    label: 'Confidence',
    all: 'Any confidence',
    options: [{ value: '60', label: '≥ 60%' }, { value: '75', label: '≥ 75%' }, { value: '90', label: '≥ 90%' }]
  }
]

const values = reactive<Record<string, string>>(Object.fromEntries(filters.map(f => [f.key, 'all'])))

const labelOf = (f: FilterDef) => f.options.find(o => o.value === values[f.key])?.label
const activeChips = computed(() => filters.filter(f => values[f.key] !== 'all'))
const activeFilters = computed(() => activeChips.value.length + (query.value ? 1 : 0))

const reset = () => {
  query.value = ''
  for (const f of filters) values[f.key] = 'all'
}

const rows = computed(() =>
  clients.value.filter((c) => {
    if (!c.name.toLowerCase().includes(query.value.toLowerCase())) return false
    if (values.profile !== 'all' && !c.profiles.some(p => p.id === values.profile)) return false
    if (values.habit !== 'all' && c.topHabit !== values.habit) return false
    if (values.change !== 'all' && (c.change?.severity ?? 'stable') !== values.change) return false
    if (values.age !== 'all') {
      const [lo, hi] = values.age!.split('-').map(Number) as [number, number]
      if (c.age < lo || c.age > hi) return false
    }
    if (values.spend !== 'all' && (trend(c) >= 0 ? 'up' : 'down') !== values.spend) return false
    if (values.confidence !== 'all' && primaryProfile(c).confidence < Number(values.confidence)) return false
    return true
  }))

function trend(c: Client) {
  const s = c.monthlySpend
  return Math.round(((s[s.length - 1]! - s[0]!) / s[0]!) * 100)
}
</script>

<template>
  <Card>
    <CardHeader class="flex flex-col gap-2 sm:flex-row sm:items-center">
      <div class="grid flex-1 gap-1">
        <CardTitle>Clients</CardTitle>
        <CardDescription>Click a client to see why they got a profile and what to offer</CardDescription>
      </div>
      <div class="text-muted-foreground text-sm tabular-nums sm:ml-auto">
        {{ rows.length }} of {{ clients.length }} clients
      </div>
    </CardHeader>
    <div class="flex flex-col gap-3 px-6">
      <div class="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-7">
        <div class="col-span-2 flex flex-col gap-1.5 md:col-span-4 xl:col-span-1">
          <span class="text-muted-foreground text-xs font-medium">Search</span>
          <div class="relative">
            <IconSearch class="text-muted-foreground pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2" />
            <Input
              v-model="query"
              placeholder="Client name…"
              class="pl-8"
            />
          </div>
        </div>
        <div
          v-for="f in filters"
          :key="f.key"
          class="flex flex-col gap-1.5"
        >
          <span class="text-muted-foreground text-xs font-medium">{{ f.label }}</span>
          <Select v-model="values[f.key]">
            <SelectTrigger class="w-full">
              <SelectValue :placeholder="f.all" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">
                {{ f.all }}
              </SelectItem>
              <SelectItem
                v-for="o in f.options"
                :key="o.value"
                :value="o.value"
              >
                {{ o.label }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <div
        v-if="activeFilters"
        class="flex flex-wrap items-center gap-2"
      >
        <Badge
          v-if="query"
          variant="secondary"
          class="cursor-pointer gap-1"
          @click="query = ''"
        >
          “{{ query }}” <IconX class="size-3" />
        </Badge>
        <Badge
          v-for="f in activeChips"
          :key="f.key"
          variant="secondary"
          class="cursor-pointer gap-1"
          @click="values[f.key] = 'all'"
        >
          {{ f.label }}: {{ labelOf(f) }} <IconX class="size-3" />
        </Badge>
        <Button
          variant="ghost"
          size="sm"
          class="h-6 px-2 text-xs"
          @click="reset"
        >
          Clear all
        </Button>
      </div>
    </div>
    <CardContent class="pt-2">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Client</TableHead>
            <TableHead>Profile</TableHead>
            <TableHead class="hidden md:table-cell">
              Top habit
            </TableHead>
            <TableHead class="hidden lg:table-cell text-right">
              Spend trend (6m)
            </TableHead>
            <TableHead class="hidden lg:table-cell">
              Latest habit change
            </TableHead>
            <TableHead>Suggested action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow
            v-for="c in rows"
            :key="c.id"
            class="cursor-pointer"
            @click="emit('select', c)"
          >
            <TableCell class="font-medium">
              {{ c.name }}
              <div class="text-muted-foreground text-xs">
                {{ c.age }} y
              </div>
            </TableCell>
            <TableCell>
              <div class="flex flex-wrap gap-1">
                <Badge
                  v-for="p in c.profiles"
                  :key="p.id"
                  :variant="p === c.profiles[0] ? 'default' : 'outline'"
                >
                  {{ profiles[p.id].label }} {{ p.confidence }}%
                </Badge>
              </div>
            </TableCell>
            <TableCell class="hidden md:table-cell">
              {{ c.topHabit }}
            </TableCell>
            <TableCell class="hidden lg:table-cell text-right tabular-nums">
              <span class="inline-flex items-center gap-1">
                <component
                  :is="trend(c) >= 0 ? IconTrendingUp : IconTrendingDown"
                  class="size-4"
                />
                {{ trend(c) > 0 ? '+' : '' }}{{ trend(c) }}%
              </span>
            </TableCell>
            <TableCell class="hidden max-w-64 truncate lg:table-cell">
              <template v-if="c.change">
                {{ c.change.text }}
              </template>
              <span
                v-else
                class="text-muted-foreground"
              >Stable</span>
            </TableCell>
            <TableCell>{{ profiles[primaryProfile(c).id].offer }}</TableCell>
          </TableRow>
          <TableEmpty
            v-if="!rows.length"
            :colspan="6"
          >
            No clients match.
          </TableEmpty>
        </TableBody>
      </Table>
    </CardContent>
  </Card>
</template>
