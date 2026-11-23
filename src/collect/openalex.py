"""References of a paper through OpenAlex (title search), cached on disk.

Only `id`, `title`, `publication_year` and `referenced_works` are requested:
citations received, authors and publication source are never fetched (they
would leak the decision or break double-blind review).

One result file per submission; an existing file is never fetched again.
"""

import os
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import requests

from src.collect import store
from src.collect.client import RateLimiter

USER_AGENT = "peer-review-kg/0.1 (research data collection)"


def result_path(raw_dir: Path, venue: str, year: int, forum_id: str) -> Path:
    return raw_dir / "openalex" / venue / str(year) / f"{forum_id}.json"


def load_result(raw_dir: Path, venue: str, year: int, forum_id: str) -> dict[str, Any] | None:
    path = result_path(raw_dir, venue, year, forum_id)
    return store.read_json(path) if path.exists() else None


def normalise_title(title: str) -> str:
    """Lower-case alphanumeric words separated by single spaces."""
    return " ".join(re.sub(r"[^\w\s]", " ", title.lower()).split())


def title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalise_title(a), normalise_title(b)).ratio()


def best_match(title: str, candidates: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, float]:
    """Candidate whose title is closest to `title`, with the similarity score."""
    best, best_score = None, 0.0
    for work in candidates:
        score = title_similarity(title, work.get("title") or "")
        if score > best_score:
            best, best_score = work, score
    return best, best_score


def match_row(result: dict[str, Any], threshold: float) -> dict[str, Any]:
    """Matching outcome for one stored result (used by the collection report)."""
    work, score = best_match(result["query_title"], result.get("candidates") or [])
    matched = work is not None and score >= threshold
    references = (work.get("referenced_works") or []) if matched else []
    return {
        "matched": matched,
        "match_score": round(score, 4),
        "openalex_id": work["id"].rsplit("/", 1)[-1] if matched else None,
        "n_references": len(references),
    }


class OpenAlexClient:
    def __init__(self, cfg: dict[str, Any]) -> None:
        self.base_url = cfg["base_url"].rstrip("/")
        self.select = ",".join(cfg["select"])
        self.year_tolerance = int(cfg["year_tolerance"])
        self.limiter = RateLimiter(cfg["max_requests_per_minute"])
        self.api_key = os.environ.get("OPENALEX_API_KEY", "")
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        self.n_requests = 0

    def search_title(self, title: str, year: int) -> dict[str, Any]:
        """Works whose title matches, published around the conference year."""
        query = normalise_title(title)
        low, high = year - 1 - self.year_tolerance, year + self.year_tolerance
        params = {
            "filter": f"title.search:{query},publication_year:{low}-{high}",
            "select": self.select,
            "per-page": 5,
        }
        if self.api_key:
            params["api_key"] = self.api_key
        self.limiter.wait()
        self.n_requests += 1
        response = self.session.get(self.base_url + "/works", params=params, timeout=60)
        response.raise_for_status()
        return response.json()

    def collect(
        self, raw_dir: Path, venue: str, year: int, forum_id: str, title: str, force: bool = False
    ) -> str:
        """Fetch and store the candidates for one submission. Returns "skipped" if cached."""
        path = result_path(raw_dir, venue, year, forum_id)
        if path.exists() and not force:
            return "skipped"
        body = self.search_title(title, year)
        store.write_json(
            path,
            {
                "forum_id": forum_id,
                "year": year,
                "query_title": title,
                "candidates": body.get("results") or [],
            },
        )
        return "collected"
