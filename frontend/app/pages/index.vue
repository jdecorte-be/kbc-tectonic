<script setup lang="ts">
import ClientDetailSheet from '@/components/ClientDetailSheet.vue'
import ClientTable from '@/components/ClientTable.vue'
import HabitAlerts from '@/components/HabitAlerts.vue'
import HabitTrendChart from '@/components/HabitTrendChart.vue'
import SectionCards from '@/components/SectionCards.vue'
import SegmentDistribution from '@/components/SegmentDistribution.vue'
import WeekdayRhythm from '@/components/WeekdayRhythm.vue'
import type { Client } from '@/data/mock'

definePageMeta({ title: 'Overview' })

const selected = ref<Client | null>(null)
const open = ref(false)
const select = (c: Client) => {
  selected.value = c
  open.value = true
}
</script>

<template>
  <div class="flex flex-col gap-4 md:gap-6">
    <SectionCards />
    <div class="grid gap-4 px-4 lg:px-6 @3xl/main:grid-cols-3">
      <div class="flex flex-col gap-4 @3xl/main:col-span-2">
        <HabitTrendChart />
        <WeekdayRhythm />
      </div>
      <div class="flex flex-col gap-4">
        <SegmentDistribution />
        <HabitAlerts @select="select" />
      </div>
    </div>
    <div class="px-4 lg:px-6">
      <ClientTable @select="select" />
    </div>
    <ClientDetailSheet
      v-model:open="open"
      :client="selected"
    />
  </div>
</template>
