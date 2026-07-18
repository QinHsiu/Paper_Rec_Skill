"""LitSearch evaluation — Recall@K / MRR / nDCG against princeton-nlp/LitSearch.

Protocol (Paper_Rec Phase 1A):
  - Corpus: official ``corpus_clean`` (64183 docs) — no external arXiv/S2 injection.
  - Methods: ``bm25`` (lexical baseline) · ``prerank`` (wiki_bridge prerank = BM25+recency+cite).
  - Metrics: Recall@{1,5,10}, MRR, nDCG@10 (binary relevance via gold corpusids).

Large HF downloads stay under benchmarks/litsearch/cache/ (gitignored).
"""
from __future__ import annotations

import json
import math
import re
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from .prerank import prerank, tokenize


def _doc_id(row: dict[str, Any]) -> str:
    for k in ("corpusid", "corpus_id", "paper_id", "id"):
        if row.get(k) is not None:
            return str(row[k])
    return ""


def _gold_ids(row: dict[str, Any]) -> list[str]:
    raw = row.get("corpusids") or row.get("corpus_ids") or row.get("gold_ids") or []
    if isinstance(raw, (str, int)):
        return [str(raw)]
    return [str(x) for x in raw if x is not None]


def _title_abs(row: dict[str, Any]) -> tuple[str, str]:
    title = str(row.get("title") or "")
    abstract = str(row.get("abstract") or row.get("summary") or "")
    return title, abstract


# --- metrics -----------------------------------------------------------------


def recall_at_k(ranked_ids: list[str], gold: set[str], k: int) -> float:
    if not gold:
        return 0.0
    top = set(ranked_ids[:k])
    return len(top & gold) / len(gold)


def hit_at_k(ranked_ids: list[str], gold: set[str], k: int) -> float:
    """Any-gold-in-top-k (common LitSearch-style hit rate)."""
    if not gold:
        return 0.0
    return 1.0 if set(ranked_ids[:k]) & gold else 0.0


def mrr(ranked_ids: list[str], gold: set[str]) -> float:
    for i, pid in enumerate(ranked_ids, start=1):
        if pid in gold:
            return 1.0 / i
    return 0.0


def ndcg_at_k(ranked_ids: list[str], gold: set[str], k: int) -> float:
    if not gold:
        return 0.0
    dcg = 0.0
    for i, pid in enumerate(ranked_ids[:k], start=1):
        if pid in gold:
            dcg += 1.0 / math.log2(i + 1)
    ideal_hits = min(len(gold), k)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_hits + 1))
    return dcg / idcg if idcg else 0.0


# --- inverted BM25 (full-corpus friendly) ------------------------------------


class Bm25Index:
    """In-memory BM25 over tokenized corpus (built once)."""

    def __init__(self, docs: list[dict[str, Any]], *, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.ids: list[str] = []
        self.titles: list[str] = []
        self.abstracts: list[str] = []
        self.years: list[int | None] = []
        self._toks: list[list[str]] = []
        self._tf: list[Counter[str]] = []
        self._df: Counter[str] = Counter()
        self._postings: dict[str, list[int]] = defaultdict(list)

        for row in docs:
            pid = _doc_id(row)
            title, abstract = _title_abs(row)
            text = f"{title} {abstract}"
            toks = tokenize(text)
            self.ids.append(pid)
            self.titles.append(title)
            self.abstracts.append(abstract)
            y = None
            for key in ("year", "yearpublished", "yearPublished"):
                if row.get(key) is not None:
                    try:
                        y = int(row[key])
                    except (TypeError, ValueError):
                        m = re.search(r"(20\d{2}|19\d{2})", str(row[key]))
                        y = int(m.group(1)) if m else None
                    break
            self.years.append(y)
            self._toks.append(toks)
            tf = Counter(toks)
            self._tf.append(tf)
            self._df.update(set(toks))
            for t in set(toks):
                self._postings[t].append(len(self.ids) - 1)

        self.N = len(self.ids)
        self.avgdl = sum(len(t) for t in self._toks) / max(self.N, 1)

    def score_query(self, query: str, *, top_k: int = 100) -> list[tuple[str, float]]:
        q_tokens = tokenize(query)
        if not q_tokens or self.N == 0:
            return []
        scores: dict[int, float] = defaultdict(float)
        N = self.N
        for term in q_tokens:
            n_qi = self._df.get(term, 0)
            if n_qi == 0:
                continue
            idf = math.log(1 + (N - n_qi + 0.5) / (n_qi + 0.5))
            for di in self._postings.get(term, []):
                freq = self._tf[di].get(term, 0)
                dl = len(self._toks[di]) or 1
                scores[di] += idf * (freq * (self.k1 + 1)) / (
                    freq + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                )
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [(self.ids[i], float(s)) for i, s in ranked]

    def as_candidates(self, indices: Iterable[int] | None = None) -> list[dict[str, Any]]:
        idxs = range(self.N) if indices is None else indices
        out = []
        for i in idxs:
            out.append(
                {
                    "corpusid": self.ids[i],
                    "paper_id": self.ids[i],
                    "title": self.titles[i],
                    "abstract": self.abstracts[i],
                    "summary": self.abstracts[i],
                    "year": self.years[i],
                }
            )
        return out


def rank_bm25(index: Bm25Index, query: str, *, top_k: int = 100) -> list[str]:
    return [pid for pid, _ in index.score_query(query, top_k=top_k)]


def rank_prerank(
    index: Bm25Index,
    query: str,
    *,
    top_k: int = 100,
    candidate_pool: int = 500,
) -> list[str]:
    """BM25 retrieve candidate_pool, then wiki_bridge.prerank re-score → top_k."""
    bm25_hits = index.score_query(query, top_k=candidate_pool)
    if not bm25_hits:
        return []
    id_to_i = {pid: i for i, pid in enumerate(index.ids)}
    cands = []
    for pid, lex in bm25_hits:
        i = id_to_i.get(pid)
        if i is None:
            continue
        cands.append(
            {
                "corpusid": pid,
                "paper_id": pid,
                "title": index.titles[i],
                "abstract": index.abstracts[i],
                "summary": index.abstracts[i],
                "year": index.years[i],
                "_bm25": lex,
            }
        )
    out = prerank(query, cands, top_k=top_k, use_citations=False)
    return [str(x.get("paper_id") or x.get("corpusid")) for x in out["items"]]


# --- data loading ------------------------------------------------------------


def load_fixture(fixture_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    queries = json.loads((fixture_dir / "queries.json").read_text(encoding="utf-8"))
    corpus = json.loads((fixture_dir / "corpus.json").read_text(encoding="utf-8"))
    return queries, corpus


def load_hf(
    *,
    cache_dir: Path | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        from datasets import load_dataset
    except ImportError as e:
        raise ImportError(
            "LitSearch full eval requires `pip install datasets`. "
            "Use --fixture for offline smoke."
        ) from e
    kwargs: dict[str, Any] = {}
    if cache_dir:
        cache_dir.mkdir(parents=True, exist_ok=True)
        kwargs["cache_dir"] = str(cache_dir)
    q = load_dataset("princeton-nlp/LitSearch", "query", split="full", **kwargs)
    c = load_dataset("princeton-nlp/LitSearch", "corpus_clean", split="full", **kwargs)
    queries = [dict(row) for row in q]
    corpus = [dict(row) for row in c]
    return queries, corpus


# --- evaluate ----------------------------------------------------------------


def evaluate(
    queries: list[dict[str, Any]],
    corpus: list[dict[str, Any]],
    *,
    method: str = "bm25",
    ks: tuple[int, ...] = (1, 5, 10),
    top_k: int = 100,
    limit_queries: int | None = None,
    candidate_pool: int = 500,
) -> dict[str, Any]:
    t0 = time.time()
    index = Bm25Index(corpus)
    rows: list[dict[str, Any]] = []
    qset = queries[: limit_queries] if limit_queries else queries

    agg: dict[str, list[float]] = defaultdict(list)
    for qi, qrow in enumerate(qset):
        qtext = str(qrow.get("query") or "")
        gold = set(_gold_ids(qrow))
        if method == "prerank":
            ranked = rank_prerank(index, qtext, top_k=top_k, candidate_pool=candidate_pool)
        else:
            ranked = rank_bm25(index, qtext, top_k=top_k)
        m = {
            "query_idx": qi,
            "query": qtext[:200],
            "n_gold": len(gold),
            "mrr": round(mrr(ranked, gold), 6),
        }
        for k in ks:
            m[f"recall@{k}"] = round(recall_at_k(ranked, gold, k), 6)
            m[f"hit@{k}"] = round(hit_at_k(ranked, gold, k), 6)
            if k == 10:
                m["ndcg@10"] = round(ndcg_at_k(ranked, gold, 10), 6)
        for k, v in m.items():
            if isinstance(v, float) and k not in ("query_idx",):
                agg[k].append(v)
        rows.append(m)

    means = {k: round(sum(vs) / len(vs), 6) if vs else 0.0 for k, vs in agg.items()}
    return {
        "bench": "litsearch",
        "method": method,
        "n_queries": len(qset),
        "n_corpus": len(corpus),
        "protocol": {
            "corpus": "corpus_clean | fixture",
            "external_search": False,
            "ks": list(ks),
            "top_k": top_k,
            "candidate_pool": candidate_pool if method == "prerank" else None,
        },
        "metrics_mean": means,
        "elapsed_sec": round(time.time() - t0, 2),
        "per_query": rows,
    }


def write_result(path: Path, result: dict[str, Any], *, slim: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(result)
    if slim:
        payload["per_query"] = payload.get("per_query", [])[:20]
        payload["per_query_note"] = "truncated to first 20; full list omitted for git-friendly runs"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
