<script setup lang="ts">
definePageMeta({ title: 'Client analysis' })
const route = useRoute()
</script>

<template>
  <ClientWorkspace
    :key="String(route.params.id)"
    :initial-client-id="String(route.params.id)"
  />
</template>
