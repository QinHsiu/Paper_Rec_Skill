# Good first issues

Starter tasks that improve docs/UX without requiring deep architecture changes. Pick one, open an Issue (or claim an existing one), and link this file.

Suggested GitHub labels: `good first issue` · `docs` · `skill` · `wiki-ui`.

---

## 1. Venue preset blurb (`docs` / `skill-draw`)

**Why:** `/draw --venue` has presets; newcomers need a one-page cheat sheet.

**Do:**
- Add a short table to `skill-draw/README.md` (or `examples.md`): venue → typical use → CLI example.
- Keep it to the existing venues in `skill-draw/lib/venues.py` (do not invent new presets unless asked).

**Done when:** A reader can pick `cvpr` / `icml` / … from the table alone.

---

## 2. Evidence UI copy polish (`wiki-ui`)

**Why:** PageView「挂到主线」and ThreadDetail evidence panel are functional; microcopy can be clearer for first-time users.

**Do:**
- Review `apps/wiki-web/src/views/PageView.vue` and `ThreadDetailView.vue` strings (CN/EN if both exist).
- Clarify: select text → choose thread + claim + stance → gate `suggested` vs accept.
- No new dependencies; keep layout minimal.

**Done when:** Empty states explain the Claim–Evidence Map in one sentence.

---

## 3. Thread tutorial screenshots / checklist (`docs`)

**Why:** [`docs/tutorials/thread-research-memory.md`](tutorials/thread-research-memory.md) is text-first.

**Do:**
- Add a “Verify locally” checklist (exact CLI commands already in the tutorial).
- Optional: ASCII or mermaid diagram of hypothesis → claim → evidence → exp.

**Done when:** Someone can finish the tutorial with only the repo clone + tutorial file.

---

## 4. `query_iter` timeline styling (`wiki-ui`)

**Why:** `ThreadDetailView` already special-cases `query_iter`; formatting can be denser.

**Do:**
- Improve display of round / path_id / raw_hits / kept / query snippets.
- Keep events append-only; no schema change unless documented in `THREAD_DESIGN.md`.

**Done when:** A `query_iter` event is readable without expanding raw JSON.

---

## 5. Compare-exp URL hint (`docs` / `wiki-ui`)

**Why:** ExpDetail supports `?compare=<exp_id>` and `?poll=5s`.

**Do:**
- Document the query params under Experiments in README or a short `docs/` note.
- Optional: show a muted hint line under the compare input in `ExpDetailView.vue`.

**Done when:** Users discover multi-run compare without reading source.

---

## Out of scope for “first issue”

- Full PDF claim extraction
- New literature-search MCP competing with article-mcp
- TensorBoard-parity live event streams
- Committing private / large experiment trees under `content/exp/`
