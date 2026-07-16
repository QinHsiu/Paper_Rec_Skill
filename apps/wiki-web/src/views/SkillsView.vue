<template>
  <div>
    <header class="page-hero">
      <h1 class="page-title">Skills</h1>
      <p class="page-lead">Paper_Rec Cursor Skill 命令与文档。</p>
    </header>
    <div class="card" v-for="s in skills" :key="s.id">
      <h2 style="margin-top:0;font-size:1.2rem">{{ s.name }}</h2>
      <p class="muted" style="margin-bottom:0.4rem">命令</p>
      <div class="row" style="margin-bottom:1rem">
        <code v-for="c in s.commands" :key="c" class="path-chip">{{ c }}</code>
      </div>
      <p class="muted" style="margin-bottom:0.4rem">文档</p>
      <ul style="margin:0;padding-left:1.1rem">
        <li v-for="d in s.docs" :key="d.path" style="margin:0.3rem 0">
          <code>{{ d.path }}</code>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { listSkills } from '../api'

const skills = ref([])
onMounted(async () => {
  skills.value = await listSkills()
  // ensure /wiki is visible even if API docs lag
  if (skills.value[0] && !skills.value[0].commands.includes('/wiki')) {
    skills.value[0].commands = [...skills.value[0].commands, '/wiki']
  }
})
</script>
