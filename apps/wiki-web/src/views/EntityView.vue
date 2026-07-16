<template>
  <div>
    <header class="page-hero article-head">
      <div>
        <p class="muted" style="margin:0 0 0.35rem;font-size:0.8rem;letter-spacing:0.06em;text-transform:uppercase">
          {{ typeLabel }}
        </p>
        <h1 class="page-title">{{ entity?.name || name }}</h1>
        <p class="page-lead" v-if="entity">关联 {{ entity.paper_count ?? papers.length }} 篇论文</p>
      </div>
      <RouterLink to="/graph"><button>返回图谱</button></RouterLink>
    </header>

    <div class="card" v-if="loading"><p class="muted">加载中…</p></div>

    <div class="card" v-else>
      <h2 style="margin-top:0;font-size:1.15rem;font-family:var(--font-display)">相关论文</h2>
      <div v-for="p in papers" :key="p.id || p.path" class="hit">
        <RouterLink :to="p.href_page || `/page/${p.path}`"><strong>{{ p.title || p.label }}</strong></RouterLink>
        <div class="meta-line">
          <span v-if="p.keyword" class="badge badge-reading">{{ p.keyword }}</span>
          <span v-if="p.added_at">入库 {{ p.added_at }}</span>
          <span v-if="p.score">分 {{ p.score }}</span>
        </div>
        <div class="row" style="margin-top:0.4rem">
          <RouterLink :to="p.href_page || `/page/${p.path}`">阅读</RouterLink>
          <RouterLink :to="p.href_edit || `/edit/${p.path}`">编辑</RouterLink>
        </div>
      </div>
      <p v-if="!papers.length" class="muted">暂无关联论文。</p>
    </div>

    <div class="card" v-if="related.length">
      <h2 style="margin-top:0;font-size:1.15rem;font-family:var(--font-display)">相关实体链接</h2>
      <div class="row" style="gap:0.5rem">
        <RouterLink
          v-for="r in related"
          :key="r.id"
          class="badge badge-reading"
          :to="r.href || `/entity/${r.type}/${r.label || r.name}`"
        >
          {{ typeCn(r.type) }} · {{ r.label || r.name }}
          <span v-if="r.paper_count"> ({{ r.paper_count }})</span>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { getEntity } from '../api'

const props = defineProps({
  kind: { type: String, required: true },
  name: { type: String, required: true },
})

const TYPE_CN = {
  keyword: '关键词',
  tag: '标签',
  team: '团队',
  company: '公司/机构',
  venue: '来源/会议',
  pack: 'Pack',
}

const loading = ref(true)
const entity = ref(null)
const papers = ref([])
const related = ref([])

const typeLabel = computed(() => TYPE_CN[props.kind] || props.kind)
function typeCn(t) {
  return TYPE_CN[t] || t
}

async function load() {
  loading.value = true
  try {
    const data = await getEntity(props.kind, props.name)
    entity.value = data.entity
    papers.value = data.papers || []
    related.value = data.related || []
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => [props.kind, props.name], load)
</script>

<style scoped>
.hit {
  padding: 0.85rem 0;
  border-bottom: 1px solid var(--border);
}
.hit:last-child {
  border-bottom: 0;
}
</style>
