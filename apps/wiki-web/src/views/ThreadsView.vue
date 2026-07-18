<template>
  <div>
    <header class="page-hero">
      <h1 class="page-title">研究主线</h1>
      <p class="page-lead">
        假设、主张与证据缺口 — 把文献检索和实验挂到同一条认知叙事上。
      </p>
    </header>

    <div class="card" style="margin-bottom:1rem">
      <h2 style="margin-top:0;font-size:1.05rem">新建主线</h2>
      <div class="row" style="flex-wrap:wrap;gap:0.5rem;align-items:flex-end">
        <label style="flex:1;min-width:12rem">
          <span class="muted" style="font-size:0.8rem">标题</span>
          <input v-model="form.title" placeholder="例如：多模态大模型对齐" style="width:100%" />
        </label>
        <label style="flex:1;min-width:10rem">
          <span class="muted" style="font-size:0.8rem">假设（可选）</span>
          <input v-model="form.hypothesis" placeholder="一句话假设" style="width:100%" />
        </label>
        <label style="min-width:8rem">
          <span class="muted" style="font-size:0.8rem">keywords</span>
          <input v-model="form.keywords" placeholder="a, b" style="width:100%" />
        </label>
        <button class="primary" :disabled="!form.title.trim() || creating" @click="create">
          {{ creating ? '创建中…' : '创建' }}
        </button>
      </div>
      <p v-if="createErr" class="muted" style="color:#b45309;margin:0.5rem 0 0">{{ createErr }}</p>
    </div>

    <div class="card" v-if="items.length">
      <p class="muted" style="margin-top:0">共 {{ items.length }} 条主线</p>
      <div v-for="t in items" :key="t.thread_id" class="week-item">
        <div class="row" style="justify-content:space-between;align-items:flex-start">
          <div>
            <RouterLink :to="`/threads/${t.thread_id}`">
              <strong>{{ t.title || t.thread_id }}</strong>
            </RouterLink>
            <div class="meta-line">
              <span class="badge" :class="statusBadge(t.status)">{{ t.status }}</span>
              <span>论文 {{ t.paper_count }}</span>
              <span>实验 {{ t.exp_count }}</span>
              <span>缺口 {{ t.gap_count }}</span>
              <span>{{ t.updated_at }}</span>
            </div>
            <p class="muted" style="margin:0.55rem 0 0;font-size:0.9rem;line-height:1.55">
              {{ t.hypothesis || '暂无假设' }}
            </p>
          </div>
          <RouterLink :to="`/threads/${t.thread_id}`"><button class="primary">详情</button></RouterLink>
        </div>
      </div>
    </div>
    <p v-else class="card muted">
      尚无研究主线。创建一条后，在 <code>/query_*</code> 中用
      <code>thread:&lt;id&gt;</code> 注入主线上下文。
    </p>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createThread, listThreads } from '../api'

const router = useRouter()
const items = ref([])
const creating = ref(false)
const createErr = ref('')
const form = reactive({ title: '', hypothesis: '', keywords: '' })

function statusBadge(s) {
  if (s === 'active') return 'badge-reading'
  if (s === 'archived') return 'badge-done'
  return 'badge-todo'
}

async function refresh() {
  items.value = await listThreads()
}

async function create() {
  createErr.value = ''
  creating.value = true
  try {
    const keywords = form.keywords
      .split(',')
      .map((x) => x.trim())
      .filter(Boolean)
    const data = await createThread({
      title: form.title.trim(),
      hypothesis: form.hypothesis.trim(),
      keywords,
    })
    form.title = ''
    form.hypothesis = ''
    form.keywords = ''
    await refresh()
    router.push(`/threads/${data.thread_id}`)
  } catch (e) {
    createErr.value = e?.response?.data?.detail || e.message || String(e)
  } finally {
    creating.value = false
  }
}

onMounted(refresh)
</script>
