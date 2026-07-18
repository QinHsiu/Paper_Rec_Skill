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
      </div>
      <p v-if="actionMsg" class="muted" style="margin:0.5rem 0 0">{{ actionMsg }}</p>
    </header>

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
      <h2 style="margin-top:0;font-size:1.15rem">论断–证据地图</h2>
      <p class="muted" style="margin-top:0;font-size:0.88rem">
        claim → evidence → paper / experiment（在论文页选中文本可挂接）
      </p>
      <div v-if="evidences.length">
        <div v-for="e in evidences" :key="e.evidence_id" class="week-item">
          <div class="meta-line">
            <span class="badge">{{ e.evidence_id }}</span>
            <span>claim {{ e.claim_id }}</span>
            <span>{{ e.stance }}</span>
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
        尚无证据。打开关联论文，选中段落后点「挂到主线」。
      </p>
      <div v-if="mapEdges.length" style="margin-top:1rem">
        <p class="muted" style="font-size:0.85rem;margin:0 0 0.35rem">关系边（摘要）</p>
        <ul style="margin:0;padding-left:1.1rem;font-size:0.88rem">
          <li v-for="(ed, i) in mapEdges.slice(0, 24)" :key="i">
            {{ ed.source }} —{{ ed.kind }}→ {{ ed.target }}
          </li>
        </ul>
      </div>
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
        <RouterLink
          v-for="p in thread.paper_paths"
          :key="p"
          :to="`/page/${p}`"
          class="path-chip"
        >{{ p }}</RouterLink>
      </div>
      <p v-else class="muted" style="margin:0">暂无。sync-report --thread 或手动挂接。</p>
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
      <h2 style="margin-top:0;font-size:1.15rem">认知时间线</h2>
      <div v-if="events.length">
        <div v-for="(ev, i) in events.slice().reverse()" :key="i" class="week-item">
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
      <p v-else class="muted" style="margin:0">尚无事件。</p>
    </section>
  </div>
  <p v-else class="card muted">加载中…</p>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import {
  acceptThreadClaim,
  getThread,
  getThreadClaimSuggestions,
  runThreadDelta,
  setThreadEvidenceGate,
} from '../api'

const props = defineProps({ id: { type: String, required: true } })
const thread = ref(null)
const deltaResult = ref(null)
const suggestions = ref([])
const deltaBusy = ref(false)
const suggestBusy = ref(false)
const actionMsg = ref('')

const events = computed(() => thread.value?.events || [])
const evidences = computed(() => thread.value?.evidences || [])
const mapEdges = computed(() => thread.value?.evidence_map?.edges || [])

function summarize(ev) {
  try {
    return JSON.stringify(ev)
  } catch {
    return String(ev)
  }
}

async function load() {
  thread.value = await getThread(props.id)
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

onMounted(load)
watch(() => props.id, load)
</script>
