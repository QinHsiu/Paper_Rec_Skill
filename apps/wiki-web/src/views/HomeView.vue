<template>
  <div class="stack">
    <header class="page-hero">
      <h1 class="page-title">阅读实验室</h1>
      <p class="page-lead">
        论文笔记以 Markdown 存于 <code>content/wiki/pages</code>，支持互链、图片与图谱。
      </p>
    </header>

    <div class="home-grid">
      <section class="card">
        <h2 style="margin-top:0;font-size:1.25rem">从论文库开始</h2>
        <p class="muted" style="margin:0 0 1.1rem;line-height:1.6">
          浏览已同步的报告页，或打开入门笔记熟悉编辑与上传。
        </p>
        <div class="row">
          <RouterLink class="home-cta" to="/pages">进入论文库 →</RouterLink>
          <RouterLink class="home-link" to="/edit/llm/2025/getting-started">编辑入门页</RouterLink>
        </div>
      </section>

      <section class="card">
        <h2 style="margin-top:0;font-size:1.25rem">快捷入口</h2>
        <ul class="quick-list">
          <li>
            <RouterLink to="/pages">
              浏览 / 筛选论文
              <span>按关键词与阅读状态过滤</span>
            </RouterLink>
          </li>
          <li>
            <RouterLink to="/graph">
              知识图谱
              <span>标签与 [[wikilink]] 关系</span>
            </RouterLink>
          </li>
          <li>
            <RouterLink to="/weekly">
              一周推荐
              <span>content/weekly 周刊</span>
            </RouterLink>
          </li>
          <li>
            <RouterLink to="/skills">
              Skill 命令
              <span>/query_english · chinese · other</span>
            </RouterLink>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>
