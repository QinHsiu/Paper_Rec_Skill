<template>
  <div>
    <header class="page-hero">
      <h1 class="page-title">搜索</h1>
      <p class="page-lead">在标题、正文与标签中查找笔记。</p>
    </header>
    <div class="card">
      <div class="row">
        <input v-model="q" placeholder="搜索标题 / 正文 / 标签" style="flex:1" @keyup.enter="run" />
        <button class="primary" @click="run">搜索</button>
      </div>
    </div>
    <div class="card">
      <div v-for="r in results" :key="r.path" class="search-hit">
        <RouterLink :to="`/page/${r.path}`"><strong>{{ r.title }}</strong></RouterLink>
        <div class="path-chip" style="display:inline-block;margin:0.35rem 0">{{ r.path }}</div>
        <div class="muted" style="font-size:0.92rem;line-height:1.5">{{ r.snippet }}</div>
      </div>
      <p v-if="searched && !results.length" class="muted">无结果</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { searchWiki } from '../api'

const q = ref('')
const results = ref([])
const searched = ref(false)

async function run() {
  searched.value = true
  results.value = await searchWiki(q.value)
}
</script>
