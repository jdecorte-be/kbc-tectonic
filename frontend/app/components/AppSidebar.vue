<script setup lang="ts">
import { IconChartBar, IconDashboard, IconGift, IconTags, IconUsers } from '@tabler/icons-vue'
import NavMain from '@/components/NavMain.vue'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Sidebar, SidebarContent, SidebarFooter, SidebarHeader } from '@/components/ui/sidebar'

const navigation = [
  { title: 'Dashboard', url: '/', icon: IconDashboard },
  { title: 'Clients', url: '/client', icon: IconUsers },
  { title: 'Profiles', url: '/categories', icon: IconTags },
  { title: 'Benchmark', url: '/benchmark', icon: IconChartBar },
  { title: 'Products', url: '/products', icon: IconGift }
]
</script>

<template>
  <Sidebar collapsible="offcanvas">
    <SidebarHeader>
      <NuxtLink
        to="/"
        class="flex items-center px-2 py-1"
        aria-label="KBC — home"
      >
        <img
          src="/kbc-logo.png"
          alt="KBC"
          class="h-14 w-auto dark:hidden"
        >
        <img
          src="/kbc-logo-dark.png"
          alt="KBC"
          class="hidden h-14 w-auto dark:block"
        >
      </NuxtLink>
    </SidebarHeader>
    <SidebarContent>
      <NavMain :items="navigation" />
    </SidebarContent>
    <SidebarFooter>
      <div class="flex items-center gap-2 rounded-md p-2">
        <Avatar class="size-8 rounded-lg">
          <AvatarFallback class="rounded-lg">
            KA
          </AvatarFallback>
        </Avatar>
        <div class="grid flex-1 text-left text-sm leading-tight">
          <span class="truncate font-medium">KBC Advisor</span>
          <span class="text-muted-foreground truncate text-xs">Synthetic data workspace</span>
        </div>
      </div>
    </SidebarFooter>
  </Sidebar>
</template>
