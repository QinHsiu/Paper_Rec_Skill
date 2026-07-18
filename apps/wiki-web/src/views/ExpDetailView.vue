<template>
  <div v-if="exp">
    <header class="page-hero">
      <p class="muted" style="margin:0 0 0.4rem">
        <RouterLink to="/experiments">← 实验列表</RouterLink>
      </p>
      <h1 class="page-title">{{ exp.title || exp.id }}</h1>
      <p class="page-lead">
        <code>content/exp/{{ exp.id }}</code>
        <span v-if="exp.wiki_path"> · Wiki <code>{{ exp.wiki_path }}</code></span>
      </p>
      <div class="meta-line">
        <span class="badge" :class="exp.target_met ? 'badge-reading' : ''">
          {{ exp.target_met ? 'target_score 达标' : '未达标' }}
        </span>
        <span v-for="p in exp.paper_refs || []" :key="p">
          <RouterLink :to="`/page/${p}`">{{ p }}</RouterLink>
        </span>
        <RouterLink
          v-for="tid in exp.thread_ids || []"
          :key="tid"
          :to="`/threads/${tid}`"
          class="path-chip"
        >主线 · {{ tid }}</RouterLink>
      </div>
    </header>

    <section class="card">
      <h2 style="margin-top:0;font-size:1.15rem">指标</h2>
      <div class="chart-wrap" v-if="primaryRows.length">
        <canvas ref="metricsCanvas" height="220"></canvas>
      </div>
      <table class="exp-table" v-if="primaryRows.length">
        <thead><tr><th>Metric</th><th>Value</th></tr></thead>
        <tbody>
          <tr v-for="r in primaryRows" :key="r[0]"><td>{{ r[0] }}</td><td>{{ r[1] }}</td></tr>
        </tbody>
      </table>
      <p v-else class="muted">无 metrics/summary.json</p>
    </section>

    <section class="card" v-if="curveSeries.length">
      <h2 style="margin-top:0;font-size:1.15rem">训练曲线（交互）</h2>
      <div class="chart-wrap">
        <canvas ref="curvesCanvas" height="280"></canvas>
      </div>
      <p class="muted" style="font-size:0.85rem;margin:0.5rem 0 0">
        悬停查看数值；可点击图例隐藏系列。
      </p>
    </section>

    <section class="card" v-if="figures.length">
      <h2 style="margin-top:0;font-size:1.15rem">图表</h2>
      <div class="fig-grid">
        <figure v-for="f in figures" :key="f.path" class="fig-item">
          <img :src="f.url" :alt="f.name" loading="lazy" />
          <figcaption>
            <code>{{ f.path }}</code>
          </figcaption>
        </figure>
      </div>
    </section>

    <section class="card" v-if="exp.final_md">
      <h2 style="margin-top:0;font-size:1.15rem">最终报告</h2>
      <pre class="exp-md">{{ exp.final_md }}</pre>
    </section>

    <section class="card" v-if="exp.files && exp.files.length">
      <h2 style="margin-top:0;font-size:1.15rem">产物文件</h2>
      <ul style="margin:0;padding-left:1.1rem">
        <li v-for="f in exp.files" :key="f.path">
          <code>{{ f.path }}</code>
          <span class="muted"> · {{ f.size }} B</span>
        </li>
      </ul>
    </section>
  </div>
  <p v-else class="card muted">加载中…</p>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Chart, registerables } from 'chart.js'
import { getExperiment } from '../api'

Chart.register(...registerables)

const props = defineProps({ id: { type: String, required: true } })
const exp = ref(null)
const metricsCanvas = ref(null)
const curvesCanvas = ref(null)
let metricsChart
let curvesChart

const COLORS = ['#1a6b7c', '#c45c26', '#2d6a4f', '#6b4c9a', '#b56576', '#3d5a80']

const primaryRows = computed(() => {
  const m = exp.value?.metrics?.primary || exp.value?.metrics || {}
  return Object.entries(m).filter(([k, v]) => k !== 'summary' && k !== 'target_met' && k !== 'run_id' && typeof v !== 'object')
})

const figures = computed(() => exp.value?.figures || [])

const curveSeries = computed(() => {
  const curves = exp.value?.curves || {}
  return Object.entries(curves).map(([name, series]) => {
    const values = (series.values || series.y || (Array.isArray(series) ? series : [])).map(Number)
    const steps = series.steps || series.x || values.map((_, i) => i + 1)
    return { name, values, steps }
  }).filter((c) => c.values.length)
})

function destroyCharts() {
  metricsChart?.destroy()
  curvesChart?.destroy()
  metricsChart = null
  curvesChart = null
}

function renderCharts() {
  destroyCharts()
  if (metricsCanvas.value && primaryRows.value.length) {
    const labels = primaryRows.value.map((r) => r[0])
    const values = primaryRows.value.map((r) => Number(r[1]) || 0)
    metricsChart = new Chart(metricsCanvas.value, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'metrics',
            data: values,
            backgroundColor: labels.map((_, i) => COLORS[i % COLORS.length] + '99'),
            borderColor: labels.map((_, i) => COLORS[i % COLORS.length]),
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } },
      },
    })
  }
  if (curvesCanvas.value && curveSeries.value.length) {
    curvesChart = new Chart(curvesCanvas.value, {
      type: 'line',
      data: {
        datasets: curveSeries.value.map((c, i) => ({
          label: c.name,
          data: c.values.map((y, j) => ({ x: Number(c.steps[j] ?? j + 1), y })),
          borderColor: COLORS[i % COLORS.length],
          backgroundColor: COLORS[i % COLORS.length] + '33',
          tension: 0.15,
          pointRadius: 2,
        })),
      },
      options: {
        responsive: true,
        interaction: { mode: 'nearest', intersect: false },
        plugins: { legend: { position: 'bottom' } },
        scales: {
          x: { type: 'linear', title: { display: true, text: 'step' } },
          y: { title: { display: true, text: 'value' } },
        },
      },
    })
  }
}

async function load() {
  exp.value = await getExperiment(props.id)
  await nextTick()
  renderCharts()
}

onMounted(load)
watch(() => props.id, load)
onBeforeUnmount(destroyCharts)
</script>

<style scoped>
.exp-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
  margin-top: 0.75rem;
}
.exp-table th,
.exp-table td {
  text-align: left;
  padding: 0.35rem 0.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}
.chart-wrap {
  position: relative;
  width: 100%;
  max-width: 820px;
}
.exp-md {
  white-space: pre-wrap;
  font-family: var(--font-prose, Georgia, serif);
  font-size: 0.92rem;
  line-height: 1.55;
  margin: 0;
}
.fig-grid {
  display: grid;
  gap: 1.25rem;
}
.fig-item {
  margin: 0;
}
.fig-item img {
  display: block;
  width: 100%;
  max-width: 720px;
  height: auto;
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.08);
}
.fig-item figcaption {
  margin-top: 0.4rem;
  font-size: 0.85rem;
  color: var(--muted, #666);
}
</style>
