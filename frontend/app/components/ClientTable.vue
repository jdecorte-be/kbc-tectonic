<script setup lang="ts">
import { IconTrendingDown, IconTrendingUp } from '@tabler/icons-vue'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableEmpty, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { PROFILES, PROFILE_IDS, clients, primaryProfile } from '@/data/mock'
import type { Client } from '@/data/mock'
import { ageLabel } from '@/lib/api'

const emit = defineEmits<{ select: [client: Client] }>()

const query = ref('')
const profile = ref('all')

const rows = computed(() =>
  clients.filter(c =>
    c.name.toLowerCase().includes(query.value.toLowerCase())
    && (profile.value === 'all' || c.profiles.some(p => p.id === profile.value))))

const trend = (c: Client) => {
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
      <div class="flex gap-2">
        <Input
          v-model="query"
          placeholder="Search client…"
          class="w-44"
        />
        <Select v-model="profile">
          <SelectTrigger class="w-44">
            <SelectValue placeholder="All profiles" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">
              All profiles
            </SelectItem>
            <SelectItem
              v-for="id in PROFILE_IDS"
              :key="id"
              :value="id"
            >
              {{ PROFILES[id].label }}
            </SelectItem>
          </SelectContent>
        </Select>
      </div>
    </CardHeader>
    <CardContent>
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
                {{ ageLabel(c.age) }}
              </div>
            </TableCell>
            <TableCell>
              <div class="flex flex-wrap gap-1">
                <Badge
                  v-for="p in c.profiles"
                  :key="p.id"
                  :variant="p === c.profiles[0] ? 'default' : 'outline'"
                >
                  {{ PROFILES[p.id].label }} {{ p.confidence }}%
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
            <TableCell>{{ PROFILES[primaryProfile(c).id].offer }}</TableCell>
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
