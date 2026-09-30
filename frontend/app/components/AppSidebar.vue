<script setup lang="ts">
import {
  IconBell,
  IconChartBar,
  IconDashboard,
  IconGift,
  IconHelp,
  IconReport,
  IconSearch,
  IconSettings,
  IconTags,
  IconUsers
} from '@tabler/icons-vue'

import NavDocuments from '@/components/NavDocuments.vue'
import NavMain from '@/components/NavMain.vue'
import NavSecondary from '@/components/NavSecondary.vue'
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
    { title: 'Overview', url: '#', icon: IconDashboard },
    { title: 'Clients', url: '#', icon: IconUsers },
    { title: 'Profiles', url: '#', icon: IconTags },
    { title: 'Habits', url: '#', icon: IconChartBar },
    { title: 'Alerts', url: '#', icon: IconBell }
  ],
  navSecondary: [
    {
      title: 'Settings',
      url: '#',
      icon: IconSettings
    },
    {
      title: 'Get Help',
      url: '#',
      icon: IconHelp
    },
    {
      title: 'Search',
      url: '#',
      icon: IconSearch
    }
  ],
  documents: [
    { name: 'Offers', url: '#', icon: IconGift },
    { name: 'Reports', url: '#', icon: IconReport }
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
      <NavDocuments :items="data.documents" />
      <NavSecondary
        :items="data.navSecondary"
        class="mt-auto"
      />
    </SidebarContent>
    <SidebarFooter>
      <NavUser :user="data.user" />
    </SidebarFooter>
  </Sidebar>
</template>
