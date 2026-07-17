<template>
  <div>
    <header class="page-hero">
      <h1 class="page-title">实验</h1>
      <p class="page-lead">
        沙箱产物与 Wiki 镜像：指标、训练曲线、关联论文，一处可追溯。
      </p>
    </header>

    <div class="card" v-if="items.length">
      <p class="muted" style="margin-top:0">共 {{ items.length }} 个实验</p>
      <div v-for="e in items" :key="e.id" class="week-item">
        <div class="row" style="justify-content:space-between;align-items:flex-start">
          <div>
            <RouterLink :to="`/experiments/${e.id}`"><strong>{{ e.title || e.id }}</strong></RouterLink>
            <div class="meta-line">
              <span class="badge" :class="e.target_met ? 'badge-done' : 'badge-reading'">
                {{ e.target_met ? '达标' : '进行中' }}
              </span>
              <span v-if="e.metrics_summary && e.metrics_summary.F1">F1 {{ e.metrics_summary.F1 }}</span>
              <span>{{ e.updated_at }}</span>
            </div>
            <p class="muted" style="margin:0.55rem 0 0;font-size:0.9rem;line-height:1.55">
              {{ e.preview || '暂无摘要' }}
            </p>
            <div class="meta-line" v-if="e.paper_refs && e.paper_refs.length">
              <RouterLink
                v-for="p in e.paper_refs"
                :key="p"
                :to="`/page/${p}`"
                class="path-chip"
              >{{ p }}</RouterLink>
            </div>
          </div>
          <RouterLink :to="`/experiments/${e.id}`"><button class="primary">详情</button></RouterLink>
        </div>
      </div>
    </div>
    <p v-else class="card muted">
      尚无实验。完成 <code>/exp_loop</code> 后执行
      <code>wiki_bridge sync-exp</code> 即可同步到此。
    </p>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { listExperiments } from '../api'

const items = ref([])
onMounted(async () => {
  items.value = await listExperiments()
})
</script>
