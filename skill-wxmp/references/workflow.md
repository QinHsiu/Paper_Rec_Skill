# Workflow · `/wxmp`

Paper_Rec 公众号推荐流水线（人审草稿）。原则见 [`editorial.md`](editorial.md)；案例见 [`../examples.md`](../examples.md)。

## Persist layout

```text
content/wxmp/
  notes/YYYY-MM-DD-<slug>.md
  figures/<slug>/              # 可选：框架图原图（上传前）
  manifests/<media_id>.json    # 可选
```

## Selection gate（写之前）

确认：**热点 · 新颖 · 可借鉴** 三项都过；否则换文或停。`/wxmp daily` 必须先过此门再 note。

## Note rules（写什么）

固定板块（缺一不可）：

1. 基本信息（名 / 团队 / 来源 / **开源**）+ **关键词**
2. **三句话看点**（贡献 + 优点，≤3 句）
3. **框架图**（有则上传素材；无则声明）
4. **关键讲解**（只讲核心）
5. **指标讲解**（可追溯）
6. **值得借鉴** + **思考与启发**

模板：[`../assets/paper_note_template.md`](../assets/paper_note_template.md)

- 标题 ≤32 字；digest ≤120 字
- `content_source_url` = arXiv 或 DOI

## Draft rules

```powershell
python skill-wxmp/scripts/paper_note_publish.py create `
  --account main --md <path> --title "…" --source-url "…" --auto-cover
```

正文内框架图：先 `upload_material` / 图文内图片接口拿到微信 URL，再写入 HTML。  
封面：`--thumb-media-id` → ModelScope → `assets/default_cover.jpg`（见 [`covers.md`](covers.md)）。

## Publish rules

仅当用户明确要求发布时调用 `publish`；默认停在草稿箱。
