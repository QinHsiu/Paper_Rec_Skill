# Examples · Paper_Rec `/wxmp` cases

选文与板块以 [`references/editorial.md`](references/editorial.md) 为准。

---

## Case A — 热点单篇 → 完整解读 → 草稿

```text
/wxmp note https://arxiv.org/abs/2106.09685
```

Agent 应：

1. **选文门**：热点/新颖/可借鉴；不过则说明原因并停。
2. 收集：题名、团队、来源、开源链接、关键词、框架图、主表指标。
3. 按模板写满：三句话看点 → 框架图 → 关键讲解 → 指标 → 借鉴 → 启发。  
   样例骨架：[`assets/cases/case_a_lora_note.md`](assets/cases/case_a_lora_note.md)
4. 落盘 `content/wxmp/notes/YYYY-MM-DD-<slug>.md`；框架图先上传再嵌入。
5. 用户确认后 `paper_note_publish.py create … --auto-cover`。
6. 回报 `media_id`；默认不 publish。

**验收**：八大板块齐全；开源与指标无臆造；有图或已声明无图。

---

## Case B — Wiki / `/ppt` 压缩成公众号体

```text
/wxmp note content/wiki/pages/llm/2021/lora
```

从 deep_read 抽取必含板块；删掉组会证明与公式墙；保留框架图引用与主指标；补全「开源」「关键词」「三句话看点」。

---

## Case C — `/wxmp daily`（检索归 paper-rec）

```text
/wxmp daily 多模态检索
```

1. paper-rec `/query_chinese` + Recent → Top 3。  
2. 按 editorial 门槛筛；展示「过/不过」理由。  
3. 用户选 1 篇 → Case A。  
4. 本 skill 不自建检索。

---

## Case D — 已有 MD，只推草稿

```text
/wxmp draft content/wxmp/notes/ready.md
```

校验模板板块是否齐全（缺则退回补写）；再上传草稿。

---

## Anti-patterns

| 不要 | 原因 |
|------|------|
| 水货凑日更 | 违反热点/新颖/可借鉴 |
| 超过三句的「看点」灌水 | 稀释贡献信号 |
| 用无关 AI 图冒充框架图 | 误导读者 |
| 编造开源链接或指标 | 违反写作闸门 |
| `/ppt` 全文粘贴 | 公众号不可读 |
| 默认自动 publish | 合规风险 |
