<template>
  <div>
    <header class="page-hero">
      <h1 class="page-title">Ask</h1>
      <p class="page-lead">基于本地 Wiki 内容检索作答。</p>
    </header>
    <div class="card">
      <div class="row">
        <input v-model="q" placeholder="基于本地 Wiki 提问…" style="flex:1" @keyup.enter="run" />
        <button class="primary" @click="run">提问</button>
      </div>
    </div>
    <div class="card" v-if="answer">
      <p style="margin-top:0;line-height:1.65">{{ answer }}</p>
      <ul style="margin:0;padding-left:1.1rem">
        <li v-for="h in hits" :key="h.path" style="margin:0.45rem 0">
          <RouterLink :to="`/page/${h.path}`">{{ h.title }}</RouterLink>
          <span class="muted"> — {{ h.snippet }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { askQuestion } from '../api'

const q = ref('')
const answer = ref('')
const hits = ref([])

async function run() {
  const data = await askQuestion(q.value)
  answer.value = data.answer
  hits.value = data.hits || []
}
</script>
