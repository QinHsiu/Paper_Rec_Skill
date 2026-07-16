<div align="center">

# Paper_Rec Workspace

**Literature retrieval skill + self-hosted Wiki reading lab**  
**论文检索技能 + 自研 Wiki 阅读记录工作区**

[![Version](https://img.shields.io/badge/version-2.2.0-blue.svg)](VERSION)

</div>

---

## Modules / 模块

| Module | Path | Role |
|--------|------|------|
| **Skill** | [`skill/`](skill/) | `/query_*` · `/wiki` |
| **Wiki API** | [`apps/wiki-api/`](apps/wiki-api/) | FastAPI：pages / search / graph / weekly / ask |
| **Wiki Web** | [`apps/wiki-web/`](apps/wiki-web/) | Vue3 SPA |
| **wiki-bridge** | [`packages/wiki-bridge/`](packages/wiki-bridge/) | 报告 → Markdown 同步 |
| **content** | [`content/`](content/) | Git Markdown 存储 |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Spec: `projects/wiki.txt`.

---

## Quick start

### 1. Cursor Skill — `/query_*` · `/wiki`

安装：

```bash
mkdir -p ../../.cursor/skills/paper-rec
cp -r skill/* ../../.cursor/skills/paper-rec/
```

命令（详见 [`skill/README.md`](skill/README.md)、[`skill/README.zh-CN.md`](skill/README.zh-CN.md)）：

| 命令 | 作用 |
|------|------|
| `/query_english` | 英文报告检索 |
| `/query_chinese` | 中文报告检索 |
| `/query_other` | 自适应语言检索 |
| `/wiki` | 查库论文 |
| `/wiki week` | 本周入库（去重） |
| `/wiki start` | 启动 Wiki UI |

`sync-report` 后：`/query_*` 会写入 `content/wiki/pages/<keyword>/README.md`。

### 2. Self-hosted Wiki

```powershell
# one-click
powershell -ExecutionPolicy Bypass -File apps/start-wiki.ps1

# or manually:
# cd apps/wiki-api; uvicorn app:app --reload --port 8787
# cd apps/wiki-web; npm run dev
```

Open http://127.0.0.1:5173/

### 3. Bridge（报告 → content）

```bash
cd packages/wiki-bridge
pip install -e .
python -m wiki_bridge.cli sync-report \
  --wiki-root ../.. \
  --report ./examples/sample_report.json \
  --query-id demo \
  --mark-reading
```

---

## Layout

```
Paper_Rec_Skill/
├── skill/
├── apps/wiki-api/
├── apps/wiki-web/
├── apps/start-wiki.ps1
├── content/wiki/pages/
├── content/weekly/
├── packages/wiki-bridge/
├── docs/
└── VERSION
```
