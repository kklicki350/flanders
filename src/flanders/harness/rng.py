"""Seeded randomness. Every random operation takes an explicit Generator."""

from __future__ import annotations

import hashlib

import numpy as np


def child(seed: int, label: str) -> np.random.Generator:
    """A reproducible Generator for (run seed, label), independent of call order."""
    digest = hashlib.sha256(f"{seed}:{label}".encode()).digest()
    return np.random.Generator(np.random.PCG64(int.from_bytes(digest[:16], "big")))
