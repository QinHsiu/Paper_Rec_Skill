<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">
        <p class="brand-mark">Paper_Rec</p>
        <p class="brand-sub">Research Lab</p>
      </div>
      <nav>
        <RouterLink to="/"><span class="nav-ico">01</span>首页</RouterLink>
        <RouterLink to="/pages"><span class="nav-ico">02</span>论文库</RouterLink>
        <RouterLink to="/experiments"><span class="nav-ico">03</span>实验</RouterLink>
        <RouterLink to="/search"><span class="nav-ico">04</span>搜索</RouterLink>
        <RouterLink to="/graph"><span class="nav-ico">05</span>知识图谱</RouterLink>
        <RouterLink to="/weekly"><span class="nav-ico">06</span>一周推荐</RouterLink>
        <RouterLink to="/ask"><span class="nav-ico">07</span>Ask</RouterLink>
        <RouterLink to="/skills"><span class="nav-ico">08</span>Skills</RouterLink>
      </nav>
      <p class="sidebar-foot">Markdown · Git · Local truth</p>
    </aside>
    <main class="main">
      <div class="main-inner" :class="{ wide: isWide }">
        <RouterView />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const isWide = computed(() =>
  ['pages', 'edit', 'graph', 'entity', 'experiments', 'exp-detail'].includes(String(route.name || '')),
)
</script>
