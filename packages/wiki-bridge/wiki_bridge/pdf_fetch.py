"""Legal OA PDF fetch chain → local file (then pdf_ingest). No Sci-Hub."""
from __future__ import annotations

import os
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from .conventions import parse_frontmatter
from .pdf_ingest import ingest_pdf, paper_dir
from .writer import resolve_content_root

USER_AGENT = "PaperRecSkill/2.17 (pdf-fetch; research; mailto:local)"
DOWNLOAD_TIMEOUT = 45


def _http_get_bytes(url: str, *, timeout: int = DOWNLOAD_TIMEOUT) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            ctype = (resp.headers.get("Content-Type") or "").lower()
            if "pdf" not in ctype and not data.startswith(b"%PDF"):
                # some servers omit content-type
                if not data.startswith(b"%PDF"):
                    return None
            return data
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return None


def _http_get_json(url: str, *, timeout: int = 15) -> dict[str, Any] | None:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY") or os.environ.get("S2_API_KEY")
    if api_key and "semanticscholar.org" in url:
        req.add_header("x-api-key", api_key)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            import json

            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError):
        return None


def paper_meta(wiki_root: Path, paper_path: str) -> dict[str, Any]:
    readme = resolve_content_root(wiki_root) / paper_path.strip("/") / "README.md"
    if not readme.is_file():
        raise FileNotFoundError(f"wiki paper not found: {paper_path}")
    meta, _ = parse_frontmatter(readme.read_text(encoding="utf-8"))
    return meta


def _normalize_arxiv(arxiv: str) -> str:
    a = arxiv.strip()
    a = re.sub(r"^arxiv:", "", a, flags=re.I)
    a = a.replace("https://arxiv.org/abs/", "").replace("http://arxiv.org/abs/", "")
    a = a.replace("https://arxiv.org/pdf/", "").replace(".pdf", "")
    return a.strip("/")


def _try_save(data: bytes, dest: Path) -> Path | None:
    if not data or not data.startswith(b"%PDF"):
        return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return dest


def resolve_candidates(meta: dict[str, Any]) -> list[tuple[str, str]]:
    """Ordered (source_name, url) candidates — legal OA only."""
    out: list[tuple[str, str]] = []
    arxiv = str(meta.get("arxiv") or "").strip()
    doi = str(meta.get("doi") or "").strip().removeprefix("https://doi.org/")
    pdf_url = str(meta.get("pdf_url") or meta.get("open_access_url") or "").strip()
    pmc = str(meta.get("pmc") or meta.get("pmcid") or "").strip()

    if arxiv:
        aid = _normalize_arxiv(arxiv)
        out.append(("arxiv", f"https://arxiv.org/pdf/{aid}.pdf"))

    if pdf_url and pdf_url.lower().endswith(".pdf"):
        out.append(("meta_pdf_url", pdf_url))

    # Semantic Scholar openAccessPdf
    s2_id = None
    if doi:
        s2_id = f"DOI:{doi}"
    elif arxiv:
        s2_id = f"ARXIV:{_normalize_arxiv(arxiv)}"
    if s2_id:
        data = _http_get_json(
            "https://api.semanticscholar.org/graph/v1/paper/"
            + urllib.parse.quote(s2_id, safe=":")
            + "?fields=openAccessPdf,externalIds,title"
        )
        if data:
            oa = (data.get("openAccessPdf") or {}).get("url")
            if oa:
                out.append(("s2_oa", oa))
            ext = data.get("externalIds") or {}
            if not arxiv and ext.get("ArXiv"):
                out.append(("arxiv", f"https://arxiv.org/pdf/{ext['ArXiv']}.pdf"))
            if not pmc and (ext.get("PubMedCentral") or ext.get("PMC")):
                pmc = str(ext.get("PubMedCentral") or ext.get("PMC"))

    # Unpaywall
    email = os.environ.get("UNPAYWALL_EMAIL") or os.environ.get("OPENALEX_EMAIL")
    if doi and email:
        up = _http_get_json(
            f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={urllib.parse.quote(email)}"
        )
        if up:
            best = up.get("best_oa_location") or {}
            u = best.get("url_for_pdf") or best.get("url")
            if u:
                out.append(("unpaywall", u))

    # bioRxiv / medRxiv style
    if doi.lower().startswith("10.1101/"):
        out.append(("biorxiv", f"https://www.biorxiv.org/content/{doi}v1.full.pdf"))
        out.append(("medrxiv", f"https://www.medrxiv.org/content/{doi}v1.full.pdf"))

    if pmc:
        if not pmc.upper().startswith("PMC"):
            pmc = f"PMC{pmc}"
        out.append(("pmc", f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/pdf/"))

    # dedupe urls keep order
    seen: set[str] = set()
    uniq: list[tuple[str, str]] = []
    for name, url in out:
        if url in seen:
            continue
        seen.add(url)
        uniq.append((name, url))
    return uniq


def download_oa_pdf(
    meta: dict[str, Any],
    *,
    dest_dir: Path | None = None,
) -> dict[str, Any]:
    """Try legal OA URLs; return {success, file_path, source, attempts, message}."""
    candidates = resolve_candidates(meta)
    attempts: list[dict[str, str]] = []
    if not candidates:
        return {
            "success": False,
            "file_path": None,
            "source": None,
            "attempts": [],
            "message": "No arXiv/DOI/OA URL on page meta. Add arxiv: or doi: frontmatter.",
        }

    dest_dir = dest_dir or Path(tempfile.mkdtemp(prefix="paper_rec_pdf_"))
    dest_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(meta.get("title") or "paper"))[:40] or "paper"
    dest = dest_dir / f"{slug}.pdf"

    for source, url in candidates:
        attempts.append({"source": source, "url": url})
        data = _http_get_bytes(url)
        if data and _try_save(data, dest):
            return {
                "success": True,
                "file_path": str(dest),
                "source": source,
                "attempts": attempts,
                "message": f"Downloaded via {source}",
            }

    return {
        "success": False,
        "file_path": None,
        "source": None,
        "attempts": attempts,
        "message": "Could not download a legal OA PDF. Upload manually or set UNPAYWALL_EMAIL.",
    }


def fetch_and_ingest(
    wiki_root: Path,
    paper_path: str,
    *,
    keep_pdf: bool = True,
) -> dict[str, Any]:
    """Download OA PDF for an existing wiki page and run pdf_ingest."""
    wiki_root = Path(wiki_root).resolve()
    paper_path = paper_path.strip("/")
    meta = paper_meta(wiki_root, paper_path)
    d = paper_dir(wiki_root, paper_path)
    pdf_dir = d / "_pdf"
    dl = download_oa_pdf(meta, dest_dir=pdf_dir if keep_pdf else None)
    if not dl.get("success"):
        return {"paper_path": paper_path, "fetch": dl, "ingest": None}

    pdf_path = Path(dl["file_path"])
    ingest = ingest_pdf(wiki_root, pdf_path, paper_path, title=str(meta.get("title") or ""))
    if not keep_pdf and pdf_path.is_file() and pdf_dir not in pdf_path.parents:
        try:
            pdf_path.unlink()
        except OSError:
            pass
    return {"paper_path": paper_path, "fetch": dl, "ingest": ingest}
