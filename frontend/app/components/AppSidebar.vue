<script setup lang="ts">
import { IconBell, IconChartBar, IconDashboard, IconTags, IconUsers } from '@tabler/icons-vue'

import NavMain from '@/components/NavMain.vue'
import NavUser from '@/components/NavUser.vue'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader
} from '@/components/ui/sidebar'

const data = {
  user: {
    name: 'KBC Advisor',
    email: 'advisor@kbc.example',
    avatar: '/avatars/shadcn.jpg'
  },
  navMain: [
    { title: 'Overview', url: '/', icon: IconDashboard },
    { title: 'Clients', url: '/client', icon: IconUsers },
    { title: 'Profiles', url: '/profiles', icon: IconTags },
    { title: 'Habits', url: '/habits', icon: IconChartBar },
    { title: 'Alerts', url: '/alerts', icon: IconBell }
  ]
}
</script>

<template>
  <Sidebar collapsible="offcanvas">
    <SidebarHeader>
      <a
        href="#"
        class="flex items-center px-2 py-1"
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
      </a>
    </SidebarHeader>
    <SidebarContent>
      <NavMain :items="data.navMain" />
    </SidebarContent>
    <SidebarFooter>
      <NavUser :user="data.user" />
    </SidebarFooter>
  </Sidebar>
</template>
