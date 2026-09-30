<script setup lang="ts">
import { IconLock } from '@tabler/icons-vue'
import { SidebarTrigger } from '@/components/ui/sidebar'

const route = useRoute()
</script>

<template>
  <header class="border-border flex h-16 shrink-0 items-center gap-3 border-b px-4 lg:px-8">
    <SidebarTrigger class="-ml-1" />
    <span class="text-muted-foreground text-sm">Workspace</span><span class="text-muted-foreground/40">/</span>
    <span class="text-sm font-medium">{{ route.meta.title ?? 'Individual analysis' }}</span>
    <div class="text-muted-foreground ml-auto hidden items-center gap-1.5 text-xs sm:flex">
      <IconLock class="size-3.5" /> KBC × Jev demo
    </div>
  </header>
</template>
