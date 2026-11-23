"""Calls to the model server: JSON output of a given schema, hash cache, retries, failure log.

Two backends (`cfg["backend"]`):
- "vllm" (default): the local server; the JSON schema constrains the generation.
- "deepseek": the hosted DeepSeek API. It only guarantees a JSON object: the schema is
  written in the system instruction and every answer is validated against it, an
  invalid one being retried like any other. Requests cost money: the cost of each
  answer is added up from its token counts, the run stops when it reaches
  `budget_usd`, and with `off_peak_only` no request is sent during peak hours. The
  served model version cannot be pinned; the one reported by the server is recorded.

- Temperature 0 and a fixed seed: the same input always gives the same answer.
- Cache: one file per (step, prompt version, model, input). An input already
  processed is never sent again.
- An answer that is not valid is retried, at most twice. Invalid JSON is first retried
  with twice the output budget (a truncated answer is the usual cause). An answer
  that is valid JSON but fails the semantic check is sent back with the error
  message: asking again the same way would give the same answer. After three
  attempts the failure is logged.
- An input that does not fit in the context of the model (refused by the server, or
  accepted with no room left for the answer) raises ContextOverflow: the caller
  shortens the input, there is nothing to retry.
- When the server stops answering (several connection errors in a row), ServerDown
  is raised and every later call fails at once: a long run stops instead of logging
  one failure per remaining item. Answers already computed stay in the cache.
"""

import hashlib
import json
import os
import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema
import requests
from pydantic import BaseModel, ValidationError

from src.collect.store import read_json, write_json

MAX_ATTEMPTS = 3


class ContextOverflow(Exception):
    """The server refused the request: prompt and output budget exceed the model context."""


class ServerDown(Exception):
    """The server no longer answers: the run must stop."""


class BudgetExceeded(ServerDown):
    """The requests of this run have cost the configured budget: the run must stop."""


def is_peak(moment: datetime, hours: list[list[int]]) -> bool:
    """Peak pricing: Monday to Friday, inside one of the [start, end) hours (UTC)."""
    return moment.weekday() < 5 and any(start <= moment.hour < end for start, end in hours)


def http_post(url: str, payload: dict[str, Any], timeout: float, headers: dict[str, str] | None = None) -> dict[str, Any]:
    response = requests.post(url, json=payload, timeout=timeout, headers=headers)
    if response.status_code == 400 and "context length" in response.text.lower():
        raise ContextOverflow(response.text[:300])
    response.raise_for_status()
    return response.json()


class LLMClient:
    def __init__(
        self,
        cfg: dict[str, Any],
        cache_dir: Path,
        failures_path: Path,
        post: Callable[[str, dict[str, Any], float], dict[str, Any]] = http_post,
    ) -> None:
        self.cfg = cfg
        self.cache_dir = cache_dir
        self.failures_path = failures_path
        self.post = post
        self._lock = threading.Lock()
        self.stats = {"calls": 0, "cache_hits": 0, "retries": 0, "failures": 0,
                      "prompt_tokens": 0, "completion_tokens": 0}
        self._connection_errors = 0  # in a row, over all threads
        self.down = False
        self.down_reason = "the server stopped answering"
        self.backend = cfg.get("backend", "vllm")
        self.served: set[str] = set()  # model versions reported by a hosted server
        if self.backend == "deepseek":
            self.stats.update({"prompt_cache_hit_tokens": 0, "cost_usd": 0.0})
            key = os.environ.get(cfg["api_key_env"])
            if not key and post is http_post:
                raise RuntimeError(f"{cfg['api_key_env']} is not set: run with `uv run --env-file .env ...`")
            self._headers = {"Authorization": f"Bearer {key}"}
        elif self.backend != "vllm":
            raise ValueError(f"unknown backend: {self.backend!r}")

    # ----------------------------------------------------------------- cache
    def cache_key(
        self, step: str, prompt_version: str, messages: list[dict[str, str]], json_schema: dict[str, Any]
    ) -> str:
        identity = {
            "step": step,
            "prompt": prompt_version,
            "model": self.cfg["model"],
            "revision": self.cfg["revision"],
            "messages": messages,
            "schema": json_schema,
        }
        return hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()

    def cache_path(self, step: str, key: str) -> Path:
        return self.cache_dir / step / key[:2] / f"{key}.json"

    # ----------------------------------------------------------------- request
    def _request_hosted(self, messages: list[dict[str, str]], json_schema: dict[str, Any], max_tokens: int):
        """DeepSeek: JSON object mode, schema given in the instruction and checked on the answer."""
        cfg = self.cfg
        while cfg["off_peak_only"] and is_peak(datetime.now(timezone.utc), cfg["peak_hours_utc"]):
            time.sleep(60)  # peak prices are twice the off-peak ones: wait
        if self.stats["cost_usd"] >= cfg["budget_usd"]:
            self.down = True
            self.down_reason = f"the requests of this run have cost {self.stats['cost_usd']:.2f} USD (budget {cfg['budget_usd']} USD)"
            raise BudgetExceeded(self.down_reason)
        instruction = ("\n\nAnswer with one JSON object and nothing else. It must be valid against this JSON schema:\n"
                       + json.dumps(json_schema, sort_keys=True))
        chat = [{**messages[0], "content": messages[0]["content"] + instruction}, *messages[1:]]
        payload = {"model": cfg["model"], "messages": chat, "temperature": cfg["temperature"], "max_tokens": max_tokens,
                   "response_format": {"type": "json_object"}, "thinking": {"type": "disabled"}}
        body = self.post(f"{cfg['base_url']}/chat/completions", payload, cfg["timeout_seconds"], self._headers)
        choice, usage = body["choices"][0], body.get("usage") or {}
        hit = usage.get("prompt_cache_hit_tokens", 0)
        miss = usage.get("prompt_cache_miss_tokens", usage.get("prompt_tokens", 0) - hit)
        prices = cfg["prices"]["peak" if is_peak(datetime.now(timezone.utc), cfg["peak_hours_utc"]) else "off_peak"]
        cost = (hit * prices["input_cache_hit"] + miss * prices["input_cache_miss"]
                + usage.get("completion_tokens", 0) * prices["output"]) / 1e6
        self._count(prompt_cache_hit_tokens=hit, cost_usd=cost)
        with self._lock:
            self.served.add(f"{body.get('model')} {body.get('system_fingerprint')}")
        return choice["message"]["content"] or "", usage

    def _request(self, messages: list[dict[str, str]], name: str, json_schema: dict[str, Any], max_tokens: int):
        if self.backend == "deepseek":
            return self._request_hosted(messages, json_schema, max_tokens)
        payload = {
            "model": self.cfg["model"],
            "messages": messages,
            "temperature": self.cfg["temperature"],
            "seed": self.cfg["seed"],
            "max_tokens": max_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": name, "schema": json_schema, "strict": True},
            },
            # Qwen3: answer directly, without a reasoning block.
            "chat_template_kwargs": {"enable_thinking": False},
        }
        body = self.post(f"{self.cfg['base_url']}/chat/completions", payload, self.cfg["timeout_seconds"])
        choice, usage = body["choices"][0], body.get("usage") or {}
        # A prompt that nearly fills the context is accepted, but the answer is cut when the
        # context is full: a larger output budget would not help, the input must be shortened.
        if choice.get("finish_reason") == "length" and usage.get("total_tokens", 0) >= self.cfg["max_model_len"]:
            raise ContextOverflow("the context of the model was full before the end of the answer")
        return choice["message"]["content"], usage

    def complete(
        self,
        step: str,
        prompt_version: str,
        messages: list[dict[str, str]],
        schema: type[BaseModel],
        check: Callable[[Any], None],
        item_id: str,
        json_schema: dict[str, Any] | None = None,
    ) -> BaseModel | None:
        """Validated answer, from the cache or the server; None after MAX_ATTEMPTS failures.

        `json_schema` constrains the generation; by default it is the schema of the
        pydantic model, a tighter one (exact number of entries) can be given.
        """
        json_schema = json_schema or schema.model_json_schema()
        key = self.cache_key(step, prompt_version, messages, json_schema)
        path = self.cache_path(step, key)
        if path.exists():
            self._count(cache_hits=1)
            return schema.model_validate(read_json(path)["output"])

        max_tokens = self.cfg["max_tokens"][step]
        attempt_messages = list(messages)
        error, content = "", ""
        for attempt in range(1, MAX_ATTEMPTS + 1):
            if self.down:
                raise ServerDown(self.down_reason)
            started = time.monotonic()
            try:
                content, usage = self._request(attempt_messages, schema.__name__, json_schema, max_tokens)
                self._connection(ok=True)
                self._count(calls=1, prompt_tokens=usage.get("prompt_tokens", 0),
                            completion_tokens=usage.get("completion_tokens", 0))
                if self.backend == "deepseek":  # what guided decoding enforces on the local server
                    jsonschema.validate(json.loads(content), json_schema)
                answer = schema.model_validate_json(content)
                check(answer)
            except BudgetExceeded:
                raise
            except (ValueError, KeyError, requests.RequestException, jsonschema.ValidationError) as exc:
                # pydantic's ValidationError and json's decoding error are ValueErrors
                error = f"{type(exc).__name__}: {str(exc)[:500]}"
                if isinstance(exc, (requests.ConnectionError, requests.Timeout)):
                    self._connection(ok=False)  # raises ServerDown after too many in a row
                    time.sleep(self.cfg["retry_wait_seconds"])
                elif isinstance(exc, requests.RequestException):
                    time.sleep(self.cfg["retry_wait_seconds"])  # HTTP error of a hosted server (429, 5xx)
                if attempt == MAX_ATTEMPTS:
                    break
                self._count(retries=1)
                # not JSON, or not of the schema: usually a truncated answer
                malformed = isinstance(exc, (ValidationError, json.JSONDecodeError))
                if isinstance(exc, (KeyError, requests.RequestException)) or (malformed and attempt == 1):
                    max_tokens *= 2 if malformed else 1
                else:
                    attempt_messages = messages + [
                        {"role": "assistant", "content": content},
                        {"role": "user", "content": f"Your answer was rejected: {error}\nAnswer again with valid JSON."},
                    ]
                continue
            write_json(path, {
                "item_id": item_id, "step": step, "prompt": prompt_version, "model": self.cfg["model"],
                "attempts": attempt, "seconds": round(time.monotonic() - started, 3),
                "usage": usage, "output": answer.model_dump(),
            })
            return answer

        self.log_failure(item_id, step, prompt_version, error, key, content)
        return None

    def log_failure(self, item_id: str, step: str, prompt_version: str, error: str,
                    key: str = "", last_output: str = "") -> None:
        """Count a failure and append it to the failure log."""
        self._count(failures=1)
        record = {"item_id": item_id, "step": step, "prompt": prompt_version, "key": key,
                  "error": error, "last_output": last_output[:2000]}
        with self._lock:
            self.failures_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.failures_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _connection(self, ok: bool) -> None:
        with self._lock:
            self._connection_errors = 0 if ok else self._connection_errors + 1
            if self._connection_errors >= self.cfg["max_connection_errors"]:
                self.down = True
        if self.down:
            raise ServerDown(f"{self._connection_errors} connection errors in a row")

    def _count(self, **increments: int) -> None:
        with self._lock:
            for name, value in increments.items():
                self.stats[name] += value
