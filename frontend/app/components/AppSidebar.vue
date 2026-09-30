<script setup lang="ts">
import { IconActivity, IconArrowUpRight, IconBolt, IconFlask, IconFingerprint, IconGift, IconShieldCheck, IconUsers } from '@tabler/icons-vue'
import { Sidebar, SidebarContent, SidebarFooter, SidebarHeader, SidebarGroup, SidebarGroupLabel, SidebarMenu, SidebarMenuItem, SidebarMenuButton } from '@/components/ui/sidebar'

const route = useRoute()
const navigation = [
  { title: 'Individual analysis', url: '/', icon: IconActivity },
  { title: 'Scalability benchmark', url: '/benchmark', icon: IconBolt },
  { title: 'Synthetic clients', url: '/client', icon: IconUsers },
  { title: 'Category registry', url: '/categories', icon: IconFingerprint },
  { title: 'Product catalogue', url: '/products', icon: IconGift }
]
</script>

<template>
  <Sidebar collapsible="offcanvas">
    <SidebarHeader class="gap-5 px-5 pt-6 pb-7">
      <NuxtLink
        to="/"
        class="flex items-center gap-3"
        aria-label="KBC — home"
      >
        <img
          src="/kbc-logo.png"
          alt="KBC"
          class="h-10 w-auto dark:hidden"
        >
        <img
          src="/kbc-logo-dark.png"
          alt="KBC"
          class="hidden h-10 w-auto dark:block"
        >
        <span class="border-border border-l pl-3 text-sm font-semibold tracking-wide">Tectonic<span class="text-muted-foreground mt-0.5 block text-[10px] font-normal tracking-[0.2em] uppercase">Customer intelligence</span></span>
      </NuxtLink>
      <div class="bg-primary/10 text-primary flex w-fit items-center gap-2 rounded-full px-2.5 py-1 text-[11px] font-medium">
        <IconFlask class="size-3.5" /> Hackathon · demo
      </div>
    </SidebarHeader>
    <SidebarContent>
      <SidebarGroup class="px-3">
        <SidebarGroupLabel class="mb-2 text-[10px] tracking-[0.16em] uppercase">
          Workspace
        </SidebarGroupLabel>
        <SidebarMenu class="gap-2">
          <SidebarMenuItem
            v-for="item in navigation"
            :key="item.url"
          >
            <SidebarMenuButton
              as-child
              :is-active="item.url === '/' ? route.path === '/' : route.path.startsWith(item.url)"
              class="h-11 px-3"
            >
              <NuxtLink :to="item.url"><component :is="item.icon" /><span>{{ item.title }}</span><IconArrowUpRight
                v-if="route.path === item.url"
                class="ml-auto size-3.5 opacity-50"
              /></NuxtLink>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarGroup>
      <div class="border-border bg-background/35 mx-5 mt-auto rounded-xl border p-4">
        <IconShieldCheck class="text-primary mb-3 size-5" />
        <p class="text-sm font-medium">
          Relevance comes first.
        </p>
        <p class="text-muted-foreground mt-2 text-xs leading-relaxed">
          Observable signals. Explainable profiles. And no advertising when the evidence is insufficient.
        </p>
      </div>
    </SidebarContent>
    <SidebarFooter class="px-5 py-5">
      <div class="text-muted-foreground flex items-center gap-2 text-xs">
        <span class="bg-primary size-1.5 rounded-full" /> 100% synthetic data
      </div>
    </SidebarFooter>
  </Sidebar>
</template>
