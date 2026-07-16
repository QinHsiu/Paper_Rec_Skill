<template>
  <div>
    <header class="page-hero">
      <h1 class="page-title">知识图谱</h1>
      <p class="page-lead">
        有关联的实体使用<strong>同一颜色</strong>，并用<strong>同色连线</strong>连接；圆点大小区分类型。
      </p>
    </header>

    <div class="card">
      <div class="kw-legend">
        <span
          v-for="c in clusters"
          :key="c.cluster"
          class="badge cluster-badge"
          :style="{ background: c.color + '22', color: c.color, borderColor: c.color }"
        >
          簇 {{ c.cluster }} · {{ c.count }}
        </span>
      </div>
      <canvas ref="canvas" height="500" style="cursor:pointer"></canvas>
      <p class="muted" style="margin:0.75rem 0 0;font-size:0.85rem">
        大点=实体（关键词/团队/公司等），小点=论文。点击跳转对应链接页。
      </p>
    </div>

    <div class="card" v-if="focus">
      <h3 style="margin-top:0;font-family:var(--font-display)">{{ focus.label }}</h3>
      <p class="muted">{{ typeLabel(focus.type) }} · 簇 {{ focus.cluster }} · {{ focus.detail }}</p>
      <div class="row" v-if="focus.href">
        <RouterLink :to="focus.href"><button class="primary">打开链接</button></RouterLink>
        <RouterLink v-if="focus.edit" :to="focus.edit"><button>编辑</button></RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Chart, registerables } from 'chart.js'
import { getGraph } from '../api'

Chart.register(...registerables)

const TYPE_CN = {
  paper: '论文',
  keyword: '关键词',
  tag: '标签',
  team: '团队',
  company: '公司/机构',
  venue: '来源/会议',
  pack: 'Pack',
}

const canvas = ref(null)
const clusters = ref([])
const focus = ref(null)
const router = useRouter()
let chart

function typeLabel(t) {
  return TYPE_CN[t] || t
}

/** Draw edges under points, same color as related cluster. */
const edgePlugin = {
  id: 'clusterEdges',
  afterDatasetsDraw(chartInst) {
    const meta = chartInst.$edgeMeta
    if (!meta?.edges?.length) return
    const { ctx, scales } = chartInst
    const xScale = scales.x
    const yScale = scales.y
    const pos = meta.positions || {}
    ctx.save()
    ctx.lineWidth = 1.6
    for (const e of meta.edges) {
      const a = pos[e.source]
      const b = pos[e.target]
      if (!a || !b) continue
      ctx.strokeStyle = e.color || '#94a3b8'
      ctx.globalAlpha = 0.55
      ctx.beginPath()
      ctx.moveTo(xScale.getPixelForValue(a.x), yScale.getPixelForValue(a.y))
      ctx.lineTo(xScale.getPixelForValue(b.x), yScale.getPixelForValue(b.y))
      ctx.stroke()
    }
    ctx.restore()
  },
}

onMounted(async () => {
  const data = await getGraph()
  clusters.value = data.clusters || []
  const nodes = data.nodes || []
  const edges = data.edges || []
  const ctx = canvas.value.getContext('2d')
  if (chart) chart.destroy()

  const positions = {}
  for (const n of nodes) {
    positions[n.id] = { x: n.x, y: n.y }
  }

  // One dataset per cluster so related entities share color
  const byCluster = {}
  for (const n of nodes) {
    const c = n.cluster || 'general'
    ;(byCluster[c] || (byCluster[c] = [])).push(n)
  }

  const datasets = Object.keys(byCluster)
    .sort()
    .map((c) => {
      const list = byCluster[c]
      const color = list[0]?.color || '#1a6b7c'
      return {
        label: `簇 ${c}`,
        data: list.map((n) => ({
          x: n.x,
          y: n.y,
          id: n.id,
          type: n.type,
          label: n.label,
          title: n.title,
          name: n.name || n.label,
          added_at: n.added_at,
          paper_count: n.paper_count,
          path: n.path,
          cluster: n.cluster,
          color: n.color,
          href: n.href || n.href_page,
          edit: n.href_edit,
          r: n.type === 'paper' ? 7 : 11,
        })),
        backgroundColor: color,
        borderColor: color,
        pointRadius: (ctx) => ctx.raw?.r ?? 9,
        pointHoverRadius: (ctx) => (ctx.raw?.r ?? 9) + 3,
        pointStyle: (ctx) => (ctx.raw?.type === 'paper' ? 'circle' : 'rectRot'),
      }
    })

  chart = new Chart(ctx, {
    type: 'scatter',
    data: { datasets },
    plugins: [edgePlugin],
    options: {
      responsive: true,
      onClick(evt, elements) {
        if (!elements.length) return
        const el = elements[0]
        const raw = chart.data.datasets[el.datasetIndex].data[el.index]
        focus.value = {
          type: raw.type,
          label: raw.label || raw.name,
          cluster: raw.cluster,
          detail:
            raw.type === 'paper'
              ? `入库 ${raw.added_at || '—'} · ${raw.title || ''}`
              : `关联论文 ${raw.paper_count ?? '—'} 篇`,
          href: raw.href,
          edit: raw.edit,
        }
        if (raw.href) router.push(raw.href)
      },
      plugins: {
        legend: {
          display: true,
          labels: { font: { family: 'Manrope, Noto Sans SC, sans-serif' } },
        },
        tooltip: {
          callbacks: {
            title(items) {
              const r = items[0]?.raw
              return r?.label || r?.name || ''
            },
            label(ctx) {
              const r = ctx.raw || {}
              return [
                `类型: ${typeLabel(r.type)}`,
                `关联簇: ${r.cluster || '—'}`,
                r.type === 'paper'
                  ? `入库: ${r.added_at || '—'}`
                  : `论文数: ${r.paper_count ?? 0}`,
              ]
            },
          },
        },
      },
      scales: {
        x: { display: false },
        y: { display: false },
      },
    },
  })
  chart.$edgeMeta = { edges, positions }
  chart.update('none')
})
</script>

<style scoped>
.kw-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  margin-bottom: 0.85rem;
}
.cluster-badge {
  border: 1px solid;
}
</style>
