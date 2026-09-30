<script setup lang="ts">
import HabitTrendChart from '@/components/HabitTrendChart.vue'
import SectionCards from '@/components/SectionCards.vue'
import SegmentDistribution from '@/components/SegmentDistribution.vue'
import WeekdayRhythm from '@/components/WeekdayRhythm.vue'

definePageMeta({ title: 'Overview' })
</script>

<template>
  <div class="flex flex-col gap-4 md:gap-6">
    <SectionCards />
    <div class="grid gap-4 px-4 lg:px-6 @3xl/main:grid-cols-3">
      <div class="flex flex-col gap-4 @3xl/main:col-span-2">
        <HabitTrendChart />
        <WeekdayRhythm />
      </div>
      <SegmentDistribution />
    </div>
  </div>
</template>
