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
        </li>
      </ul>
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
            <template v-if="ev.path">{{ ev.path }}</template>
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
} from '../api'

const props = defineProps({ id: { type: String, required: true } })
const thread = ref(null)
const deltaResult = ref(null)
const suggestions = ref([])
const deltaBusy = ref(false)
const suggestBusy = ref(false)
const actionMsg = ref('')

const events = computed(() => thread.value?.events || [])

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
