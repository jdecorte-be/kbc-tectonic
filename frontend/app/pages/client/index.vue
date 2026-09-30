<script setup lang="ts">
import ClientTable from '@/components/ClientTable.vue'
import { clients, primaryProfile } from '@/data/mock'
import type { Client } from '@/data/mock'

definePageMeta({ title: 'Clients' })

const flagged = clients.filter(c => c.change && c.change.severity !== 'info').length
const multi = clients.filter(c => c.profiles.length > 1).length
const avgConf = Math.round(clients.reduce((a, c) => a + primaryProfile(c).confidence, 0) / clients.length)

const stats = [
  { label: 'Clients', value: clients.length },
  { label: 'Need attention', value: flagged },
  { label: 'Multiple profiles', value: multi },
  { label: 'Avg. confidence', value: `${avgConf}%` }
]

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
