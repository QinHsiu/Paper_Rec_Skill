# Iterative Deep-Search Final Fix Report

Date: 2026-08-14

## Fix 1 — Live arXiv request pacing

Root cause: `ArxivQuerySearcher.search` called the API on every invocation without
the inter-request delay used by `arxiv_watch`.

Change: added `wait_time=3.0` by default, delayed only between requests, and
allowed both `wait_time=0` and an injectable sleep function for tests.

Covering test: `test_arxiv_query_searcher_waits_between_requests`.

Command:

```text
python -m pytest packages/wiki-bridge/tests/test_deep_search.py -q
```

Output:

```text
20 passed in 1.01s
```

## Fix 2 — `{"papers": [...]}` seed dispatch

Root cause: CLI classified any dict containing a list-valued field as a query
table before checking the documented `papers` seed shape, so the topic query
could have no matching key and silently return zero papers.

Change: dispatch now prefers a top-level list, then `papers` / `documents` seed
lists keyed by the topic, and only then falls back to list-valued query-table
entries.

Covering test: `test_cli_deep_search_papers_seed_is_used_for_topic`.

Command:

```text
python -m pytest packages/wiki-bridge/tests/test_deep_search.py -q
```

Output:

```text
20 passed in 1.01s
```

## Fix 3 — Missing `--thread` validation

Root cause: `persist_deep_search` created draft output files before
`append_query_trace` discovered that `thread.json` did not exist.

Change: persistence validates the thread before creating output directories;
the CLI performs the same validation and emits one JSON error with exit code 2,
without a traceback.

Covering test: `test_cli_deep_search_missing_thread_fails_without_writing`.

Command:

```text
python -m pytest packages/wiki-bridge/tests/test_deep_search.py -q
```

Output:

```text
20 passed in 1.01s
```

## Fix 4 — Module 2b old refine-wave guard

Root cause: the skill documented the deep-search override but still allowed the
old one-wave refine Actions to run afterward.

Change: added an Action 0 guard to skip those old Actions when `--breadth` /
`--depth` was passed or live deep-search already ran, using the markdown report
as the user-facing output.

Covering test: `test_skill_mentions_breadth_depth_flags` now asserts the guard
text.

Command:

```text
python -m pytest packages/wiki-bridge/tests/test_deep_search.py -q
```

Output:

```text
20 passed in 1.01s
```

## Final verification

Commands:

```text
python -m pytest packages/wiki-bridge/tests/test_deep_search.py -q
python -m pytest packages/wiki-bridge/tests -q
```

Output:

```text
20 passed in 1.01s
65 passed in 1.60s
```

Lint diagnostics reported no errors for the edited Python files.
