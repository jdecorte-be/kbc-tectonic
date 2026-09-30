<script setup lang="ts">
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { segmentCounts } from '@/data/mock'

const max = Math.max(...segmentCounts.map(s => s.count))
const total = segmentCounts.reduce((a, s) => a + s.count, 0)
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle>Client profiles</CardTitle>
      <CardDescription>Main profile per client, inferred from transactions</CardDescription>
    </CardHeader>
    <CardContent class="flex flex-col gap-3">
      <div
        v-for="s in segmentCounts"
        :key="s.id"
        class="grid gap-1"
      >
        <div class="flex items-center justify-between text-sm">
          <span>{{ s.label }}</span>
          <span class="text-muted-foreground tabular-nums">
            {{ s.count.toLocaleString('en-BE') }} · {{ Math.round((s.count / total) * 100) }}%
          </span>
        </div>
        <div class="bg-muted h-2 overflow-hidden rounded-full">
          <div
            class="bg-primary h-full rounded-full"
            :style="{ width: `${(s.count / max) * 100}%` }"
          />
        </div>
      </div>
    </CardContent>
  </Card>
</template>
