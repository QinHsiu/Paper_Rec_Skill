<template>
  <div v-if="page">
    <header class="card article-head">
      <div>
        <h1 class="page-title">{{ page.meta.title || path }}</h1>
        <div class="meta-line">
          <span class="badge" :class="`badge-${page.meta.status || 'todo'}`">
            {{ page.meta.status || 'todo' }}
          </span>
          <span>{{ page.meta.year || '—' }}</span>
          <span class="path-chip">{{ path }}</span>
          <RouterLink
            v-for="tid in threadIds"
            :key="tid"
            :to="`/threads/${tid}`"
            class="path-chip"
          >主线 · {{ tid }}</RouterLink>
        </div>
      </div>
      <div class="row" style="flex-wrap:wrap;gap:0.4rem">
        <button class="primary" @click="openAttach" :disabled="!selection.trim()">
          挂到主线
        </button>
        <button @click="openRecommend" :disabled="!selection.trim() || !threadIds.length">
          推荐证据
        </button>
        <button @click="copyBibtex">导出 BibTeX</button>
        <label class="file-btn">
          上传 PDF/TXT
          <input type="file" accept=".pdf,.txt,.md" hidden @change="onIngestFile" />
        </label>
        <RouterLink :to="`/edit/${path}`"><button>编辑笔记</button></RouterLink>
        <RouterLink to="/pages"><button>返回列表</button></RouterLink>
      </div>
    </header>

    <p class="muted" style="margin:0 0 0.75rem;font-size:0.88rem">
      选中正文 →「挂到主线」或「推荐证据」。上传 PDF 会写入 fulltext.md 并可选生成 suggested claims。
      <span v-if="selection">已选 {{ selection.length }} 字</span>
      <span v-if="ingestMsg"> · {{ ingestMsg }}</span>
    </p>

    <article ref="articleEl" class="card prose" v-html="html" @mouseup="captureSelection"></article>

    <div v-if="showAttach" class="card attach-panel">
      <h2 style="margin-top:0;font-size:1.1rem">挂到研究主线</h2>
      <p class="muted" style="font-size:0.9rem;white-space:pre-wrap">「{{ selection.slice(0, 280) }}{{ selection.length > 280 ? '…' : '' }}」</p>
      <div class="row" style="flex-wrap:wrap;gap:0.5rem;align-items:flex-end">
        <label>
          <span class="muted" style="font-size:0.8rem">主线</span>
          <select v-model="form.threadId" @change="onThreadChange">
            <option value="">选择…</option>
            <option v-for="t in threads" :key="t.thread_id" :value="t.thread_id">
              {{ t.title || t.thread_id }}
            </option>
          </select>
        </label>
        <label>
          <span class="muted" style="font-size:0.8rem">Claim</span>
          <select v-model="form.claimId">
            <option value="">选择…</option>
            <option v-for="c in claims" :key="c.id" :value="c.id">
              {{ c.id }} — {{ (c.text || '').slice(0, 48) }}
            </option>
          </select>
        </label>
        <label>
          <span class="muted" style="font-size:0.8rem">support_status</span>
          <select v-model="form.supportStatus">
            <option value="supports">supports</option>
            <option value="refutes">refutes</option>
            <option value="related">related</option>
            <option value="insufficient">insufficient</option>
          </select>
        </label>
        <label>
          <span class="muted" style="font-size:0.8rem">confidence</span>
          <input type="number" min="0" max="1" step="0.1" v-model.number="form.confidence" style="width:4rem" />
        </label>
        <button class="primary" :disabled="!canSubmit || busy" @click="submitEvidence">
          {{ busy ? '提交中…' : '创建证据' }}
        </button>
        <button @click="showAttach = false">取消</button>
      </div>
      <p v-if="attachMsg" class="muted" style="margin:0.5rem 0 0">{{ attachMsg }}</p>
    </div>

    <div v-if="showRecommend" class="card attach-panel">
      <h2 style="margin-top:0;font-size:1.1rem">证据反哺推荐</h2>
      <p class="muted" style="font-size:0.88rem">基于选中段落与关联主线（只读推荐，不自动写入）。</p>
      <div v-if="recClaims.length">
        <p style="margin:0.5rem 0 0.25rem;font-weight:600">Claims</p>
        <ul style="margin:0;padding-left:1.1rem;font-size:0.9rem">
          <li v-for="c in recClaims" :key="c.id">
            <code>{{ c.id }}</code> ({{ c.recommend_score }}) {{ c.text }}
          </li>
        </ul>
      </div>
      <div v-if="recEvs.length">
        <p style="margin:0.75rem 0 0.25rem;font-weight:600">Evidences</p>
        <ul style="margin:0;padding-left:1.1rem;font-size:0.9rem">
          <li v-for="e in recEvs" :key="e.evidence_id">
            <code>{{ e.evidence_id }}</code>
            · {{ e.support_status || e.stance }}
            · conf {{ e.confidence ?? '—' }}
            · score {{ e.recommend_score }}
            — {{ (e.quote || '').slice(0, 120) }}
          </li>
        </ul>
      </div>
      <button style="margin-top:0.75rem" @click="showRecommend = false">关闭</button>
    </div>
  </div>
  <p v-else class="muted">加载中…</p>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import {
  createThreadEvidence,
  exportBibtex,
  getPage,
  getThread,
  ingestPaperFile,
  listThreads,
  recommendForThread,
  threadsForPaper,
} from '../api'

const props = defineProps({ path: { type: String, required: true } })
const page = ref(null)
const threadIds = ref([])
const threads = ref([])
const claims = ref([])
const selection = ref('')
const showAttach = ref(false)
const showRecommend = ref(false)
const busy = ref(false)
const attachMsg = ref('')
const ingestMsg = ref('')
const recClaims = ref([])
const recEvs = ref([])
const articleEl = ref(null)
const form = reactive({
  threadId: '',
  claimId: '',
  supportStatus: 'supports',
  confidence: 0.7,
})

const html = computed(() => {
  if (!page.value) return ''
  const raw = marked.parse(page.value.body || '')
  return DOMPurify.sanitize(raw)
})

const canSubmit = computed(() => form.threadId && form.claimId && selection.value.trim())

function captureSelection() {
  const sel = window.getSelection?.()
  const text = (sel?.toString() || '').trim()
  if (text) selection.value = text
}

async function load() {
  page.value = await getPage(props.path)
  try {
    threadIds.value = await threadsForPaper(props.path)
  } catch {
    threadIds.value = []
  }
}

async function openAttach() {
  captureSelection()
  if (!selection.value.trim()) {
    attachMsg.value = '请先选中一段正文'
    showAttach.value = true
    return
  }
  attachMsg.value = ''
  showAttach.value = true
  threads.value = await listThreads()
  if (!form.threadId && threadIds.value.length === 1) {
    form.threadId = threadIds.value[0]
  }
  if (!form.threadId && threads.value.length === 1) {
    form.threadId = threads.value[0].thread_id
  }
  await onThreadChange()
}

async function openRecommend() {
  captureSelection()
  if (!selection.value.trim()) return
  const tid = threadIds.value[0]
  if (!tid) {
    attachMsg.value = '请先关联研究主线'
    return
  }
  try {
    const data = await recommendForThread(tid, selection.value)
    recClaims.value = data.claims || []
    recEvs.value = data.evidences || []
    showRecommend.value = true
  } catch (e) {
    attachMsg.value = e?.response?.data?.detail || e.message || String(e)
  }
}

async function onThreadChange() {
  claims.value = []
  form.claimId = ''
  if (!form.threadId) return
  const t = await getThread(form.threadId)
  claims.value = t.claims || []
  if (claims.value.length === 1) form.claimId = claims.value[0].id
}

async function submitEvidence() {
  busy.value = true
  attachMsg.value = ''
  try {
    const rec = await createThreadEvidence(form.threadId, {
      claim_id: form.claimId,
      kind: 'quote',
      paper_path: props.path,
      quote: selection.value.trim(),
      stance: form.supportStatus === 'insufficient' ? 'related' : form.supportStatus,
      support_status: form.supportStatus,
      confidence: form.confidence,
      gate: 'accepted',
    })
    attachMsg.value = `已创建 ${rec.evidence_id} (conf=${rec.confidence}) → ${form.threadId}/${form.claimId}`
    if (!threadIds.value.includes(form.threadId)) {
      threadIds.value = [...threadIds.value, form.threadId]
    }
  } catch (e) {
    attachMsg.value = e?.response?.data?.detail || e.message || String(e)
  } finally {
    busy.value = false
  }
}

async function copyBibtex() {
  try {
    const data = await exportBibtex([props.path])
    const text = data.bibtex || ''
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
      attachMsg.value = `BibTeX 已复制` + (data.warnings?.length ? `（警告 ${data.warnings.length}）` : '')
    } else {
      attachMsg.value = text.slice(0, 200)
    }
  } catch (e) {
    attachMsg.value = e?.response?.data?.detail || e.message || String(e)
  }
}

async function onIngestFile(ev) {
  const file = ev.target.files?.[0]
  ev.target.value = ''
  if (!file) return
  ingestMsg.value = '解析中…'
  try {
    const tid = threadIds.value[0] || ''
    const out = await ingestPaperFile(props.path, file, { threadId: tid, applySuggest: Boolean(tid) })
    const n = out.suggest?.claims?.length || out.suggest?.candidates?.length || 0
    ingestMsg.value = `已写入 fulltext · 候选 ${n}（suggested）`
  } catch (e) {
    ingestMsg.value = e?.response?.data?.detail || e.message || String(e)
  }
}

onMounted(load)
watch(() => props.path, load)
</script>

<style scoped>
.attach-panel {
  margin-top: 1rem;
}
.attach-panel select {
  display: block;
  min-width: 12rem;
  margin-top: 0.25rem;
}
.file-btn {
  display: inline-flex;
  align-items: center;
  padding: 0.35rem 0.75rem;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}
</style>
