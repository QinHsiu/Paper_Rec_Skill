# Migration Notes / 迁移说明

**Nothing from the Skill docs was deleted** when the workspace was split; Skill lives under `skill/`.

## Path mapping / 路径对照

| Before (repo root) | After |
|--------------------|--------|
| `SKILL.md` | [`skill/SKILL.md`](../skill/SKILL.md) |
| `sources-reference.md` | [`skill/sources-reference.md`](../skill/sources-reference.md) |
| `output-template.md` | [`skill/output-template.md`](../skill/output-template.md) |
| `examples.md` | [`skill/examples.md`](../skill/examples.md) |
| Skill READMEs | [`skill/README*.md`](../skill/) |

## Current layout (2.2.0+)

| Path | Role |
|------|------|
| `README.md` | Workspace overview |
| `apps/wiki-api/` | FastAPI Wiki backend |
| `apps/wiki-web/` | Vue3 Wiki SPA |
| `apps/start-wiki.ps1` | One-click launch |
| `content/` | Git Markdown store |
| `packages/wiki-bridge/` | Report → Wiki sync CLI (`wiki_bridge`) |
| `docs/ARCHITECTURE.md` | Module boundaries |

## Removed

- `services/otter-wiki/` — deleted
- `docker-compose.yml` (Otter image) — deleted
- Package rename: `otter_bridge` → `wiki_bridge`

## Skill install path（跨平台）

```
skill/      →  .agents/skills/paper-rec/
skill-exp/  →  .agents/skills/exp-sandbox/
```

（或各平台等价的 skills / prompts 目录。）
