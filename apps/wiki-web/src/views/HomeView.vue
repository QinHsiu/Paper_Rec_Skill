<template>
  <div class="stack">
    <header class="home-hero">
      <p class="home-kicker">Literature · Wiki · Experiment</p>
      <h1 class="home-brand">Paper_Rec</h1>
      <p class="home-tagline">
        检索文献、沉淀阅读、验证实验——把研究闭环留在本地 Markdown 里。
      </p>
      <div class="home-actions">
        <RouterLink class="home-cta" to="/pages">进入论文库</RouterLink>
        <RouterLink class="home-cta-ghost" to="/experiments">查看实验</RouterLink>
      </div>
    </header>

    <div class="flow-strip">
      <div class="flow-step">
        <div class="flow-num">01</div>
        <strong>Retrieve</strong>
        <span>/query_* 多源检索与结构化报告</span>
      </div>
      <div class="flow-step">
        <div class="flow-num">02</div>
        <strong>Annotate</strong>
        <span>Wiki 阅读、评分与笔记标记</span>
      </div>
      <div class="flow-step">
        <div class="flow-num">03</div>
        <strong>Experiment</strong>
        <span>/exp_* 方案验证与训练闭环</span>
      </div>
      <div class="flow-step">
        <div class="flow-num">04</div>
        <strong>Remember</strong>
        <span>指标与曲线回写实验模块</span>
      </div>
    </div>

    <div class="home-grid">
      <section class="card">
        <h2 class="panel-title">继续阅读</h2>
        <p class="panel-copy">
          论文以独立 README 存于本地 Git 内容库，支持互链、图片上传与知识图谱。
        </p>
        <div class="row">
          <RouterLink class="home-link" to="/edit/llm/2025/getting-started">编辑入门页 →</RouterLink>
          <RouterLink class="home-link" to="/weekly">本周入库 →</RouterLink>
        </div>
      </section>

      <section class="card">
        <h2 class="panel-title">快捷入口</h2>
        <ul class="quick-list">
          <li>
            <RouterLink to="/pages">
              论文库
              <span>按关键词与阅读状态筛选</span>
            </RouterLink>
          </li>
          <li>
            <RouterLink to="/experiments">
              实验
              <span>loss 曲线 · 指标 · 关联论文</span>
            </RouterLink>
          </li>
          <li>
            <RouterLink to="/graph">
              知识图谱
              <span>关键词 / 团队 / 实体关系</span>
            </RouterLink>
          </li>
          <li>
            <RouterLink to="/skills">
              Skills
              <span>/query_* · /exp_*</span>
            </RouterLink>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>
