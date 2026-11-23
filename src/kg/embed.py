"""Text embeddings with a cache on disk.

The cache of a model is two arrays: the 64-bit hashes of the texts already encoded
(sorted) and their vectors (float16). A text is never encoded twice, whatever the
node type it belongs to and whatever the run.
"""

import hashlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

Encoder = Callable[[list[str]], np.ndarray]


def text_hash(text: str) -> np.uint64:
    return np.frombuffer(hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest(), dtype=np.uint64)[0]


class EmbeddingCache:
    """Vectors of one model, keyed by the hash of the text."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.keys = np.empty(0, dtype=np.uint64)
        self.vectors: np.ndarray | None = None
        if (directory / "keys.npy").exists():
            self.keys = np.load(directory / "keys.npy")
            self.vectors = np.load(directory / "vectors.npy")

    def lookup(self, hashes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """(position of each hash in the cache, True where the hash is cached)."""
        if not len(self.keys):
            return np.zeros(len(hashes), dtype=np.int64), np.zeros(len(hashes), dtype=bool)
        where = np.minimum(np.searchsorted(self.keys, hashes), len(self.keys) - 1)
        return where, self.keys[where] == hashes

    def add(self, hashes: np.ndarray, vectors: np.ndarray) -> None:
        keys = np.concatenate([self.keys, hashes])
        stacked = vectors if self.vectors is None else np.concatenate([self.vectors, vectors])
        order = np.argsort(keys, kind="stable")
        self.keys, self.vectors = keys[order], stacked[order]
        self.directory.mkdir(parents=True, exist_ok=True)
        np.save(self.directory / "keys.npy", self.keys)
        np.save(self.directory / "vectors.npy", self.vectors)

    def embed(self, texts: list[str], encode: Encoder, save_every: int = 100_000) -> tuple[np.ndarray, int]:
        """(float32 vectors of `texts`, number of texts sent to the model). New vectors
        are saved every `save_every` texts, so that an interrupted run loses little."""
        hashes = np.array([text_hash(text) for text in texts], dtype=np.uint64)
        _, cached = self.lookup(hashes)
        missing, first = np.unique(hashes[~cached], return_index=True)
        new_texts = [texts[i] for i in np.flatnonzero(~cached)[first]]
        for start in range(0, len(missing), save_every):
            batch = slice(start, start + save_every)
            self.add(missing[batch], encode(new_texts[batch]).astype(np.float16))
        where, cached = self.lookup(hashes)
        assert cached.all()
        return self.vectors[where].astype(np.float32), len(missing)


def mean_of_chunks(chunk_vectors: np.ndarray, lengths: list[int]) -> np.ndarray:
    """Mean vector of each item, given the vectors of all chunks in order and the
    number of chunks of each item. An item without chunk gets a zero vector."""
    out = np.zeros((len(lengths), chunk_vectors.shape[1]), dtype=np.float32)
    start = 0
    for index, n in enumerate(lengths):
        if n:
            out[index] = chunk_vectors[start:start + n].mean(axis=0)
        start += n
    return out


def sentence_encoder(settings: dict[str, Any], device: str = "cuda") -> Encoder:
    """Encoder of the sentence-embedding model named in the config (`kg.text_model`)."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(settings["name"], revision=settings["revision"], device=device)
    if device == "cuda":
        model.half()

    def encode(texts: list[str]) -> np.ndarray:
        return model.encode(texts, batch_size=settings["batch_size"], convert_to_numpy=True,
                            normalize_embeddings=False, show_progress_bar=False)

    return encode


def cache_name(model: str, revision: str) -> str:
    return f"{model.replace('/', '--')}@{revision[:12]}"
