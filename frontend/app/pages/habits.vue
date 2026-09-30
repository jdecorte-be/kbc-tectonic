<script setup lang="ts">
import HabitTrendChart from '@/components/HabitTrendChart.vue'
import WeekdayRhythm from '@/components/WeekdayRhythm.vue'

definePageMeta({ title: 'Habits' })
</script>

<template>
  <div class="grid gap-4 px-4 lg:px-6">
    <HabitTrendChart />
    <WeekdayRhythm />
  </div>
</template>
