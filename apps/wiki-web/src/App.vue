<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">
        <p class="brand-mark">Paper_Rec</p>
        <p class="brand-sub">Research Lab</p>
      </div>
      <nav>
        <p class="nav-group">研读</p>
        <button
          type="button"
          class="nav-item"
          :class="{ active: isActive('/pages', { prefix: true }) || route.name === 'page' || route.name === 'edit' }"
          @click="go('/pages')"
        >
          论文库
        </button>
        <button type="button" class="nav-item" :class="{ active: isActive('/weekly') }" @click="go('/weekly')">
          一周推荐
        </button>
        <button type="button" class="nav-item" :class="{ active: isActive('/ask') }" @click="go('/ask')">
          智能研读
        </button>

        <p class="nav-group">研究</p>
        <button
          type="button"
          class="nav-item"
          :class="{ active: isActive('/threads', { prefix: true }) }"
          @click="go('/threads')"
        >
          研究主线
        </button>
        <button
          type="button"
          class="nav-item"
          :class="{ active: isActive('/experiments', { prefix: true }) }"
          @click="go('/experiments')"
        >
          实验
        </button>
        <button
          type="button"
          class="nav-item"
          :class="{ active: isActive('/graph', { prefix: true }) || route.name === 'entity' }"
          @click="go('/graph')"
        >
          知识图谱
        </button>

        <p class="nav-group">工作台</p>
        <button type="button" class="nav-item" :class="{ active: isActive('/search') }" @click="go('/search')">
          库内搜索
        </button>
        <button type="button" class="nav-item" :class="{ active: isActive('/skills') }" @click="go('/skills')">
          Skills
        </button>
        <button type="button" class="nav-item" :class="{ active: isActive('/') }" @click="go('/')">
          总览
        </button>
      </nav>
    </aside>
    <main class="main">
      <div class="main-inner" :class="{ wide: isWide, 'full-bleed': isReading }">
        <RouterView />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const isWide = computed(() =>
  ['pages', 'edit', 'graph', 'entity', 'experiments', 'exp-detail', 'threads', 'thread-detail', 'page', 'ask'].includes(
    String(route.name || ''),
  ),
)
const isReading = computed(() => ['page', 'ask', 'edit'].includes(String(route.name || '')))

function isActive(path, { prefix = false } = {}) {
  const current = route.path || '/'
  if (path === '/') return current === '/'
  if (prefix) return current === path || current.startsWith(`${path}/`)
  return current === path
}

function go(path) {
  if (route.path !== path) router.push(path)
}
</script>
