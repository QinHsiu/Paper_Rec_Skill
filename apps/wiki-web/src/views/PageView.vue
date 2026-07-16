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
        </div>
      </div>
      <div class="row">
        <RouterLink :to="`/edit/${path}`"><button class="primary">编辑笔记</button></RouterLink>
        <RouterLink to="/pages"><button>返回列表</button></RouterLink>
      </div>
    </header>
    <article class="card prose" v-html="html"></article>
  </div>
  <p v-else class="muted">加载中…</p>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { getPage } from '../api'

const props = defineProps({ path: { type: String, required: true } })
const page = ref(null)

const html = computed(() => {
  if (!page.value) return ''
  const raw = marked.parse(page.value.body || '')
  return DOMPurify.sanitize(raw)
})

async function load() {
  page.value = await getPage(props.path)
}

onMounted(load)
watch(() => props.path, load)
</script>
