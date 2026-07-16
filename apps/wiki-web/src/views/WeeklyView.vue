<template>
  <div>
    <header class="page-hero">
      <h1 class="page-title">一周推荐</h1>
      <p class="page-lead">
        本周通过 Skill 写入 Wiki 的论文（按 arXiv/标题去重）。
        <span v-if="week">{{ week }} · {{ from }} → {{ to }}</span>
      </p>
    </header>

    <div class="card" v-if="papers.length">
      <p class="muted" style="margin-top:0">共 {{ papers.length }} 篇</p>
      <div v-for="p in papers" :key="p.path" class="week-item">
        <div class="row" style="justify-content:space-between;align-items:flex-start">
          <div>
            <RouterLink :to="`/page/${p.path}`"><strong>{{ p.title }}</strong></RouterLink>
            <div class="meta-line">
              <span class="badge badge-reading">{{ p.keyword }}</span>
              <span>检索分 {{ p.score || '—' }}</span>
              <span>入库 {{ p.added_at }}</span>
            </div>
            <p class="muted" style="margin:0.5rem 0 0;font-size:0.9rem;line-height:1.5">
              {{ p.summary || '暂无摘要' }}
            </p>
          </div>
          <RouterLink :to="`/edit/${p.path}`"><button>编辑</button></RouterLink>
        </div>
      </div>
    </div>
    <p v-else class="card muted">本周尚无新入库论文。用 `/query_*` 检索后 `sync-report` 或 `/wiki` 写入即可。</p>

    <div v-if="digests.length">
      <h2 class="page-title" style="font-size:1.25rem;margin-top:1.5rem">手写周刊</h2>
      <div class="card" v-for="item in digests" :key="item.path">
        <h3 style="margin-top:0">{{ item.title }}</h3>
        <p class="muted">{{ item.week }} · {{ item.type }}</p>
        <pre style="white-space:pre-wrap;font-family:var(--font-prose)">{{ item.preview }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { listWeekly } from '../api'

const papers = ref([])
const digests = ref([])
const week = ref('')
const from = ref('')
const to = ref('')

onMounted(async () => {
  const data = await listWeekly()
  papers.value = data.papers || []
  digests.value = data.digests || []
  week.value = data.week || ''
  from.value = data.from || ''
  to.value = data.to || ''
})
</script>

<style scoped>
.week-item {
  padding: 1rem 0;
  border-bottom: 1px solid var(--border);
}
.week-item:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}
.week-item:first-of-type {
  padding-top: 0;
}
</style>
