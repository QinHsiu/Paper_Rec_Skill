<template>
  <div class="ask-workspace">
    <section class="ask-pane">
      <header class="page-hero">
        <h1 class="page-title">智能研读</h1>
        <p class="page-lead">基于本地 Wiki 提问；答案与来源并排，便于核对摘录。</p>
      </header>
      <div class="surface ask-composer">
        <div class="row">
          <input v-model="q" placeholder="基于本地 Wiki 提问…" style="flex:1" @keyup.enter="run" />
          <button class="primary" @click="run">提问</button>
        </div>
      </div>
      <div class="surface" v-if="answer">
        <p class="rail-kicker">回答</p>
        <p class="ask-answer">{{ answer }}</p>
      </div>
      <p v-else class="muted ask-empty">提出问题后，左侧显示回答，右侧列出可点击的来源页。</p>
    </section>
    <aside class="ask-sources surface">
      <p class="rail-kicker">来源</p>
      <h2 class="rail-title">证据页</h2>
      <ul v-if="hits.length" class="ask-hit-list">
        <li v-for="h in hits" :key="h.path">
          <RouterLink :to="`/page/${h.path}`">{{ h.title }}</RouterLink>
          <span class="muted">{{ h.snippet }}</span>
        </li>
      </ul>
      <p v-else class="muted">尚无命中。可先入库论文再提问。</p>
      <RouterLink class="rail-link" to="/pages">前往论文库</RouterLink>
    </aside>
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
