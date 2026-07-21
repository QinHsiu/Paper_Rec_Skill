# Wiki / library query filters (khoj-inspired)

When listing or searching the reading library (`/wiki` / wiki-web), support operators in the user string:

| Token | Meaning |
|-------|---------|
| `+term` | Must include |
| `-term` | Must exclude (whole-word) |
| `dt>=2024` / `dt<2023-06` | Year/date lower/upper bound from frontmatter |
| `file:pdf` / `file:fulltext` | Has PDF ingest / fulltext.md |

Example: `+RAG -survey dt>=2023 file:fulltext`

Agent: parse filters before scanning `content/wiki/pages`; do not send filter tokens to OpenAlex as topic terms (same spirit as `rank-intent`).
