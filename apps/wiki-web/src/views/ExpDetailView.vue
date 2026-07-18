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
      <label class="ctrl-row">
        <input type="checkbox" v-model="primaryOnly" />
        仅 primary 指标
      </label>
      <div class="chart-wrap" v-if="metricRows.length">
        <canvas ref="metricsCanvas" height="220"></canvas>
      </div>
      <table class="exp-table" v-if="metricRows.length">
        <thead><tr><th>Metric</th><th>Value</th></tr></thead>
        <tbody>
          <tr v-for="r in metricRows" :key="r[0]"><td>{{ r[0] }}</td><td>{{ r[1] }}</td></tr>
        </tbody>
      </table>
      <p v-else class="muted">无 metrics/summary.json</p>
    </section>

    <section class="card" v-if="allCurveSeries.length || compareExp">
      <h2 style="margin-top:0;font-size:1.15rem">训练曲线（多 run）</h2>
      <div class="ctrl-row" v-if="runNames.length > 1">
        <span class="muted" style="margin-right:0.5rem">Runs:</span>
        <label v-for="n in runNames" :key="n" class="run-chip">
          <input type="checkbox" :value="n" v-model="selectedRuns" />
          {{ n }}
        </label>
      </div>
      <div class="ctrl-row">
        <label>
          对比实验
          <input
            v-model="compareId"
            class="compare-input"
            placeholder="exp_id"
            @keyup.enter="loadCompare"
          />
        </label>
        <button type="button" class="btn-link" @click="loadCompare">加载</button>
        <button type="button" class="btn-link" v-if="compareExp" @click="clearCompare">清除</button>
        <label class="poll-label">
          <input type="checkbox" v-model="pollEnabled" />
          轮询刷新（5s）
        </label>
      </div>
      <div class="chart-wrap" v-if="visibleCurveSeries.length">
        <canvas ref="curvesCanvas" height="280"></canvas>
      </div>
      <p class="muted" style="font-size:0.85rem;margin:0.5rem 0 0">
        多文件约定：<code>metrics/curves.json</code> + <code>curves_&lt;run&gt;.json</code>。
        悬停查看数值；点击图例隐藏系列。
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
import { useRoute } from 'vue-router'
import { Chart, registerables } from 'chart.js'
import { getExperiment } from '../api'

Chart.register(...registerables)

const props = defineProps({ id: { type: String, required: true } })
const route = useRoute()
const exp = ref(null)
const compareExp = ref(null)
const compareId = ref('')
const metricsCanvas = ref(null)
const curvesCanvas = ref(null)
const primaryOnly = ref(true)
const selectedRuns = ref([])
const pollEnabled = ref(false)
let metricsChart
let curvesChart
let pollTimer

const COLORS = ['#1a6b7c', '#c45c26', '#2d6a4f', '#6b4c9a', '#b56576', '#3d5a80', '#8b5a2b', '#4a5568']

function seriesFromCurves(curves, prefix = '') {
  return Object.entries(curves || {}).map(([name, series]) => {
    const values = (series.values || series.y || (Array.isArray(series) ? series : [])).map(Number)
    const steps = series.steps || series.x || values.map((_, i) => i + 1)
    const label = prefix ? `${prefix}/${name}` : name
    return { name: label, seriesKey: name, values, steps }
  }).filter((c) => c.values.length)
}

const runNames = computed(() => {
  const runs = exp.value?.curve_runs || []
  if (runs.length) return runs.map((r) => r.name)
  if (exp.value?.curves && Object.keys(exp.value.curves).length) return ['default']
  return []
})

const allCurveSeries = computed(() => {
  const runs = exp.value?.curve_runs || []
  if (runs.length) {
    return runs.flatMap((r) => seriesFromCurves(r.curves, r.name))
  }
  return seriesFromCurves(exp.value?.curves || {})
})

const visibleCurveSeries = computed(() => {
  const sel = new Set(selectedRuns.value.length ? selectedRuns.value : runNames.value)
  let series = allCurveSeries.value.filter((c) => {
    const run = c.name.includes('/') ? c.name.split('/')[0] : 'default'
    return sel.has(run)
  })
  if (compareExp.value) {
    const cruns = compareExp.value.curve_runs || []
    const extra = cruns.length
      ? cruns.flatMap((r) => seriesFromCurves(r.curves, `cmp:${compareExp.value.id}/${r.name}`))
      : seriesFromCurves(compareExp.value.curves || {}, `cmp:${compareExp.value.id}`)
    series = series.concat(extra)
  }
  if (primaryOnly.value) {
    const primary = exp.value?.metrics?.primary || {}
    const keys = new Set(Object.keys(primary).filter((k) => typeof primary[k] !== 'object'))
    if (keys.size) {
      series = series.filter((c) => keys.has(c.seriesKey) || c.seriesKey === 'train_loss' || c.seriesKey.startsWith('val_'))
    }
  }
  return series
})

const metricRows = computed(() => {
  const m = exp.value?.metrics || {}
  const src = primaryOnly.value && m.primary ? m.primary : (m.primary || m)
  return Object.entries(src).filter(
    ([k, v]) => k !== 'summary' && k !== 'target_met' && k !== 'run_id' && typeof v !== 'object',
  )
})

const figures = computed(() => exp.value?.figures || [])

function destroyCharts() {
  metricsChart?.destroy()
  curvesChart?.destroy()
  metricsChart = null
  curvesChart = null
}

function renderCharts() {
  destroyCharts()
  if (metricsCanvas.value && metricRows.value.length) {
    const labels = metricRows.value.map((r) => r[0])
    const values = metricRows.value.map((r) => Number(r[1]) || 0)
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
  if (curvesCanvas.value && visibleCurveSeries.value.length) {
    curvesChart = new Chart(curvesCanvas.value, {
      type: 'line',
      data: {
        datasets: visibleCurveSeries.value.map((c, i) => ({
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
  if (!selectedRuns.value.length && runNames.value.length) {
    selectedRuns.value = [...runNames.value]
  }
  const qCompare = route.query.compare
  if (typeof qCompare === 'string' && qCompare && !compareId.value) {
    compareId.value = qCompare
    await loadCompare()
  }
  if (route.query.poll === '5' || route.query.poll === '5s') {
    pollEnabled.value = true
  }
  await nextTick()
  renderCharts()
}

async function loadCompare() {
  const id = (compareId.value || '').trim()
  if (!id) return
  compareExp.value = await getExperiment(id)
  await nextTick()
  renderCharts()
}

function clearCompare() {
  compareExp.value = null
  compareId.value = ''
  renderCharts()
}

function stopPoll() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function startPoll() {
  stopPoll()
  if (!pollEnabled.value) return
  pollTimer = setInterval(async () => {
    exp.value = await getExperiment(props.id)
    if (compareExp.value?.id) {
      compareExp.value = await getExperiment(compareExp.value.id)
    }
    await nextTick()
    renderCharts()
  }, 5000)
}

onMounted(load)
watch(() => props.id, load)
watch([primaryOnly, selectedRuns, visibleCurveSeries], async () => {
  await nextTick()
  renderCharts()
})
watch(pollEnabled, (on) => {
  if (on) startPoll()
  else stopPoll()
})
onBeforeUnmount(() => {
  destroyCharts()
  stopPoll()
})
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
.ctrl-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem 1rem;
  align-items: center;
  margin-bottom: 0.75rem;
  font-size: 0.9rem;
}
.run-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}
.compare-input {
  margin-left: 0.35rem;
  padding: 0.2rem 0.4rem;
  min-width: 10rem;
}
.btn-link {
  background: none;
  border: none;
  color: var(--accent, #1a6b7c);
  cursor: pointer;
  text-decoration: underline;
  padding: 0;
  font: inherit;
}
.poll-label {
  margin-left: auto;
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
