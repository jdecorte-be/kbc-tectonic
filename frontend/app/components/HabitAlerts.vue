<script setup lang="ts">
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { primaryProfile } from '@/lib/profileColor'
import type { Client } from '@/types/api'

const props = withDefaults(defineProps<{ limit?: number }>(), { limit: 6 })
const emit = defineEmits<{ select: [client: Client] }>()

const order = { alert: 0, watch: 1, info: 2 }
const clients = await useClients()
const profiles = await useProfiles()
const alerts = computed(() => clients.value
  .filter(c => c.change)
  .sort((a, b) => order[a.change!.severity] - order[b.change!.severity])
  .slice(0, props.limit))

const variant = (s: string) => (s === 'alert' ? 'destructive' : s === 'watch' ? 'secondary' : 'outline')
</script>

<template>
  <Card>
    <CardHeader>
      <CardTitle>Habit changes</CardTitle>
      <CardDescription>Drift vs. each client's own baseline</CardDescription>
    </CardHeader>
    <CardContent class="flex flex-col gap-1">
      <button
        v-for="c in alerts"
        :key="c.id"
        type="button"
        class="hover:bg-muted flex flex-col items-start gap-1 rounded-md p-2 text-left text-sm transition-colors"
        @click="emit('select', c)"
      >
        <div class="flex w-full items-center justify-between gap-2">
          <span class="font-medium">{{ c.name }}</span>
          <Badge :variant="variant(c.change!.severity)">
            {{ c.change!.delta > 0 ? '+' : '' }}{{ c.change!.delta }}%
          </Badge>
        </div>
        <span class="text-muted-foreground">{{ c.change!.text }}</span>
        <span class="text-xs">
          Profile: {{ profiles[primaryProfile(c).id].label }}
        </span>
      </button>
    </CardContent>
  </Card>
</template>
