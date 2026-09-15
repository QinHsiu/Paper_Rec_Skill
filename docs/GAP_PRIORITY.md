# Gap Priority

Derived from `evals/competitor_scorecard/data.json` cells with state `落后`.

| Severity | Dimension | Wave | Target CLI | Competitors | Rationale |
|----------|-----------|------|------------|-------------|-----------|
| High | b_novelty | W2 | `novelty-check` | AI-Scientist | AI-Scientist multi-round novelty critic deeper than single-shot novelty-check. |
| High | b_survey | W2 | `survey-draft` | AutoSurvey | outline-merge + subsection RAG + cite check deeper than survey-draft heuristic. |
| High | c_drift_watch | W2 | `thread-delta` | ResearchRabbit | Interest/collection drift patterns; Paper_Rec feedback unused for Watch/rank profile. |
| High | c_wiki_filter | W2 | `wiki-filter-apply` | khoj | khoj applies wiki filters on pages; Paper_Rec parse-only without apply. |
| Medium | a_graph_explore | W3 | `a-graph-explore` | ResearchRabbit, Connected Papers, Semantic Scholar | ResearchRabbit visual related-paper graph ahead of Paper_Rec graph exploration. |
| Medium | a_query_rewrite | W3 | `a-query-rewrite` | STORM | Persona-parallel question lanes / Co-STORM mind map cover skew better than single rewrite. |
| Medium | a_ranking | W3 | `a-ranking` | asreview | Nature-grade AL ranking/balancer deeper than screen-next TF-IDF hybrid. |
| Medium | a_report | W3 | `a-report` | AutoSurvey, Elicit | Large-corpus survey generation quality ahead of TF-IDF survey-draft. |
| Medium | b_grounded_qa | W3 | `b-grounded-qa` | paper-qa, OpenScholar, Elicit, Consensus, NotebookLM | paper-qa map-reduce relevance + refuse; Paper_Rec cutoff thinner than agentic paper-qa. |
| Medium | c_mcp_session | W3 | `c-mcp-session` | gptr-mcp | research_id → deferred write_report first-class; Paper_Rec research-session thinner in thread-MCP. |

## Wave mapping

- **W1:** Critical trust/depth engines only.
- **W2:** High coverage + thread.
- **W3:** Medium polish + prove narrative.

SP1+ plans must not start until this file exists and Critical rows are acknowledged.
