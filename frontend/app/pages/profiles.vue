<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { profileColor } from '@/lib/profileColor'
import { PROFILE_IDS } from '@/types/api'
import type { ProfileId } from '@/types/api'

definePageMeta({ title: 'Profiles' })

const clients = await useClients()
const profiles = await useProfiles()

const filter = ref<'all' | 'core' | 'extra'>('all')
const filters = [
  { id: 'all', label: 'All' },
  { id: 'core', label: 'Core' },
  { id: 'extra', label: 'Extra' }
] as const

const all = computed(() => PROFILE_IDS.map((id) => {
  const members = clients.value
    .map(client => ({ client, confidence: client.profiles.find(p => p.id === id)?.confidence ?? 0 }))
    .filter(m => m.confidence > 0)
    .sort((a, b) => b.confidence - a.confidence)
  const avg = members.length ? Math.round(members.reduce((a, m) => a + m.confidence, 0) / members.length) : 0
  const evidence = members
    .filter(m => m.client.profiles[0]?.id === id)
    .flatMap(m => m.client.signals.map(s => ({ ...s, who: m.client.name })))
    .sort((a, b) => b.weight - a.weight)
    .slice(0, 3)
  return { ...profiles.value[id], members, avg, evidence }
}).filter(p => p.label))

const list = computed(() => all.value.filter(p => filter.value === 'all' || (filter.value === 'core') === p.core))

const selectedId = ref<ProfileId | null>(null)
const selected = computed(() => list.value.find(p => p.id === selectedId.value) ?? list.value[0])
</script>

<template>
  <div class="flex flex-col gap-4 px-4 lg:px-6">
    <div class="flex items-center justify-between gap-2">
      <p class="text-muted-foreground text-sm">
        {{ clients.length }} clients across {{ all.filter(p => p.members.length).length }} active profiles
      </p>
      <div class="flex gap-2">
        <Button
          v-for="f in filters"
          :key="f.id"
          size="sm"
          :variant="filter === f.id ? 'default' : 'outline'"
          @click="filter = f.id"
        >
          {{ f.label }}
        </Button>
      </div>
    </div>

    <div class="grid grid-cols-2 gap-3 @3xl/main:grid-cols-4">
      <button
        v-for="p in list"
        :key="p.id"
        type="button"
        :class="cn('bg-card hover:border-primary/60 flex flex-col gap-2 rounded-lg border p-3 text-left transition-colors', p.id === selected?.id && 'border-primary ring-primary/30 ring-2')"
        @click="selectedId = p.id"
      >
        <span class="flex items-center gap-2 text-sm font-medium">
          <span
            class="size-2.5 shrink-0 rounded-full"
            :style="{ backgroundColor: profileColor(p.id) }"
          />
          <span class="truncate">{{ p.label }}</span>
        </span>
        <span class="flex items-baseline justify-between">
          <span class="text-2xl font-semibold tabular-nums">{{ p.members.length }}</span>
          <span class="text-muted-foreground text-xs tabular-nums">
            {{ p.members.length ? `avg ${p.avg}%` : 'no clients' }}
          </span>
        </span>
      </button>
    </div>

    <Card v-if="selected">
      <CardHeader>
        <CardTitle class="flex items-center gap-2 text-xl">
          <span
            class="size-3 rounded-full"
            :style="{ backgroundColor: profileColor(selected.id) }"
          />
          {{ selected.label }}
          <Badge
            v-if="selected.core"
            variant="outline"
          >
            Core
          </Badge>
        </CardTitle>
        <CardDescription>{{ selected.description }}</CardDescription>
      </CardHeader>
      <CardContent class="grid gap-6 text-sm @3xl/main:grid-cols-2">
        <section class="flex flex-col gap-2">
          <h3 class="font-medium">
            Clients ({{ selected.members.length }}) · avg {{ selected.members.length ? `${selected.avg}%` : '–' }}
          </h3>
          <p
            v-if="!selected.members.length"
            class="text-muted-foreground"
          >
            No clients yet.
          </p>
          <NuxtLink
            v-for="m in selected.members"
            :key="m.client.id"
            :to="`/client/${m.client.id}`"
            class="hover:bg-muted grid gap-1 rounded-md p-2"
          >
            <div class="flex justify-between">
              <span>{{ m.client.name }}</span>
              <span class="text-muted-foreground tabular-nums">{{ m.confidence }}%</span>
            </div>
            <div class="bg-muted h-1.5 overflow-hidden rounded-full">
              <div
                class="h-full rounded-full"
                :style="{ width: `${m.confidence}%`, backgroundColor: profileColor(selected.id) }"
              />
            </div>
          </NuxtLink>
        </section>

        <section class="flex flex-col gap-5">
          <div>
            <h3 class="mb-1 font-medium">
              Signals we look for
            </h3>
            <ul class="text-muted-foreground list-inside list-disc">
              <li
                v-for="s in selected.looksFor"
                :key="s"
              >
                {{ s }}
              </li>
            </ul>
          </div>
          <div v-if="selected.evidence.length">
            <h3 class="mb-1 font-medium">
              Seen in clients
            </h3>
            <ul class="text-muted-foreground flex flex-col gap-1">
              <li
                v-for="e in selected.evidence"
                :key="e.who + e.text"
              >
                {{ e.text }} · {{ e.who }}
              </li>
            </ul>
          </div>
          <div class="bg-muted rounded-md p-3">
            <div class="text-muted-foreground text-xs">
              Suggested offer
            </div>
            <div class="text-primary font-medium">
              {{ selected.offer }}
            </div>
          </div>
        </section>
      </CardContent>
    </Card>
  </div>
</template>
