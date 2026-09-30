<script setup lang="ts">
import { IconArrowRight, IconTags, IconLoader2, IconRefresh, IconSparkles } from '@tabler/icons-vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardAction, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableEmpty, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { errorMessage, number } from '@/lib/api'

definePageMeta({ title: 'Category registry' })
const api = useKbcApi()
const registry = ref<Awaited<ReturnType<typeof api.categories>> | null>(null)
const loading = ref(true)
const error = ref('')
const discovered = computed(() => registry.value?.items.filter(category => category.source === 'openai').length ?? 0)
async function load() {
  loading.value = true
  error.value = ''
  try {
    registry.value = await api.categories()
  } catch (cause) {
    error.value = errorMessage(cause)
  } finally {
    loading.value = false
  }
}
onMounted(load)
</script>

<template>
  <div class="flex flex-col gap-4 md:gap-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="text-2xl font-semibold">
          Category registry
        </h2>
        <p class="text-muted-foreground text-sm">
          Categories available to Jev and learned from OpenAI discovery.
        </p>
      </div>
      <Button
        variant="outline"
        size="sm"
        :disabled="loading"
        @click="load"
      >
        <IconRefresh :class="loading && 'animate-spin'" /> Refresh registry
      </Button>
    </div>
    <p
      v-if="error"
      role="alert"
      class="text-destructive rounded-xl border p-4 text-sm"
    >
      {{ error }}
    </p>
    <div
      v-if="loading && !registry"
      class="text-muted-foreground flex items-center justify-center gap-2 py-12 text-sm"
    >
      <IconLoader2 class="size-4 animate-spin" /> Loading category registry…
    </div>
    <template v-if="registry">
      <div class="*:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card dark:*:data-[slot=card]:bg-card grid gap-4 *:data-[slot=card]:bg-gradient-to-t *:data-[slot=card]:shadow-xs sm:grid-cols-2">
        <Card class="@container/card">
          <CardHeader>
            <CardDescription>Available categories</CardDescription>
            <CardTitle class="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
              {{ number(registry.items.length) }}
            </CardTitle>
            <CardAction>
              <Badge variant="outline">
                <IconTags /> Registry
              </Badge>
            </CardAction>
          </CardHeader>
          <CardFooter class="flex-col items-start gap-1.5 text-sm">
            <div class="font-medium">
              Shared across client analyses
            </div>
            <div class="text-muted-foreground">
              Jev selects from the latest saved categories
            </div>
          </CardFooter>
        </Card>
        <Card class="@container/card">
          <CardHeader>
            <CardDescription>Discovered by OpenAI</CardDescription>
            <CardTitle class="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
              {{ number(discovered) }}
            </CardTitle>
            <CardAction>
              <Badge variant="outline">
                <IconSparkles /> Learned
              </Badge>
            </CardAction>
          </CardHeader>
          <CardFooter class="flex-col items-start gap-1.5 text-sm">
            <div class="font-medium">
              Discovery after an Unknown response
            </div>
            <div class="text-muted-foreground">
              New categories become options for the next client
            </div>
          </CardFooter>
        </Card>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Classification workflow</CardTitle>
          <CardDescription>When evidence is insufficient, the result can remain Unknown.</CardDescription>
        </CardHeader>
        <CardContent class="flex flex-wrap items-center gap-2">
          <Badge variant="outline">
            Jev classification
          </Badge><IconArrowRight class="text-muted-foreground size-4" />
          <Badge variant="outline">
            Unknown
          </Badge><IconArrowRight class="text-muted-foreground size-4" />
          <Badge variant="outline">
            OpenAI discovery
          </Badge><IconArrowRight class="text-muted-foreground size-4" />
          <Badge variant="outline">
            Saved for future analyses
          </Badge>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Categories</CardTitle>
          <CardDescription>Definitions, source and the number of assigned clients.</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Category</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Source</TableHead>
                <TableHead class="text-right">
                  Clients
                </TableHead>
                <TableHead>Created</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow
                v-for="category in registry.items"
                :key="category.id"
              >
                <TableCell class="font-medium">
                  {{ category.label }}
                </TableCell>
                <TableCell class="text-muted-foreground min-w-60 whitespace-normal">
                  {{ category.description }}
                </TableCell>
                <TableCell>
                  <Badge variant="outline">
                    <IconSparkles v-if="category.source === 'openai'" />
                    {{ category.source === 'openai' ? 'OpenAI' : 'Initial category' }}
                  </Badge>
                </TableCell>
                <TableCell class="text-right tabular-nums">
                  {{ number(category.client_count) }}
                </TableCell>
                <TableCell class="text-muted-foreground">
                  {{ new Date(category.created_at).toLocaleDateString('en-BE') }}
                </TableCell>
              </TableRow>
              <TableEmpty
                v-if="!registry.items.length"
                :colspan="5"
              >
                No categories are available yet.
              </TableEmpty>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      <Card v-if="registry.questions.length">
        <CardHeader>
          <CardTitle>Classification instructions</CardTitle>
          <CardDescription>Saved questions used to classify clients.</CardDescription>
        </CardHeader>
        <CardContent>
          <details
            v-for="question in registry.questions"
            :key="question.id"
            class="border-b py-3 first:pt-0 last:border-0 last:pb-0"
          >
            <summary class="cursor-pointer text-sm font-medium">
              {{ question.id }}
            </summary>
            <p class="text-muted-foreground mt-3 text-sm whitespace-pre-line">
              {{ question.instructions }}
            </p>
          </details>
        </CardContent>
      </Card>
    </template>
  </div>
</template>
