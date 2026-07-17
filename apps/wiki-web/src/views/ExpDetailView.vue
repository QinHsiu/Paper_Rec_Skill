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
      </div>
    </header>

    <section class="card">
      <h2 style="margin-top:0;font-size:1.15rem">指标</h2>
      <table class="exp-table" v-if="primaryRows.length">
        <thead><tr><th>Metric</th><th>Value</th></tr></thead>
        <tbody>
          <tr v-for="r in primaryRows" :key="r[0]"><td>{{ r[0] }}</td><td>{{ r[1] }}</td></tr>
        </tbody>
      </table>
      <p v-else class="muted">无 metrics/summary.json</p>
    </section>

    <section class="card" v-if="curveBlocks.length">
      <h2 style="margin-top:0;font-size:1.15rem">训练曲线</h2>
      <div v-for="c in curveBlocks" :key="c.name" style="margin-bottom:1rem">
        <strong>{{ c.name }}</strong>
        <div class="spark">{{ c.spark }}</div>
        <p class="muted" style="font-size:0.85rem;margin:0.35rem 0 0">
          last={{ c.last }} · n={{ c.n }}
        </p>
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
import { computed, onMounted, ref } from 'vue'
import { getExperiment } from '../api'

const props = defineProps({ id: { type: String, required: true } })
const exp = ref(null)

const BLOCKS = '▁▂▃▄▅▆▇█'
function spark(values) {
  if (!values?.length) return '(empty)'
  const lo = Math.min(...values)
  const hi = Math.max(...values)
  const span = hi - lo || 1
  return values
    .slice(-32)
    .map((v) => BLOCKS[Math.round(((v - lo) / span) * (BLOCKS.length - 1))])
    .join('')
}

const primaryRows = computed(() => {
  const m = exp.value?.metrics?.primary || exp.value?.metrics || {}
  return Object.entries(m).filter(([k]) => k !== 'summary' && k !== 'target_met' && k !== 'run_id')
})

const curveBlocks = computed(() => {
  const curves = exp.value?.curves || {}
  return Object.entries(curves).map(([name, series]) => {
    const values = (series.values || series.y || series || []).map(Number)
    return {
      name,
      spark: spark(values),
      last: values.length ? values[values.length - 1] : '—',
      n: values.length,
    }
  })
})

onMounted(async () => {
  exp.value = await getExperiment(props.id)
})
</script>

<style scoped>
.exp-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}
.exp-table th,
.exp-table td {
  text-align: left;
  padding: 0.35rem 0.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}
.spark {
  font-family: ui-monospace, monospace;
  font-size: 1.35rem;
  letter-spacing: 0.02em;
  margin-top: 0.35rem;
}
.exp-md {
  white-space: pre-wrap;
  font-family: var(--font-prose, Georgia, serif);
  font-size: 0.92rem;
  line-height: 1.55;
  margin: 0;
}
</style>
