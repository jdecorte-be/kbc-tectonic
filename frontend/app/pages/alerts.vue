<script setup lang="ts">
import HabitAlerts from '@/components/HabitAlerts.vue'
import type { Client } from '@/data/mock'

definePageMeta({ title: 'Alerts' })

const open = (c: Client) => navigateTo(`/client/${c.id}`)
</script>

<template>
  <div class="px-4 lg:px-6">
    <HabitAlerts
      :limit="50"
      @select="open"
    />
  </div>
</template>
