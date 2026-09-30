<script setup lang="ts">
import { IconBrandGithub } from '@tabler/icons-vue'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { SidebarTrigger } from '@/components/ui/sidebar'

const route = useRoute()
</script>

<template>
  <header class="flex h-(--header-height) shrink-0 items-center gap-2 border-b transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-(--header-height)">
    <div class="flex w-full items-center gap-1 px-4 lg:gap-2 lg:px-6">
      <SidebarTrigger class="-ml-1" />
      <Separator
        orientation="vertical"
        class="mx-2 data-[orientation=vertical]:h-4"
      />
      <h1 class="text-base font-medium">
        {{ route.meta.title ?? 'Client profiles & habits' }}
      </h1>
      <div class="ml-auto flex items-center gap-2">
        <span class="text-muted-foreground hidden text-xs sm:inline">Synthetic demo data</span>
        <Button variant="ghost" size="sm" as-child class="hidden sm:flex">
          <a
            href="https://github.com/jdecorte-be/kbc-tectonic"
            target="_blank"
            rel="noopener noreferrer"
            class="dark:text-foreground"
          >
            <IconBrandGithub class="size-4" />
            GitHub
          </a>
        </Button>
      </div>
    </div>
  </header>
</template>
