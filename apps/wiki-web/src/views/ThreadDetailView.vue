<template>
  <div v-if="thread">
    <header class="page-hero">
      <p class="muted" style="margin:0 0 0.4rem">
        <RouterLink to="/threads">← 研究主线</RouterLink>
      </p>
      <h1 class="page-title">{{ thread.title || thread.thread_id }}</h1>
      <p class="page-lead">
        <code>content/threads/{{ thread.thread_id }}</code>
      </p>
      <div class="meta-line">
        <span class="badge badge-reading">{{ thread.status }}</span>
        <span>claims {{ (thread.claims || []).length }}</span>
        <span>gaps {{ (thread.evidence_gaps || []).length }}</span>
        <span v-if="thread.watch">watch {{ thread.watch.enabled ? 'on' : 'off' }}</span>
      </div>
      <div class="row" style="margin-top:0.75rem;gap:0.5rem;flex-wrap:wrap">
        <button class="primary" :disabled="deltaBusy" @click="runDelta('auto')">
          {{ deltaBusy ? 'Delta…' : '运行 Delta' }}
        </button>
        <button :disabled="deltaBusy" @click="runDelta('gap_focus')">Gap focus</button>
        <button :disabled="deltaBusy" @click="runDelta('diff_brief')">Diff brief</button>
        <button :disabled="suggestBusy" @click="loadSuggestions">主张建议</button>
        <button :disabled="rwBusy" @click="makeRelatedWork">Related Work 提纲</button>
        <button :disabled="draftBusy" @click="makePaperDraft">多章草稿包</button>
        <button @click="exportThreadBib">导出 BibTeX</button>
      </div>
      <p v-if="actionMsg" class="muted" style="margin:0.5rem 0 0">{{ actionMsg }}</p>
    </header>

    <section class="card" v-if="coverage">
      <h2 style="margin-top:0;font-size:1.15rem">证据覆盖提示</h2>
      <p style="margin:0;line-height:1.55">{{ coverage.advice }}</p>
      <ul style="margin:0.5rem 0 0;padding-left:1.1rem;font-size:0.9rem" v-if="(coverage.claims || []).length">
        <li v-for="c in coverage.claims" :key="c.claim_id" style="margin-bottom:0.35rem">
          <code>{{ c.claim_id }}</code>
          · 高置信 {{ c.high_confidence }} · 低置信 {{ c.low_confidence }}
          — {{ c.advice }}
        </li>
      </ul>
    </section>

    <section class="card" v-if="deltaResult">
      <h2 style="margin-top:0;font-size:1.15rem">最近 Delta · {{ deltaResult.mode }}</h2>
      <p class="muted" style="margin-top:0" v-if="deltaResult.delta_path">
        <code>{{ deltaResult.delta_path }}</code>
      </p>
      <ul style="margin:0;padding-left:1.1rem" v-if="(deltaResult.candidates || []).length">
        <li v-for="c in deltaResult.candidates" :key="c.path">
          R={{ c.R }} · <RouterLink :to="`/page/${c.path}`">{{ c.path }}</RouterLink> — {{ c.title }}
        </li>
      </ul>
      <p v-else class="muted">无新候选（或低于阈值）。</p>
    </section>

    <section class="card" v-if="(suggestions || []).length">
      <h2 style="margin-top:0;font-size:1.15rem">主张更新建议（需确认）</h2>
      <div v-for="s in suggestions" :key="s.claim_id" class="week-item">
        <div class="row" style="justify-content:space-between;align-items:center">
          <div>
            <code>{{ s.claim_id }}</code> → <strong>{{ s.status }}</strong>
            <p class="muted" style="margin:0.25rem 0 0;font-size:0.88rem">{{ s.reason }}</p>
          </div>
          <button class="primary" @click="acceptClaim(s)">接受</button>
        </div>
      </div>
    </section>

    <section class="card">
      <h2 style="margin-top:0;font-size:1.15rem">假设</h2>
      <p style="margin:0;line-height:1.65;white-space:pre-wrap">{{ thread.hypothesis || '—' }}</p>
    </section>

    <section class="card">
      <h2 style="margin-top:0;font-size:1.15rem">认知地图（Claim–Evidence）</h2>
      <div class="ctrl-row">
        <label v-for="t in typeFilters" :key="t" class="run-chip">
          <input type="checkbox" :value="t" v-model="showTypes" />
          {{ t }}
        </label>
        <label class="run-chip">
          <input type="checkbox" v-model="acceptedOnly" />
          仅 accepted 证据
        </label>
      </div>
      <div class="chart-wrap" v-if="graphNodes.length">
        <canvas ref="graphCanvas" height="360"></canvas>
      </div>
      <p v-else class="muted">尚无图节点。挂接 claim / evidence / 论文后自动出现。</p>
      <p class="muted" style="font-size:0.85rem;margin:0.5rem 0 0">
        节点：thread / claim / evidence / paper / experiment。点击图例外区域可查看下方焦点。
      </p>
      <div v-if="graphFocus" class="week-item" style="margin-top:0.75rem">
        <strong>{{ graphFocus.label }}</strong>
        <span class="badge" style="margin-left:0.35rem">{{ graphFocus.type }}</span>
        <p class="muted" style="margin:0.35rem 0 0;font-size:0.88rem">{{ graphFocus.detail }}</p>
        <RouterLink v-if="graphFocus.href" :to="graphFocus.href" class="path-chip">打开</RouterLink>
      </div>
    </section>

    <section class="card" v-if="(thread.claims || []).length">
      <h2 style="margin-top:0;font-size:1.15rem">主张 Claims</h2>
      <ul style="margin:0;padding-left:1.1rem">
        <li v-for="c in thread.claims" :key="c.id" style="margin-bottom:0.4rem">
          <code>{{ c.id }}</code>
          <span class="badge" style="margin-left:0.35rem">{{ c.status }}</span>
          {{ c.text }}
          <span class="muted" v-if="(c.evidence_ids || []).length">
            · evidences {{ (c.evidence_ids || []).length }}
          </span>
        </li>
      </ul>
    </section>

    <section class="card">
      <h2 style="margin-top:0;font-size:1.15rem">论断–证据列表</h2>
      <p class="muted" style="margin-top:0;font-size:0.88rem">
        claim → evidence → paper / experiment（在论文页选中文本可挂接）
      </p>
      <div class="ctrl-row">
        <label class="run-chip">
          gate
          <select v-model="evGateFilter">
            <option value="">全部</option>
            <option value="accepted">accepted</option>
            <option value="suggested">suggested</option>
          </select>
        </label>
        <label class="run-chip">
          conf
          <select v-model="evConfFilter">
            <option value="all">全部</option>
            <option value="high">≥0.8 高置信</option>
            <option value="low">&lt;0.8 低置信</option>
          </select>
        </label>
      </div>
      <div v-if="filteredEvidences.length">
        <div
          v-for="e in filteredEvidences"
          :key="e.evidence_id"
          class="week-item"
          :class="evidenceClass(e)"
        >
          <div class="meta-line">
            <span class="badge">{{ e.evidence_id }}</span>
            <span v-if="isHighConf(e)" title="高置信">✅</span>
            <span>claim {{ e.claim_id }}</span>
            <span>{{ e.stance }}</span>
            <span v-if="e.support_status">status={{ e.support_status }}</span>
            <span v-if="e.confidence != null" :class="isHighConf(e) ? 'conf-high' : 'conf-low'">
              conf={{ e.confidence }}
            </span>
            <span v-if="e.citation_key">[@{{ e.citation_key }}]</span>
            <span v-if="e.page != null">p.{{ e.page }}</span>
            <span v-if="e.evidence_level">lvl={{ e.evidence_level }}</span>
            <span>gate={{ e.gate }}</span>
            <span>{{ e.kind }}</span>
          </div>
          <p style="margin:0.35rem 0 0;font-size:0.9rem;line-height:1.5;white-space:pre-wrap">
            {{ e.quote || (e.metric_key ? `${e.metric_key}=${e.metric_value}` : '—') }}
          </p>
          <div class="meta-line" style="margin-top:0.35rem">
            <RouterLink v-if="e.paper_path" :to="`/page/${e.paper_path}`" class="path-chip">
              {{ e.paper_path }}
            </RouterLink>
            <RouterLink v-if="e.exp_id" :to="`/experiments/${e.exp_id}`" class="path-chip">
              exp {{ e.exp_id }}
            </RouterLink>
            <button
              v-if="e.gate === 'suggested'"
              class="primary"
              style="margin-left:auto"
              @click="acceptEvidence(e)"
            >接受证据</button>
          </div>
        </div>
      </div>
      <p v-else class="muted" style="margin:0">
        尚无证据（或被筛选过滤）。打开关联论文，选中段落后点「挂到主线」。
      </p>
    </section>

    <section class="card" v-if="draftPreview">
      <h2 style="margin-top:0;font-size:1.15rem">多章草稿包</h2>
      <p class="muted" style="margin-top:0">
        <code>{{ draftPreview.dir }}</code>
        · Markdown 可溯源框架（非 LaTeX 成稿）
      </p>
      <ul style="margin:0;padding-left:1.1rem;font-size:0.9rem">
        <li v-for="(p, name) in draftPreview.paths" :key="name">
          <code>{{ name }}</code> → {{ p }}
        </li>
      </ul>
    </section>

    <section class="card" v-if="rwPreview">
      <h2 style="margin-top:0;font-size:1.15rem">Related Work 提纲</h2>
      <p class="muted" style="margin-top:0"><code>{{ rwPreview.path }}</code></p>
      <pre class="exp-md">{{ rwPreview.markdown }}</pre>
    </section>

    <section class="card" v-if="bibPreview">
      <h2 style="margin-top:0;font-size:1.15rem">BibTeX</h2>
      <pre class="exp-md">{{ bibPreview }}</pre>
    </section>

    <section class="card" v-if="(thread.open_questions || []).length">
      <h2 style="margin-top:0;font-size:1.15rem">开放问题</h2>
      <ul style="margin:0;padding-left:1.1rem">
        <li v-for="q in thread.open_questions" :key="q.id">
          <code>{{ q.id }}</code> {{ q.text }}
        </li>
      </ul>
    </section>

    <section class="card" v-if="(thread.evidence_gaps || []).length">
      <h2 style="margin-top:0;font-size:1.15rem">证据缺口</h2>
      <ul style="margin:0;padding-left:1.1rem">
        <li v-for="(g, i) in thread.evidence_gaps" :key="i">
          claim <code>{{ g.claim_id }}</code> · {{ g.need }} — {{ g.note }}
        </li>
      </ul>
    </section>

    <section class="card">
      <h2 style="margin-top:0;font-size:1.15rem">关联论文</h2>
      <div class="meta-line" v-if="(thread.paper_paths || []).length">
        <div v-for="p in thread.paper_paths" :key="p" style="display:flex;align-items:center;gap:0.35rem;flex-wrap:wrap;margin-bottom:0.35rem">
          <RouterLink :to="`/page/${p}`" class="path-chip">{{ p }}</RouterLink>
          <button style="font-size:0.8rem" @click="sendFeedback('accept', p)">接受</button>
          <button style="font-size:0.8rem" @click="sendFeedback('pin', p)">钉住</button>
          <button style="font-size:0.8rem" @click="sendFeedback('skip', p)">略过</button>
        </div>
      </div>
      <p v-else class="muted" style="margin:0">暂无。sync-report --thread 或手动挂接。</p>
      <p class="muted" style="font-size:0.85rem;margin:0.5rem 0 0">
        反馈写入 events（accept/skip/pin），并轻量调整 seed_terms。
      </p>
    </section>

    <section class="card">
      <h2 style="margin-top:0;font-size:1.15rem">关联实验</h2>
      <div class="meta-line" v-if="(thread.experiment_ids || []).length">
        <RouterLink
          v-for="e in thread.experiment_ids"
          :key="e"
          :to="`/experiments/${e}`"
          class="path-chip"
        >{{ e }}</RouterLink>
      </div>
      <p v-else class="muted" style="margin:0">暂无。sync-exp --thread 可挂接。</p>
    </section>

    <section class="card">
      <h2 style="margin-top:0;font-size:1.15rem">演进时间线</h2>
      <div v-if="timelineDays.length">
        <div v-for="day in timelineDays" :key="day.day" style="margin-bottom:1rem">
          <h3 style="margin:0 0 0.5rem;font-size:1rem;font-family:var(--font-display)">{{ day.day }}</h3>
          <div v-for="(ev, i) in day.events" :key="i" class="week-item">
            <div class="meta-line">
              <span class="badge">{{ ev.kind }}</span>
              <span>{{ ev.ts }}</span>
              <span v-if="ev.gate">gate={{ ev.gate }}</span>
              <span v-if="ev.R != null">R={{ ev.R }}</span>
              <span v-if="ev.mode">mode={{ ev.mode }}</span>
            </div>
            <p class="muted" style="margin:0.35rem 0 0;font-size:0.88rem">
              <template v-if="ev.kind === 'query_iter'">
                round {{ ev.round }} · {{ ev.path_id || 'path' }}
                · hits {{ ev.raw_hits ?? '—' }} → kept {{ ev.kept ?? '—' }}
                <span v-if="(ev.queries || []).length"> · {{ (ev.queries || []).slice(0, 2).join(' | ') }}</span>
              </template>
              <template v-else-if="ev.path">{{ ev.path }}</template>
              <template v-else-if="ev.experiment_id">exp {{ ev.experiment_id }}</template>
              <template v-else-if="ev.text">{{ ev.text }}</template>
              <template v-else-if="ev.rationale">{{ (ev.rationale || []).join(' · ') }}</template>
              <template v-else>{{ summarize(ev) }}</template>
            </p>
          </div>
        </div>
      </div>
      <p v-else class="muted" style="margin:0">尚无事件。</p>
    </section>
  </div>
  <p v-else class="card muted">加载中…</p>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Chart, registerables } from 'chart.js'
import {
  acceptThreadClaim,
  exportBibtex,
  generatePaperDraft,
  generateRelatedWork,
  getEvidenceCoverage,
  getThread,
  getThreadClaimSuggestions,
  getThreadGraph,
  runThreadDelta,
  setThreadEvidenceGate,
  threadFeedback,
} from '../api'

Chart.register(...registerables)

const props = defineProps({ id: { type: String, required: true } })
const thread = ref(null)
const graph = ref(null)
const coverage = ref(null)
const deltaResult = ref(null)
const suggestions = ref([])
const deltaBusy = ref(false)
const suggestBusy = ref(false)
const rwBusy = ref(false)
const draftBusy = ref(false)
const actionMsg = ref('')
const rwPreview = ref(null)
const draftPreview = ref(null)
const bibPreview = ref('')
const graphCanvas = ref(null)
const graphFocus = ref(null)
const showTypes = ref(['thread', 'claim', 'evidence', 'paper', 'experiment'])
const typeFilters = ['thread', 'claim', 'evidence', 'paper', 'experiment']
const acceptedOnly = ref(false)
const evGateFilter = ref('')
const evConfFilter = ref('all')
let graphChart

const evidences = computed(() => thread.value?.evidences || [])

function isHighConf(e) {
  const c = e?.confidence
  return c != null && Number(c) >= 0.8
}

function evidenceClass(e) {
  if (isHighConf(e)) return 'ev-high'
  if (e?.confidence != null && Number(e.confidence) < 0.8) return 'ev-low'
  return ''
}

const filteredEvidences = computed(() => {
  let rows = evidences.value
  if (evGateFilter.value) {
    rows = rows.filter((e) => e.gate === evGateFilter.value)
  }
  if (evConfFilter.value === 'high') {
    rows = rows.filter((e) => isHighConf(e))
  } else if (evConfFilter.value === 'low') {
    rows = rows.filter((e) => e.confidence != null && Number(e.confidence) < 0.8)
  }
  return rows
})

const timelineDays = computed(() => graph.value?.timeline || [])

const graphNodes = computed(() => {
  let nodes = graph.value?.nodes || []
  const types = new Set(showTypes.value)
  nodes = nodes.filter((n) => types.has(n.type))
  if (acceptedOnly.value) {
    const drop = new Set(
      (graph.value?.nodes || [])
        .filter((n) => n.type === 'evidence' && n.gate !== 'accepted')
        .map((n) => n.id),
    )
    nodes = nodes.filter((n) => !drop.has(n.id))
  }
  return nodes
})

const graphEdges = computed(() => {
  const ids = new Set(graphNodes.value.map((n) => n.id))
  return (graph.value?.edges || []).filter((e) => ids.has(e.source) && ids.has(e.target))
})

function summarize(ev) {
  try {
    return JSON.stringify(ev)
  } catch {
    return String(ev)
  }
}

const edgePlugin = {
  id: 'threadEdges',
  afterDatasetsDraw(chartInst) {
    const meta = chartInst.$edgeMeta
    if (!meta?.edges?.length) return
    const { ctx, scales } = chartInst
    const pos = meta.positions || {}
    ctx.save()
    ctx.lineWidth = 1.4
    for (const e of meta.edges) {
      const a = pos[e.source]
      const b = pos[e.target]
      if (!a || !b) continue
      ctx.strokeStyle = '#94a3b8'
      ctx.globalAlpha = 0.5
      ctx.beginPath()
      ctx.moveTo(scales.x.getPixelForValue(a.x), scales.y.getPixelForValue(a.y))
      ctx.lineTo(scales.x.getPixelForValue(b.x), scales.y.getPixelForValue(b.y))
      ctx.stroke()
    }
    ctx.restore()
  },
}

function renderGraph() {
  graphChart?.destroy()
  graphChart = null
  if (!graphCanvas.value || !graphNodes.value.length) return
  const positions = {}
  for (const n of graphNodes.value) positions[n.id] = { x: n.x, y: n.y }
  const byType = {}
  for (const n of graphNodes.value) {
    ;(byType[n.type] || (byType[n.type] = [])).push(n)
  }
  const datasets = Object.keys(byType).map((t) => {
    const list = byType[t]
    return {
      label: t,
      data: list.map((n) => ({ x: n.x, y: n.y, raw: n })),
      backgroundColor: list[0]?.color || '#1a6b7c',
      pointRadius: t === 'thread' ? 10 : t === 'claim' ? 8 : 6,
    }
  })
  graphChart = new Chart(graphCanvas.value, {
    type: 'scatter',
    data: { datasets },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'bottom' },
        tooltip: {
          callbacks: {
            label(ctx) {
              const n = ctx.raw?.raw
              return n ? `${n.type}: ${n.label}` : ''
            },
          },
        },
      },
      scales: {
        x: { min: 0, max: 1, display: false },
        y: { min: 0, max: 1, display: false },
      },
      onClick(_e, elems) {
        if (!elems.length) return
        const ds = elems[0].datasetIndex
        const i = elems[0].index
        graphFocus.value = graphChart.data.datasets[ds].data[i].raw
      },
    },
    plugins: [edgePlugin],
  })
  graphChart.$edgeMeta = { edges: graphEdges.value, positions }
}

async function load() {
  thread.value = await getThread(props.id)
  graph.value = await getThreadGraph(props.id)
  try {
    coverage.value = await getEvidenceCoverage(props.id)
  } catch {
    coverage.value = null
  }
  await nextTick()
  renderGraph()
}

async function acceptEvidence(e) {
  try {
    await setThreadEvidenceGate(props.id, e.evidence_id, 'accepted')
    actionMsg.value = `已接受证据 ${e.evidence_id}`
    await load()
  } catch (err) {
    actionMsg.value = err?.response?.data?.detail || err.message || String(err)
  }
}

async function runDelta(mode) {
  deltaBusy.value = true
  actionMsg.value = ''
  try {
    deltaResult.value = await runThreadDelta(props.id, { mode, persist: true })
    actionMsg.value = `Delta 完成 · 候选 ${(deltaResult.value.candidates || []).length} 篇`
    await load()
    if ((deltaResult.value.claim_suggestions || []).length) {
      suggestions.value = deltaResult.value.claim_suggestions
    }
  } catch (e) {
    actionMsg.value = e?.response?.data?.detail || e.message || String(e)
  } finally {
    deltaBusy.value = false
  }
}

async function loadSuggestions() {
  suggestBusy.value = true
  try {
    const data = await getThreadClaimSuggestions(props.id)
    suggestions.value = data.suggestions || []
    actionMsg.value = suggestions.value.length ? `有 ${suggestions.value.length} 条建议` : '暂无建议'
  } catch (e) {
    actionMsg.value = e?.response?.data?.detail || e.message || String(e)
  } finally {
    suggestBusy.value = false
  }
}

async function acceptClaim(s) {
  try {
    await acceptThreadClaim(props.id, {
      claim_id: s.claim_id,
      status: s.status,
      reason: s.reason || '',
    })
    suggestions.value = suggestions.value.filter((x) => x.claim_id !== s.claim_id)
    actionMsg.value = `已接受 ${s.claim_id} → ${s.status}`
    await load()
  } catch (e) {
    actionMsg.value = e?.response?.data?.detail || e.message || String(e)
  }
}

async function makeRelatedWork() {
  rwBusy.value = true
  try {
    rwPreview.value = await generateRelatedWork(props.id)
    actionMsg.value = `已写入 ${rwPreview.value.path}`
    await load()
  } catch (e) {
    actionMsg.value = e?.response?.data?.detail || e.message || String(e)
  } finally {
    rwBusy.value = false
  }
}

async function makePaperDraft() {
  draftBusy.value = true
  try {
    draftPreview.value = await generatePaperDraft(props.id, 'generic')
    actionMsg.value = `已写入草稿包 ${draftPreview.value.dir}`
    await load()
  } catch (e) {
    actionMsg.value = e?.response?.data?.detail || e.message || String(e)
  } finally {
    draftBusy.value = false
  }
}

async function exportThreadBib() {
  const paths = thread.value?.paper_paths || []
  if (!paths.length) {
    actionMsg.value = '无线论文可导出'
    return
  }
  try {
    const data = await exportBibtex(paths)
    bibPreview.value = data.bibtex || ''
    actionMsg.value = `BibTeX ${data.count} 条` + (data.warnings?.length ? ` · 警告 ${data.warnings.length}` : '')
  } catch (e) {
    actionMsg.value = e?.response?.data?.detail || e.message || String(e)
  }
}

async function sendFeedback(action, path) {
  try {
    const out = await threadFeedback(props.id, { action, path })
    actionMsg.value = `反馈 ${action} · ${path}` + (out.seed_terms ? ` · seeds ${out.seed_terms.length}` : '')
    await load()
  } catch (e) {
    actionMsg.value = e?.response?.data?.detail || e.message || String(e)
  }
}

onMounted(load)
watch(() => props.id, load)
watch([showTypes, acceptedOnly, graph], async () => {
  await nextTick()
  renderGraph()
})
onBeforeUnmount(() => graphChart?.destroy())
</script>

<style scoped>
.chart-wrap {
  position: relative;
  width: 100%;
  max-width: 720px;
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
.exp-md {
  white-space: pre-wrap;
  font-family: ui-monospace, monospace;
  font-size: 0.85rem;
  line-height: 1.45;
  margin: 0;
  max-height: 28rem;
  overflow: auto;
}
.ev-high {
  border-left: 3px solid #15803d;
  padding-left: 0.65rem;
}
.ev-low {
  opacity: 0.72;
  border-left: 3px solid #94a3b8;
  padding-left: 0.65rem;
}
.conf-high {
  color: #15803d;
  font-weight: 600;
}
.conf-low {
  color: #64748b;
}
</style>
