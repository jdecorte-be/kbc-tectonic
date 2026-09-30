<script setup lang="ts">
import ClientTable from '@/components/ClientTable.vue'
import { primaryProfile } from '@/lib/profileColor'
import type { Client } from '@/types/api'

definePageMeta({ title: 'Clients' })

const clients = await useClients()
const flagged = computed(() => clients.value.filter(c => c.change && c.change.severity !== 'info').length)
const multi = computed(() => clients.value.filter(c => c.profiles.length > 1).length)
const avgConf = computed(() => clients.value.length ? Math.round(clients.value.reduce((a, c) => a + primaryProfile(c).confidence, 0) / clients.value.length) : 0)

const stats = computed(() => [
  { label: 'Clients', value: clients.value.length },
  { label: 'Need attention', value: flagged.value },
  { label: 'Multiple profiles', value: multi.value },
  { label: 'Avg. confidence', value: `${avgConf.value}%` }
])

const open = (c: Client) => navigateTo(`/client/${c.id}`)
</script>

<template>
  <div class="flex flex-col gap-4 md:gap-6">
    <div class="grid grid-cols-2 gap-4 px-4 lg:grid-cols-4 lg:px-6">
      <div
        v-for="s in stats"
        :key="s.label"
        class="rounded-xl border p-4"
      >
        <div class="text-muted-foreground text-sm">
          {{ s.label }}
        </div>
        <div class="text-2xl font-semibold tabular-nums">
          {{ s.value }}
        </div>
      </div>
    </div>
    <div class="px-4 lg:px-6">
      <ClientTable @select="open" />
    </div>
  </div>
</template>
