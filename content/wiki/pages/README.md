# Wiki pages

每篇检索论文 = **独立目录 + README.md**（便于单独编辑）：

```
content/wiki/pages/<keyword>/<year>/<slug>/README.md
content/wiki/pages/<keyword>/README.md          ← 该关键词下 /query_* 日志（非论文）
content/wiki/deleted.json                       ← 删除黑名单
```

例：一次 `/query_*` 得到 10 篇 → 写入 10 个 `…/README.md`。

## 删除

- SPA / API 删除论文后写入 `deleted.json`
- 之后 `wiki_bridge sync-report` **跳过**黑名单中的论文，不再入库

## Slash 命令

| 命令 | 说明 |
|------|------|
| `/query_english` `/query_chinese` `/query_other` | 检索；sync 后每篇独立 README |
| `/wiki` | 查库 / 本周 / 启动 UI |
