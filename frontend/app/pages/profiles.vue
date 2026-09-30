<script setup lang="ts">
import SegmentDistribution from '@/components/SegmentDistribution.vue'
import { Badge } from '@/components/ui/badge'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { PROFILES, PROFILE_IDS, clients } from '@/data/mock'

definePageMeta({ title: 'Profiles' })

const cards = PROFILE_IDS.map(id => ({
  id,
  ...PROFILES[id],
  members: clients.filter(c => c.profiles.some(p => p.id === id))
}))
</script>

<template>
  <div class="grid gap-4 px-4 lg:px-6 @3xl/main:grid-cols-3">
    <div class="@3xl/main:col-span-1">
      <SegmentDistribution />
    </div>
    <div class="grid content-start gap-4 sm:grid-cols-2 @3xl/main:col-span-2">
      <Card
        v-for="p in cards"
        :key="p.id"
      >
        <CardHeader>
          <CardTitle class="flex items-center justify-between gap-2">
            {{ p.label }}
            <Badge
              v-if="p.core"
              variant="outline"
            >
              Core
            </Badge>
          </CardTitle>
          <CardDescription>Offer: {{ p.offer }}</CardDescription>
          <div class="flex flex-wrap gap-1 pt-2 text-sm">
            <NuxtLink
              v-for="c in p.members"
              :key="c.id"
              :to="`/client/${c.id}`"
              class="text-primary underline"
            >
              {{ c.name }}
            </NuxtLink>
            <span
              v-if="!p.members.length"
              class="text-muted-foreground"
            >No clients yet</span>
          </div>
        </CardHeader>
      </Card>
    </div>
  </div>
</template>
