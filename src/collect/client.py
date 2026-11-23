"""OpenReview access: authenticated clients, API version detection, rate-limited raw GET.

Requests go through the authenticated `requests` session of openreview-py (which
already retries on 429/5xx and honours Retry-After) but return the raw JSON of
the API, so that data/raw/ keeps every field unmodified.
"""

import os
import time
from typing import Any

import openreview
import requests
from openreview import tools

BASE_URLS = {"v1": "https://api.openreview.net", "v2": "https://api2.openreview.net"}
PAGE_SIZE = 1000
LOGIN_RETRY_SECONDS = 90  # the login endpoint allows 3 calls per short window
MAX_ATTEMPTS = 4
REQUEST_TIMEOUT = 120


class OpenReviewError(RuntimeError):
    """Non-200 answer from the OpenReview API."""

    def __init__(self, status: int, name: str, message: str) -> None:
        super().__init__(f"HTTP {status} {name}: {message}")
        self.status = status
        self.name = name
        self.message = message

    def as_dict(self) -> dict[str, Any]:
        return {"status": self.status, "name": self.name, "message": self.message}


class RateLimitExceeded(OpenReviewError):
    """HTTP 429 whose waiting time exceeds what the run is allowed to wait."""

    def __init__(self, endpoint: str, retry_after: float, policy: str | None) -> None:
        super().__init__(
            429,
            "RateLimitError",
            f"{endpoint}: quota exhausted (policy {policy}), retry after {retry_after:.0f} s",
        )
        self.endpoint = endpoint
        self.retry_after = retry_after
        self.policy = policy

    def as_dict(self) -> dict[str, Any]:
        return {**super().as_dict(), "endpoint": self.endpoint,
                "retry_after_seconds": self.retry_after, "policy": self.policy}


class RateLimiter:
    """Enforce a minimum interval between two requests."""

    def __init__(self, max_per_minute: float, clock=time.monotonic, sleep=time.sleep) -> None:
        if max_per_minute <= 0:
            raise ValueError("max_per_minute must be positive")
        self.min_interval = 60.0 / max_per_minute
        self._clock = clock
        self._sleep = sleep
        self._last: float | None = None

    def wait(self) -> None:
        now = self._clock()
        if self._last is not None:
            remaining = self.min_interval - (now - self._last)
            if remaining > 0:
                self._sleep(remaining)
                now = self._clock()
        self._last = now


class OpenReviewSession:
    """Rate-limited, authenticated access to both API versions."""

    def __init__(self, max_requests_per_minute: float, max_rate_limit_wait: float = 120) -> None:
        self.limiter = RateLimiter(max_requests_per_minute)
        self.max_rate_limit_wait = max_rate_limit_wait
        self.n_requests = 0
        # Rate-limit policy announced by the server, per "api endpoint" (e.g. "500;w=3600").
        self.policies: dict[str, str] = {}
        self._clients: dict[str, Any] = {}
        # Plain session: the one of openreview-py silently sleeps on 429, however long.
        self._http = requests.Session()

    def _client(self, api: str):
        if api not in self._clients:
            username = os.environ.get("OPENREVIEW_USERNAME")
            password = os.environ.get("OPENREVIEW_PASSWORD")
            if not username or not password:
                raise RuntimeError(
                    "OPENREVIEW_USERNAME / OPENREVIEW_PASSWORD are not set. Put them in .env "
                    "and run with: uv run --env-file .env python scripts/01_collect.py ..."
                )
            # Log in once (the login endpoint allows very few calls) and share the
            # token with the API v1 client.
            if "v2" not in self._clients:
                self._clients["v2"] = self._login(username, password)
            if api == "v1":
                self.limiter.wait()
                self._clients["v1"] = openreview.Client(
                    baseurl=BASE_URLS["v1"], token=self._clients["v2"].token
                )
        return self._clients[api]

    def _login(self, username: str, password: str):
        """Log in; if the login endpoint is rate limited, wait as told and retry once."""
        for attempt in range(2):
            self.limiter.wait()
            try:
                return openreview.api.OpenReviewClient(
                    baseurl=BASE_URLS["v2"], username=username, password=password
                )
            except openreview.OpenReviewException as exc:
                error = exc.args[0] if exc.args and isinstance(exc.args[0], dict) else {}
                if error.get("status") != 429 or attempt == 1:
                    raise
                time.sleep(LOGIN_RETRY_SECONDS)
        raise AssertionError("unreachable")

    def get(self, api: str, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """One GET request (retried on 5xx and short rate-limit waits); returns the raw JSON body."""
        client = self._client(api)
        url = BASE_URLS[api] + endpoint
        for attempt in range(MAX_ATTEMPTS):
            last = attempt == MAX_ATTEMPTS - 1
            self.limiter.wait()
            self.n_requests += 1
            try:
                response = self._http.get(
                    url,
                    params=tools.format_params(params),
                    headers=client.headers,
                    timeout=REQUEST_TIMEOUT,
                )
            except requests.RequestException:
                if last:
                    raise
                time.sleep(10 * (attempt + 1))
                continue

            policy = response.headers.get("ratelimit-policy")
            if policy:
                self.policies[f"{api} {endpoint}"] = policy
            if response.status_code == 200:
                return response.json()
            if response.status_code == 429:
                retry_after = float(response.headers.get("retry-after", 60))
                if retry_after > self.max_rate_limit_wait or last:
                    raise RateLimitExceeded(f"{api} {endpoint}", retry_after, policy)
                time.sleep(retry_after + 1)
                continue
            if response.status_code >= 500 and not last:
                time.sleep(10 * (attempt + 1))
                continue
            try:
                body = response.json()
            except ValueError:
                body = {}
            raise OpenReviewError(
                response.status_code,
                str(body.get("name", "Error")),
                str(body.get("message", response.text[:300])),
            )
        raise AssertionError("unreachable")

    def get_all(
        self,
        api: str,
        endpoint: str,
        key: str,
        params: dict[str, Any],
        max_items: int | None = None,
    ) -> list[dict[str, Any]]:
        """All items of a listing.

        With `max_items`, a single page is requested (caller-defined order).
        Otherwise the listing is walked with an id cursor, PAGE_SIZE items at a time.
        """
        if max_items is not None:
            return self.get(api, endpoint, {**params, "limit": max_items})[key]

        items: list[dict[str, Any]] = []
        after: str | None = None
        while True:
            page_params = {**params, "limit": PAGE_SIZE, "sort": "id"}
            if after is not None:
                page_params["after"] = after
            page = self.get(api, endpoint, page_params)[key]
            items.extend(page)
            if len(page) < PAGE_SIZE:
                return items
            after = page[-1]["id"]


def api_version(session: OpenReviewSession, venue_id: str) -> tuple[str, dict[str, Any]]:
    """Return ("v1" | "v2", venue group JSON).

    Documented rule: read the venue group with the API v2 client; the venue is on
    API v2 if the group has a `domain`, on API v1 otherwise.
    """
    groups = session.get("v2", "/groups", {"id": venue_id})["groups"]
    if not groups:
        raise RuntimeError(f"venue group not found: {venue_id}")
    group = groups[0]
    return ("v2" if group.get("domain") else "v1"), group
