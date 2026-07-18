# Contributing to Paper_Rec

Thanks for helping. This repo is a **research OS** (literature skill + Wiki + Cognitive Thread + exp sandbox). Contributions should deepen **research memory**, not turn the project into a manuscript pipeline or a second literature-search MCP.

## Principles (read first)

| Do | Don't |
|----|--------|
| Keep Git Markdown as the source of truth | Add SaaS-only state without a file mirror |
| Default auto-assoc / claim / evidence to `suggested` until a human/agent gate | Silently write `accepted` membership |
| Compose with [article-mcp](https://github.com/fangfuzha/article-mcp) for search | Duplicate generic multi-source search MCP tools |
| Prefer small, reviewable PRs | Bundle unrelated skill + UI + docs rewrites |

Design contracts: [`docs/THREAD_DESIGN.md`](docs/THREAD_DESIGN.md) · [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) · [`docs/OPTIMIZATION_PLAN.md`](docs/OPTIMIZATION_PLAN.md).

## Dev environment

**Requirements:** Python 3.10+, Node 18+ (Wiki UI), Git.

```bash
git clone https://github.com/QinHsiu/Paper_Rec_Skill.git
cd Paper_Rec_Skill

# Bridge + MCP
pip install -e packages/wiki-bridge -e packages/thread-mcp
pip install "mcp>=1.0"   # only if you run Thread Memory MCP

# Wiki API
pip install -r apps/wiki-api/requirements.txt   # if present; else: fastapi uvicorn

# Wiki Web
cd apps/wiki-web && npm install && cd ../..
```

**Run Wiki locally**

```bash
# terminal 1 — API (from repo root; PAPER_REC_ROOT optional if cwd is workspace)
cd apps/wiki-api && uvicorn app.main:app --reload --port 8787

# terminal 2 — SPA
cd apps/wiki-web && npm run dev
```

**Smoke CLI**

```bash
python -m wiki_bridge.cli thread-list --wiki-root .
python -m wiki_bridge.cli thread-show --wiki-root . --id mm-llm-alignment
```

MCP config: [`docs/MCP.md`](docs/MCP.md) (set `PAPER_REC_ROOT` only; no `PYTHONPATH`).

## Where to change what

| Goal | Touch |
|------|--------|
| Retrieval / report workflow | `skill/SKILL.md`, `skill/output-template.md`, `skill/sources-reference.md` |
| Experiment orchestration | `skill-exp/` (+ `reference/`) |
| Plot styles / venues | `skill-draw/lib/` |
| Thread / evidence / sync | `packages/wiki-bridge/wiki_bridge/` |
| Thread Memory MCP | `packages/thread-mcp/` |
| REST API | `apps/wiki-api/` |
| SPA | `apps/wiki-web/src/` |
| Sample content | `content/threads/`, `content/exp/demo-*` (do **not** commit private exps) |

Skill copies under a parent monorepo `.agents/skills/` (if any) should be synced from `skill/` / `skill-exp/` / `skill-draw/` when you change those packages.

## Changing Skills

1. Edit Markdown / `reference/` under the skill package.
2. Bump `skill*/VERSION` + `skill*/CHANGELOG.md` (semver; skill-local).
3. If the change is user-visible at workspace level, also bump root `VERSION` + `CHANGELOG.md`.
4. Keep Module numbers and contracts aligned with `docs/THREAD_DESIGN.md`.

## PR checklist

Before opening a PR:

- [ ] Scope is one concern (docs / skill / bridge / UI).
- [ ] No secrets, no private datasets, no ignored `content/exp/*` research dumps.
- [ ] `CHANGELOG` / `VERSION` updated when behavior or docs ship to users.
- [ ] New Thread/API fields documented in `THREAD_DESIGN.md` (or MCP.md for tools).
- [ ] Default gates stay `suggested` unless the user explicitly accepts.
- [ ] Brief test note: CLI command, API route, or UI path you exercised.

**PR title style:** `fix(scope): …` / `fix(scope): …` / `docs: …` / `release x.y.z: …`

## Good first issues

See [`docs/GOOD_FIRST_ISSUES.md`](docs/GOOD_FIRST_ISSUES.md). On GitHub, label matching issues with `good first issue`.

## Discussions & questions

Use [GitHub Discussions](https://github.com/QinHsiu/Paper_Rec_Skill/discussions) for design questions and “how do I run X?”. Use Issues for concrete bugs and actionable features.

If Discussions is not enabled yet on the repo: **Settings → General → Features → Discussions**.

## Tutorial

Walkthrough: [`docs/tutorials/thread-research-memory.md`](docs/tutorials/thread-research-memory.md) (sample thread `mm-llm-alignment`).

## License

By contributing, you agree your work is released under the MIT License (see [`LICENSE`](LICENSE)).
