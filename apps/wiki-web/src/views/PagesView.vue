<template>
  <div>
    <header class="page-hero">
      <h1 class="page-title">论文库</h1>
      <p class="page-lead">
        每篇论文独立目录 <code>…/slug/README.md</code>；删除后写入黑名单，同步时不再入库。
      </p>
    </header>

    <div class="toolbar">
      <div class="toolbar-left">
        <input v-model="keyword" placeholder="关键词筛选" style="min-width:12rem" @keyup.enter="load" />
        <select v-model="status" @change="load">
          <option value="">全部状态</option>
          <option value="todo">todo</option>
          <option value="reading">reading</option>
          <option value="done">done</option>
          <option value="abandoned">abandoned</option>
        </select>
        <button @click="load">刷新</button>
      </div>
      <div class="toolbar-right">
        <button class="primary" @click="create">新建笔记</button>
      </div>
    </div>

    <div class="card card-flush">
      <table class="papers-table">
        <thead>
          <tr>
            <th style="width:20%">标题</th>
            <th style="width:24%">摘要</th>
            <th>关键词</th>
            <th>检索分</th>
            <th>入库</th>
            <th>个人分</th>
            <th>状态</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in pages" :key="p.path">
            <td>
              <RouterLink :to="`/page/${p.path}`">{{ p.title }}</RouterLink>
            </td>
            <td class="summary-cell muted">{{ p.summary || '—' }}</td>
            <td class="muted">{{ p.keyword }}</td>
            <td><strong>{{ p.score || '—' }}</strong></td>
            <td class="muted mono-sm">{{ p.added_at || '—' }}</td>
            <td>
              <input
                class="rating-input"
                :value="p.rating"
                placeholder="1–10"
                @change="(e) => saveRating(p, e.target.value)"
              />
            </td>
            <td>
              <span class="badge" :class="`badge-${p.status || 'todo'}`">{{ p.status || 'todo' }}</span>
            </td>
            <td class="row" style="gap:0.45rem;white-space:nowrap">
              <RouterLink :to="`/edit/${p.path}`">编辑</RouterLink>
              <button type="button" class="danger-btn" @click="remove(p)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!pages.length" class="muted" style="padding:1.25rem">
        暂无页面。可用 Skill 检索后 sync，或点「新建笔记」。
      </p>
    </div>

    <div class="card" v-if="deleted.length">
      <h3 style="margin-top:0;font-family:var(--font-display)">删除表（黑名单）</h3>
      <p class="muted" style="margin-top:0">以下论文不会再次被 sync 写入论文库。</p>
      <ul style="margin:0;padding-left:1.1rem">
        <li v-for="d in deleted" :key="d.key" class="muted" style="margin:0.35rem 0">
          {{ d.title || d.path || d.key }}
          <span class="mono-sm"> · {{ d.deleted_at }} · {{ d.key }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { deletePage, listDeleted, listPages, patchPageMeta, savePage } from '../api'

const pages = ref([])
const deleted = ref([])
const keyword = ref('')
const status = ref('')
const router = useRouter()

async function load() {
  pages.value = await listPages({
    keyword: keyword.value || undefined,
    status: status.value || undefined,
  })
  try {
    deleted.value = await listDeleted()
  } catch {
    deleted.value = []
  }
}

async function saveRating(p, value) {
  const rating = String(value || '').trim()
  p.rating = rating
  await patchPageMeta(p.path, { rating })
}

async function remove(p) {
  if (!confirm(`删除「${p.title}」？将移入删除表，之后 sync 不会再入库。`)) return
  await deletePage(p.path)
  await load()
}

async function create() {
  const title = prompt('论文标题')
  if (!title) return
  const keywordName = prompt('关键词目录（如 llm / cv）', 'llm') || 'llm'
  const year = prompt('年份', String(new Date().getFullYear())) || 'unknown'
  const path = `${keywordName}/${year}/${title.toLowerCase().replace(/[^\w\u4e00-\u9fff]+/g, '-').replace(/^-|-$/g, '')}`
  await savePage(path, {
    meta: {
      title,
      keyword: keywordName,
      year,
      status: 'todo',
      tags: [keywordName],
      summary: '',
      score: '',
      rating: '',
      added_at: new Date().toISOString().slice(0, 10),
    },
    body: `## Core Idea / 核心观点\n\n…\n\n## Personal notes / 个人笔记\n\n### Takeaways\n\n- \n\n### Figures / 插图\n\n`,
  })
  router.push(`/edit/${path}`)
}

onMounted(load)
</script>

<style scoped>
.summary-cell {
  font-size: 0.84rem;
  line-height: 1.45;
  max-width: 22rem;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.rating-input {
  width: 3.6rem;
  padding: 0.35rem 0.4rem;
  text-align: center;
}
.mono-sm {
  font-family: var(--font-mono);
  font-size: 0.78rem;
}
.papers-table td {
  vertical-align: top;
}
.danger-btn {
  color: var(--danger);
  border-color: #e8cccc;
  background: #fdf6f6;
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}
</style>
