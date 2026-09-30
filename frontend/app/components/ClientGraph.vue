<script setup lang="ts">
import { Graph, GraphLinkStyle } from '@unovis/ts'
import { VisGraph, VisSingleContainer } from '@unovis/vue'
import type { Client, ProfileId } from '@/types/api'
import { profileColor } from '@/lib/profileColor'
import { trackersFor } from '@/lib/trackers'
import type { Trackers } from '@/lib/trackers'

const props = withDefaults(defineProps<{
  layout?: 'sorted' | 'network'
  filter?: ProfileId[] // empty = everything active
  height?: number
}>(), { layout: 'sorted', filter: () => [], height: 460 })

const emit = defineEmits<{ select: [client: Client] }>()
const selected = defineModel<string | undefined>('selected')

const clients = await useClients()
const dash = await useDashboard()
const { data: jev } = await useJev()
const profiles = await useProfiles()
const relations = await useRelations(3)

interface GNode { id: string, kind: 'client' | 'profile', profile: ProfileId, client?: Client, t?: Trackers, count?: number, x?: number, y?: number }
interface GLink { source: string, target: string, kind: 'linked' | 'similar' | 'tracker', weight: number }

const COL = 170 // px between profile clusters
const ROW = 100 // px between clients in a cluster
const HEAD = 100 // px from a profile header to its first client
const PER_ROW = 6 // profile clusters per grid row
const SECONDARY = 0.5 // show a dashed link to any other profile tracked at >= 50%

const scored = computed(() => clients.value.map(c => ({ c, t: trackersFor(c, jev.value?.clients[c.id]) })))

// Profile columns, biggest segment first; clients inside a column sorted by their tracker, strongest on top.
const columns = computed(() => {
  const groups = new Map<ProfileId, typeof scored.value>()
  for (const s of scored.value) groups.set(s.t.main, [...(groups.get(s.t.main) ?? []), s])
  return [...groups.entries()]
    .map(([id, members]) => ({ id, members: members.sort((a, b) => b.t.mainConfidence - a.t.mainConfidence) }))
    .sort((a, b) => b.members.length - a.members.length || profiles.value[a.id].label.localeCompare(profiles.value[b.id].label))
})

const data = computed(() => {
  const nodes: GNode[] = []
  const links: GLink[] = []
  const explicit = dash.value?.links ?? []

  if (props.layout === 'sorted') {
    let top = 0
    for (let r = 0; r * PER_ROW < columns.value.length; r++) {
      const row = columns.value.slice(r * PER_ROW, (r + 1) * PER_ROW)
      row.forEach((col, i) => {
        const x = i * COL
        nodes.push({ id: `p:${col.id}`, kind: 'profile', profile: col.id, count: col.members.length, x, y: top })
        col.members.forEach(({ c, t }, j) => nodes.push({ id: c.id, kind: 'client', profile: t.main, client: c, t, x, y: top + HEAD + j * ROW }))
      })
      top += HEAD + Math.max(...row.map(c => c.members.length)) * ROW + 30
    }
    const cols = new Set(columns.value.map(c => c.id))
    for (const { c, t } of scored.value) {
      for (const tr of t.trackers) {
        if (tr.id !== t.main && tr.confidence >= SECONDARY && cols.has(tr.id)) {
          links.push({ source: c.id, target: `p:${tr.id}`, kind: 'tracker', weight: tr.confidence })
        }
      }
    }
    for (const [a, b] of explicit) links.push({ source: a, target: b, kind: 'linked', weight: 1 })
    return { nodes, links }
  }

  for (const { c, t } of scored.value) nodes.push({ id: c.id, kind: 'client', profile: t.main, client: c, t })
  const seen = new Set<string>()
  for (const c of clients.value) {
    for (const r of relations.value[c.id] ?? []) {
      const key = [c.id, r.clientId].sort().join('|')
      if (seen.has(key)) continue
      seen.add(key)
      links.push({ source: c.id, target: r.clientId, kind: r.kind, weight: r.score })
    }
  }
  return { nodes, links }
})

const nodeById = computed(() => new Map(data.value.nodes.map(n => [n.id, n])))
const idOf = (x: unknown) => typeof x === 'string' ? x : (x as GNode).id
const active = (n: GNode) => !props.filter.length || props.filter.includes(n.profile)
  || (n.kind === 'client' && n.t!.trackers.some(t => props.filter.includes(t.id) && t.confidence >= SECONDARY))

const initials = (name: string) => name.split(' ').map(w => w[0]).join('').slice(0, 2)
const pct = (v: number) => `${Math.round(v * 100)}%`

const graph = {
  nodeFill: (n: GNode) => n.kind === 'profile' ? profileColor(n.profile) : 'var(--card)',
  nodeShape: (n: GNode) => n.kind === 'profile' ? 'square' : 'circle',
  nodeSize: (n: GNode) => n.kind === 'profile' ? 22 : 36,
  nodeStroke: (n: GNode) => n.client?.change && n.client.change.severity !== 'info' ? 'var(--destructive)' : 'var(--border)',
  nodeStrokeWidth: (n: GNode) => n.kind === 'profile' ? 0 : 1.5,
  nodeIconSize: 12,
  nodeGaugeValue: (n: GNode) => n.kind === 'client' ? n.t!.mainConfidence * 100 : 0,
  nodeGaugeFill: (n: GNode) => profileColor(n.profile),
  nodeLabel: (n: GNode) => n.kind === 'profile' ? profiles.value[n.profile].label : n.client!.name.split(' ')[0],
  nodeSubLabel: (n: GNode) => n.kind === 'profile' ? `${n.count} client${n.count === 1 ? '' : 's'}` : pct(n.t!.mainConfidence),
  nodeIcon: (n: GNode) => n.kind === 'profile' ? '' : initials(n.client!.name),
  nodeLabelTrimLength: 22,
  nodeDisabled: (n: GNode) => !active(n),
  linkWidth: (l: GLink) => l.kind === 'linked' ? 2.5 : l.kind === 'tracker' ? 1 + l.weight * 2 : 1,
  linkStroke: (l: GLink) => l.kind === 'linked' ? 'var(--primary)' : l.kind === 'tracker' ? profileColor(nodeById.value.get(idOf(l.target))!.profile) : 'var(--muted-foreground)',
  linkStyle: (l: GLink) => l.kind === 'tracker' ? GraphLinkStyle.Dashed : GraphLinkStyle.Solid,
  linkFlow: (l: GLink) => l.kind === 'linked',
  linkDisabled: (l: GLink) => {
    const s = nodeById.value.get(idOf(l.source))
    const t = nodeById.value.get(idOf(l.target))
    return !s || !t || !active(s) || !active(t)
  }
}

const events = {
  [Graph.selectors.node]: {
    click: (n: GNode) => {
      if (n.kind !== 'client') return
      selected.value = n.id
      emit('select', n.client!)
    }
  }
}
</script>

<template>
  <VisSingleContainer
    :data="data"
    :height="height"
    class="[--vis-graph-node-label-text-color:var(--foreground)] [--vis-graph-node-sublabel-text-color:var(--muted-foreground)] [--vis-graph-node-label-background:transparent] [--vis-graph-node-icon-fill-color:var(--foreground)] [--vis-graph-link-stroke-opacity:0.6] [--vis-graph-node-label-font-size:12px] [--vis-graph-node-sublabel-font-size:10px] [--vis-graph-node-greyout-color:var(--muted)] [--vis-dark-graph-node-greyout-color:var(--muted)] [--vis-graph-node-icon-greyout-color:var(--muted-foreground)] [--vis-dark-graph-node-icon-greyout-color:var(--muted-foreground)] [--vis-graph-node-greyout-opacity:0.35] [--vis-graph-link-greyout-opacity:0.15]"
  >
    <VisGraph
      :key="layout"
      v-bind="graph"
      :layout-type="layout === 'sorted' ? 'precalculated' : 'force'"
      :force-layout-settings="{ charge: -500, linkDistance: 80 }"
      :fit-view-padding="40"
      :selected-node-id="selected"
      :events="events"
    />
  </VisSingleContainer>
</template>
