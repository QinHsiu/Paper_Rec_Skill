from __future__ import annotations

DIMENSIONS: list[dict[str, str]] = [
    {"id": "a_multi_source", "axis": "A", "label": "Multi-source recall"},
    {"id": "a_query_rewrite", "axis": "A", "label": "Query rewrite / intent"},
    {"id": "a_ranking", "axis": "A", "label": "Interpretable ranking"},
    {"id": "a_graph_explore", "axis": "A", "label": "Graph / related-paper exploration"},
    {"id": "a_saturation", "axis": "A", "label": "Dedup + discovery saturation"},
    {"id": "a_report", "axis": "A", "label": "Structured report quality"},
    {"id": "b_grounded_qa", "axis": "B", "label": "Grounded Q&A"},
    {"id": "b_citation_trust", "axis": "B", "label": "Citation trust (retraction / conflict)"},
    {"id": "b_hard_gate", "axis": "B", "label": "Numeric results hard-gate"},
    {"id": "b_survey", "axis": "B", "label": "Survey / related-work quality"},
    {"id": "b_novelty", "axis": "B", "label": "Novelty kill-switch"},
    {"id": "b_parallel_deep", "axis": "B", "label": "Parallel deep-research + compress"},
    {"id": "b_fig_vlm", "axis": "B", "label": "Figure semantic / VLM review"},
    {"id": "b_al_stop", "axis": "B", "label": "Active screening + stoppers"},
    {"id": "c_thread", "axis": "C", "label": "Cognitive Thread memory"},
    {"id": "c_drift_watch", "axis": "C", "label": "Interest drift → Watch/rank"},
    {"id": "c_wiki_filter", "axis": "C", "label": "Wiki filter apply"},
    {"id": "c_mcp_session", "axis": "C", "label": "MCP deferred research_id"},
    {"id": "c_bot_push", "axis": "C", "label": "Bot / webhook push"},
    {"id": "c_local_audit", "axis": "C", "label": "Local auditability / CLI"},
]

OSS_COMPETITORS = [
    "AutoResearchClaw",
    "AI-Scientist",
    "AI-Scientist-v2",
    "AgentLaboratory",
    "AI-Researcher",
    "AI-Research-SKILLs",
    "PaperPilot",
    "paper-search-pro",
    "paper-qa",
    "OpenScholar",
    "asreview",
    "AutoSurvey",
    "gpt-researcher",
    "STORM",
    "open_deep_research",
    "Curie",
    "khoj",
    "gptr-mcp",
]

CLOSED_COMPETITORS = [
    "Elicit",
    "Consensus",
    "Scite",
    "ResearchRabbit",
    "Connected Papers",
    "Semantic Scholar",
    "NotebookLM",
]

CELL_STATES = frozenset({"领先", "持平", "落后", "不适用"})
