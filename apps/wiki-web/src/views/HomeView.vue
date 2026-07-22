<template>
  <div class="stack">
    <header class="home-hero">
      <p class="home-kicker">一站式本地学术工作台</p>
      <h1 class="home-brand">Paper_Rec</h1>
      <p class="home-tagline">
        文献研读、研究主线与实验验收同一处沉淀——参考一站式学术助手的工作流，数据仍留在本地 Git。
      </p>
      <div class="home-actions">
        <RouterLink class="home-cta" to="/pages">打开论文库</RouterLink>
        <RouterLink class="home-cta-ghost" to="/ask">智能研读</RouterLink>
        <RouterLink class="home-cta-ghost" to="/threads">进入主线</RouterLink>
      </div>
    </header>

    <section class="module-row" aria-label="核心工作区">
      <RouterLink class="module-tile" to="/pages">
        <span class="module-label">文献研读</span>
        <strong>论文库 · 双栏阅读</strong>
        <span>入库、标注、挂证据到主线；对照笔记与 AI 提问。</span>
      </RouterLink>
      <RouterLink class="module-tile" to="/threads">
        <span class="module-label">研究推进</span>
        <strong>主线 · 实验 · 图谱</strong>
        <span>假设、缺口、实验指标与关系网同屏追踪。</span>
      </RouterLink>
      <RouterLink class="module-tile" to="/ask">
        <span class="module-label">辅助问答</span>
        <strong>基于本地 Wiki 作答</strong>
        <span>问句与来源并排，减少幻觉、可追溯引用。</span>
      </RouterLink>
    </section>

    <div class="flow-strip">
      <div class="flow-step">
        <div class="flow-num">01</div>
        <strong>Retrieve</strong>
        <span>/query_* 多源检索入库</span>
      </div>
      <div class="flow-step">
        <div class="flow-num">02</div>
        <strong>Read</strong>
        <span>双栏研读 · 摘录挂主线</span>
      </div>
      <div class="flow-step">
        <div class="flow-num">03</div>
        <strong>Experiment</strong>
        <span>/exp_* · lab 验收硬闸</span>
      </div>
      <div class="flow-step">
        <div class="flow-num">04</div>
        <strong>Write</strong>
        <span>草稿 · 诚信闸门再导出</span>
      </div>
    </div>

    <div class="home-grid">
      <section class="surface">
        <h2 class="panel-title">继续阅读</h2>
        <p class="panel-copy">
          论文以独立 README 存于本地内容库；选中正文可挂 claim 证据，并可拉取全文 / 1-hop 引用。
        </p>
        <div class="row">
          <RouterLink class="home-link" to="/weekly">本周入库 →</RouterLink>
          <RouterLink class="home-link" to="/experiments">实验看板 →</RouterLink>
        </div>
      </section>

      <section class="surface">
        <h2 class="panel-title">快捷入口</h2>
        <ul class="quick-list">
          <li>
            <RouterLink to="/pages">
              论文库
              <span>按关键词与阅读状态筛选</span>
            </RouterLink>
          </li>
          <li>
            <RouterLink to="/threads">
              研究主线
              <span>假设 · claims · Watch/Delta</span>
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
              <span>/query_* · /exp_* · /lab</span>
            </RouterLink>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>
