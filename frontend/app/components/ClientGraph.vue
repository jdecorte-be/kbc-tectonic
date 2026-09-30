<script setup lang="ts">
import ForceGraph from 'force-graph'
import { useResizeObserver } from '@vueuse/core'
import { IconFocusCentered, IconMinus, IconPlayerPause, IconPlayerPlay, IconPlus } from '@tabler/icons-vue'
import { Button } from '@/components/ui/button'
import type { Client, ProfileId } from '@/types/api'
import { profileColor } from '@/lib/profileColor'
import { trackersFor } from '@/lib/trackers'
import type { Trackers } from '@/lib/trackers'

const props = withDefaults(defineProps<{
  layout?: 'sorted' | 'network'
  filter?: ProfileId[] // empty = everything active
  height?: number
}>(), { layout: 'sorted', filter: () => [], height: 460 })

const emit = defineEmits<{ select: [client: Client], toggleProfile: [profile: ProfileId] }>()
const selected = defineModel<string | undefined>('selected')

const clients = await useClients()
const dash = await useDashboard()
const { data: jev } = await useJev()
const profiles = await useProfiles()
const relations = await useRelations(3)
const colorMode = useColorMode()

interface GNode {
  id: string
  kind: 'client' | 'profile'
  profile: ProfileId
  r: number
  client?: Client
  t?: Trackers
  count?: number
  x?: number
  y?: number
  vx?: number
  vy?: number
  fx?: number
  fy?: number
}
type End = string | GNode
interface GLink { source: End, target: End, kind: 'member' | 'tracker' | 'linked' | 'similar', weight: number }

const SECONDARY = 0.5 // link a client to any other profile tracked at >= 50%
const CLIENT_R = 6

const idOf = (x: End) => typeof x === 'string' ? x : x.id
const initials = (name: string) => name.split(' ').map(w => w[0]).join('').slice(0, 2)
const pct = (v: number) => `${Math.round(v * 100)}%`
const alerting = (n: GNode) => !!n.client?.change && n.client.change.severity !== 'info'

const scored = computed(() => clients.value.map(c => ({ c, t: trackersFor(c, jev.value?.clients[c.id]) })))

// Profiles biggest segment first; each gets an anchor point on a ring that its clients gravitate to.
const segments = computed(() => {
  const counts = new Map<ProfileId, number>()
  for (const { t } of scored.value) counts.set(t.main, (counts.get(t.main) ?? 0) + 1)
  return [...counts.entries()].sort((a, b) => b[1] - a[1])
})
const anchors = computed(() => {
  const n = segments.value.length
  const R = 90 + n * 22
  return new Map(segments.value.map(([p], i) => {
    const a = (i / n) * Math.PI * 2 - Math.PI / 2
    return [p, { x: Math.cos(a) * R, y: Math.sin(a) * R }]
  }))
})

// ---- graph data ------------------------------------------------------------

let prev = new Map<string, GNode>() // keep positions so switching layouts animates instead of restarting

const data = computed(() => {
  const nodes: GNode[] = []
  const links: GLink[] = []
  const sorted = props.layout === 'sorted'

  if (sorted) {
    for (const [p, count] of segments.value) {
      nodes.push({ id: `p:${p}`, kind: 'profile', profile: p, count, r: 10 + Math.sqrt(count) * 2.2 })
    }
  }
  for (const { c, t } of scored.value) {
    nodes.push({ id: c.id, kind: 'client', profile: t.main, client: c, t, r: CLIENT_R })
    if (!sorted) continue
    links.push({ source: c.id, target: `p:${t.main}`, kind: 'member', weight: t.mainConfidence })
    for (const tr of t.trackers) {
      if (tr.id !== t.main && tr.confidence >= SECONDARY && anchors.value.has(tr.id)) {
        links.push({ source: c.id, target: `p:${tr.id}`, kind: 'tracker', weight: tr.confidence })
      }
    }
  }

  const seen = new Set<string>()
  const add = (a: string, b: string, kind: 'linked' | 'similar', weight: number) => {
    const key = [a, b].sort().join('|')
    if (seen.has(key)) return
    seen.add(key)
    links.push({ source: a, target: b, kind, weight })
  }
  for (const [a, b] of dash.value?.links ?? []) add(a, b, 'linked', 1)
  if (!sorted) {
    const max = Math.max(1, ...Object.values(relations.value).flat().map(r => r.score))
    for (const c of clients.value) {
      for (const r of relations.value[c.id] ?? []) add(c.id, r.clientId, r.kind, r.score / max)
    }
  }

  const ids = new Set(nodes.map(n => n.id))
  const valid = links.filter(l => ids.has(idOf(l.source)) && ids.has(idOf(l.target)))

  for (const n of nodes) {
    const old = prev.get(n.id)
    const a = anchors.value.get(n.profile)!
    if (old?.x !== undefined) Object.assign(n, { x: old.x, y: old.y, vx: old.vx, vy: old.vy })
    else if (n.kind === 'profile') Object.assign(n, { x: a.x, y: a.y })
    else Object.assign(n, { x: a.x * 0.2 + (Math.random() - 0.5) * 40, y: a.y * 0.2 + (Math.random() - 0.5) * 40 })
  }
  prev = new Map(nodes.map(n => [n.id, n]))
  return { nodes, links: valid }
})

const neighbours = computed(() => {
  const m = new Map<string, Set<string>>()
  for (const l of data.value.links) {
    const a = idOf(l.source)
    const b = idOf(l.target)
    if (!m.has(a)) m.set(a, new Set())
    if (!m.has(b)) m.set(b, new Set())
    m.get(a)!.add(b)
    m.get(b)!.add(a)
  }
  return m
})

// ---- interaction state -----------------------------------------------------

const hovered = ref<string>()
const focus = computed(() => hovered.value ?? selected.value)
const paused = ref(false)

const active = (n: GNode) => !props.filter.length || props.filter.includes(n.profile)
  || (n.kind === 'client' && n.t!.trackers.some(t => props.filter.includes(t.id) && t.confidence >= SECONDARY))
const inFocus = (id: string) => !focus.value || id === focus.value || !!neighbours.value.get(focus.value)?.has(id)
const nodeAlpha = (n: GNode) => !active(n) ? 0.1 : inFocus(n.id) ? 1 : 0.18
const linkTouchesFocus = (l: GLink) => !!focus.value && (idOf(l.source) === focus.value || idOf(l.target) === focus.value)

// ---- theme (canvas can't read CSS variables, so resolve them) --------------

const theme = reactive({ fg: '#fff', muted: '#888', card: '#111', border: '#333', primary: '#1DBCC2', destructive: '#e5484d', bg: '#000' })
function readTheme() {
  const s = getComputedStyle(document.documentElement)
  const v = (name: string, fallback: string) => s.getPropertyValue(name).trim() || fallback
  Object.assign(theme, {
    fg: v('--foreground', theme.fg),
    muted: v('--muted-foreground', theme.muted),
    card: v('--card', theme.card),
    border: v('--border', theme.border),
    primary: v('--primary', theme.primary),
    destructive: v('--destructive', theme.destructive),
    bg: v('--background', theme.bg)
  })
}

// ---- drawing ---------------------------------------------------------------

const FONT = 'ui-sans-serif, system-ui, sans-serif'
const pulse = (speed = 1) => (Math.sin(performance.now() / (400 / speed)) + 1) / 2

function drawClient(n: GNode, ctx: CanvasRenderingContext2D, k: number) {
  const { x = 0, y = 0, r } = n
  const color = profileColor(n.profile)
  const isSel = n.id === selected.value
  const isHover = n.id === hovered.value
  ctx.globalAlpha = nodeAlpha(n)

  if (alerting(n) && active(n)) {
    ctx.beginPath()
    ctx.arc(x, y, r + 2 + pulse() * 4, 0, Math.PI * 2)
    ctx.strokeStyle = theme.destructive
    ctx.globalAlpha *= 0.6 * (1 - pulse() * 0.7)
    ctx.lineWidth = 1
    ctx.stroke()
    ctx.globalAlpha = nodeAlpha(n)
  }
  if (isSel) {
    ctx.beginPath()
    ctx.arc(x, y, r + 5 + pulse(0.6) * 3, 0, Math.PI * 2)
    ctx.fillStyle = theme.primary
    ctx.globalAlpha = 0.18
    ctx.fill()
    ctx.globalAlpha = 1
  }

  ctx.beginPath()
  ctx.arc(x, y, r * (isHover ? 1.15 : 1), 0, Math.PI * 2)
  ctx.fillStyle = theme.card
  ctx.fill()
  ctx.lineWidth = 0.6
  ctx.strokeStyle = isSel ? theme.primary : alerting(n) ? theme.destructive : theme.border
  ctx.stroke()

  // Confidence gauge in the profile colour.
  ctx.beginPath()
  ctx.arc(x, y, r * (isHover ? 1.15 : 1) - 0.9, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * n.t!.mainConfidence)
  ctx.strokeStyle = color
  ctx.lineWidth = 1.8
  ctx.lineCap = 'round'
  ctx.stroke()

  if (k * r > 9) {
    ctx.fillStyle = theme.fg
    ctx.font = `600 ${r * 0.75}px ${FONT}`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(initials(n.client!.name), x, y + 0.3)
  }
  if (isSel || isHover || k > 2.6 || (focus.value && inFocus(n.id) && k > 1.2)) {
    const fs = 11 / k
    ctx.font = `${isSel || isHover ? 600 : 400} ${fs}px ${FONT}`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'top'
    ctx.fillStyle = isSel || isHover ? theme.fg : theme.muted
    ctx.fillText(n.client!.name.split(' ')[0]!, x, y + r + 2 / k + 1)
  }
  ctx.globalAlpha = 1
}

function drawProfile(n: GNode, ctx: CanvasRenderingContext2D, k: number) {
  const { x = 0, y = 0, r } = n
  const color = profileColor(n.profile)
  const picked = props.filter.includes(n.profile)
  ctx.globalAlpha = nodeAlpha(n)

  const glow = ctx.createRadialGradient(x, y, r * 0.6, x, y, r * 2.4)
  glow.addColorStop(0, color)
  glow.addColorStop(1, 'transparent')
  ctx.globalAlpha *= 0.25 + (n.id === hovered.value ? 0.2 : 0)
  ctx.fillStyle = glow
  ctx.beginPath()
  ctx.arc(x, y, r * 2.4, 0, Math.PI * 2)
  ctx.fill()

  ctx.globalAlpha = nodeAlpha(n)
  ctx.beginPath()
  ctx.arc(x, y, r, 0, Math.PI * 2)
  ctx.fillStyle = color
  ctx.fill()
  if (picked) {
    ctx.lineWidth = 2 / k
    ctx.strokeStyle = theme.fg
    ctx.stroke()
  }

  ctx.fillStyle = theme.bg
  ctx.font = `700 ${r * 0.8}px ${FONT}`
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(String(n.count), x, y + 0.5)

  const fs = Math.max(12 / k, 4)
  ctx.font = `600 ${fs}px ${FONT}`
  ctx.textBaseline = 'top'
  ctx.fillStyle = theme.fg
  ctx.fillText(profiles.value[n.profile].label, x, y + r + 3)
  ctx.globalAlpha = 1
}

function drawLink(l: GLink, ctx: CanvasRenderingContext2D, k: number) {
  const s = l.source as GNode
  const t = l.target as GNode
  if (s.x === undefined || t.x === undefined) return
  const hot = linkTouchesFocus(l)
  const dim = !active(s) || !active(t) ? 0.03 : focus.value && !hot ? 0.04 : 1

  ctx.beginPath()
  ctx.moveTo(s.x, s.y!)
  ctx.lineTo(t.x, t.y!)
  ctx.setLineDash([])
  if (l.kind === 'linked') {
    ctx.strokeStyle = theme.primary
    ctx.lineWidth = 2.2
    ctx.globalAlpha = 0.85 * dim
  } else if (l.kind === 'member') {
    ctx.strokeStyle = profileColor(t.profile)
    ctx.lineWidth = 0.4 + l.weight * 1.2
    ctx.globalAlpha = (hot ? 0.9 : 0.22) * dim
  } else if (l.kind === 'tracker') {
    ctx.strokeStyle = profileColor(t.profile)
    ctx.lineWidth = 0.8
    ctx.setLineDash([3, 3])
    ctx.globalAlpha = (hot ? 0.8 : 0.12) * dim
  } else {
    ctx.strokeStyle = theme.muted
    ctx.lineWidth = 0.3 + l.weight * 1.2
    ctx.globalAlpha = (hot ? 0.8 : 0.15) * dim
  }
  ctx.lineWidth /= Math.max(1, k / 2)
  ctx.stroke()
  ctx.setLineDash([])
  ctx.globalAlpha = 1
}

// Network view: soft coloured halo + label behind each profile cluster.
function drawClusters(ctx: CanvasRenderingContext2D, k: number) {
  if (props.layout !== 'network') return
  const acc = new Map<ProfileId, { x: number, y: number, n: number, far: number }>()
  for (const n of data.value.nodes) {
    const a = acc.get(n.profile) ?? { x: 0, y: 0, n: 0, far: 0 }
    a.x += n.x ?? 0
    a.y += n.y ?? 0
    a.n++
    acc.set(n.profile, a)
  }
  for (const n of data.value.nodes) {
    const a = acc.get(n.profile)!
    a.far = Math.max(a.far, Math.hypot((n.x ?? 0) - a.x / a.n, (n.y ?? 0) - a.y / a.n))
  }
  for (const [p, a] of acc) {
    const cx = a.x / a.n
    const cy = a.y / a.n
    const R = Math.max(24, a.far + 14)
    const faded = props.filter.length && !props.filter.includes(p)
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, R)
    g.addColorStop(0, profileColor(p))
    g.addColorStop(1, 'transparent')
    ctx.globalAlpha = faded ? 0.03 : 0.13
    ctx.fillStyle = g
    ctx.beginPath()
    ctx.arc(cx, cy, R, 0, Math.PI * 2)
    ctx.fill()
    ctx.globalAlpha = faded ? 0.15 : 0.9
    ctx.fillStyle = profileColor(p)
    ctx.font = `600 ${13 / k}px ${FONT}`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'bottom'
    ctx.fillText(`${profiles.value[p].label} · ${a.n}`, cx, cy - R - 2)
  }
  ctx.globalAlpha = 1
}

function tooltip(n: GNode) {
  if (n.kind === 'profile') {
    return `<div style="font:12px ${FONT}"><b>${profiles.value[n.profile].label}</b><br>${n.count} clients · click to filter</div>`
  }
  const c = n.client!
  const top = n.t!.trackers.slice(0, 3).map(t => `${profiles.value[t.id].label} ${pct(t.confidence)}`).join('<br>')
  const alert = c.change ? `<br><span style="color:${theme.destructive}">⚠ ${c.change.habit} ${c.change.delta > 0 ? '+' : ''}${c.change.delta}%</span>` : ''
  return `<div style="font:12px ${FONT};line-height:1.4"><b>${c.name}</b> · ${c.age}y<br><span style="opacity:.75">${top}</span>${alert}</div>`
}

// ---- forces ----------------------------------------------------------------

// Pulls every node towards its profile's anchor; hubs are held firmly, clients gently.
function clusterForce() {
  let nodes: GNode[] = []
  const force = (alpha: number) => {
    const sorted = props.layout === 'sorted'
    for (const n of nodes) {
      const a = anchors.value.get(n.profile)
      if (!a) continue
      const s = n.kind === 'profile' ? 0.25 : sorted ? 0.01 : 0.06
      n.vx! += (a.x - n.x!) * s * alpha
      n.vy! += (a.y - n.y!) * s * alpha
    }
  }
  force.initialize = (ns: GNode[]) => {
    nodes = ns
  }
  return force
}

// ---- lifecycle -------------------------------------------------------------

const el = ref<HTMLDivElement>()
let fg: ForceGraph<GNode, GLink> | undefined
let fitted = false

function configureForces() {
  if (!fg) return
  const link = fg.d3Force('link')!
  link.distance((l: GLink) => l.kind === 'member' ? 18 + (1 - l.weight) * 70 : l.kind === 'tracker' ? 140 : l.kind === 'linked' ? 26 : 45)
  link.strength((l: GLink) => l.kind === 'member' ? 0.5 : l.kind === 'tracker' ? 0.008 : l.kind === 'linked' ? 0.4 : 0.03 + l.weight * 0.1)
  fg.d3Force('charge')!.strength((n: GNode) => n.kind === 'profile' ? -260 : -26)
  fg.d3Force('center', null)
  fg.d3Force('cluster', clusterForce())
}

function focusNode(id: string | undefined, zoom = true) {
  const n = id ? data.value.nodes.find(x => x.id === id) : undefined
  if (!fg || !n || n.x === undefined) return
  fg.centerAt(n.x, n.y, 700)
  if (zoom) fg.zoom(Math.max(fg.zoom(), 2.6), 700)
}

const zoomBy = (f: number) => fg?.zoom(fg.zoom() * f, 300)
const fit = () => fg?.zoomToFit(600, 40)
function togglePause() {
  paused.value = !paused.value
  if (paused.value) fg?.pauseAnimation()
  else fg?.resumeAnimation()
}

onMounted(() => {
  readTheme()
  fg = new ForceGraph<GNode, GLink>(el.value!)
    .width(el.value!.clientWidth)
    .height(props.height)
    .backgroundColor('transparent')
    .autoPauseRedraw(false) // keep pulsing rings and particles alive
    .nodeRelSize(1)
    .nodeVal(n => n.r * n.r)
    .nodeLabel(tooltip)
    .nodeCanvasObject((n, ctx, k) => n.kind === 'profile' ? drawProfile(n, ctx, k) : drawClient(n, ctx, k))
    .linkCanvasObjectMode(() => 'replace')
    .linkCanvasObject(drawLink)
    .linkDirectionalParticles(l => l.kind === 'linked' ? 2 : linkTouchesFocus(l) && l.kind !== 'tracker' ? 2 : 0)
    .linkDirectionalParticleWidth(l => l.kind === 'linked' ? 3 : 2.2)
    .linkDirectionalParticleSpeed(l => l.kind === 'linked' ? 0.006 : 0.01)
    .linkDirectionalParticleColor(l => l.kind === 'member' || l.kind === 'tracker' ? profileColor((l.target as GNode).profile) : theme.primary)
    .d3VelocityDecay(0.3)
    .cooldownTime(8000)
    .minZoom(0.3)
    .maxZoom(8)
    .onRenderFramePre(drawClusters)
    .onNodeHover((n) => {
      hovered.value = n?.id
      el.value!.style.cursor = n ? 'pointer' : 'grab'
    })
    .onNodeClick((n) => {
      if (n.kind === 'profile') return emit('toggleProfile', n.profile)
      selected.value = n.id
      emit('select', n.client!)
    })
    .onNodeDragEnd((n) => {
      if (n.kind === 'profile') return // hubs spring back to their anchor
      n.fx = n.x
      n.fy = n.y
    })
    .onNodeRightClick((n) => {
      n.fx = undefined
      n.fy = undefined
      fg!.d3ReheatSimulation()
    })
    .onBackgroundClick(() => { selected.value = undefined })
    .onEngineStop(() => {
      if (!fitted) fit()
      fitted = true
    })
  configureForces()
  fg.graphData(data.value)
  setTimeout(() => !fitted && fit(), 1500)
})

useResizeObserver(el, ([entry]) => fg?.width(entry!.contentRect.width))
watch(() => props.height, h => fg?.height(h))

watch(data, (d) => {
  if (!fg) return
  fitted = false
  fg.graphData(d)
  configureForces()
  fg.d3ReheatSimulation()
  setTimeout(() => !fitted && fit(), 1200)
})

// Re-evaluate particle accessors when the highlighted neighbourhood changes.
watch(focus, () => fg?.linkDirectionalParticles(fg.linkDirectionalParticles()))
watch(selected, id => id && id !== hovered.value && focusNode(id))
watch(() => colorMode.value, () => nextTick(readTheme))

onBeforeUnmount(() => {
  fg?._destructor()
  fg = undefined
})
</script>

<template>
  <div class="relative">
    <div
      ref="el"
      class="w-full cursor-grab"
      :style="{ height: `${height}px` }"
    />
    <div class="bg-card/80 absolute top-3 right-3 flex flex-col gap-1 rounded-lg border p-1 backdrop-blur">
      <Button
        variant="ghost"
        size="icon"
        class="size-7"
        title="Zoom in"
        @click="zoomBy(1.4)"
      >
        <IconPlus />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        class="size-7"
        title="Zoom out"
        @click="zoomBy(1 / 1.4)"
      >
        <IconMinus />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        class="size-7"
        title="Fit to view"
        @click="fit"
      >
        <IconFocusCentered />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        class="size-7"
        :title="paused ? 'Resume animation' : 'Pause animation'"
        @click="togglePause"
      >
        <IconPlayerPlay v-if="paused" />
        <IconPlayerPause v-else />
      </Button>
    </div>
    <p class="text-muted-foreground pointer-events-none absolute bottom-2 left-3 text-[11px]">
      Drag to pin · right-click to release · scroll to zoom · click a profile hub to filter
    </p>
  </div>
</template>
