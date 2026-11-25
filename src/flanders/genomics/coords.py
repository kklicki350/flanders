"""The only place coordinate systems are converted.

FLANDERS uses 1-based inclusive coordinates with strand "+"/"-" everywhere outside
tool adapters. Biopython, BED and Python slicing use 0-based half-open.
"""

from __future__ import annotations


def from_zero_based(start: int, end: int) -> tuple[int, int]:
    """0-based half-open [start, end) -> 1-based inclusive [start, end]."""
    if end <= start:
        raise ValueError(f"empty or inverted interval [{start}, {end})")
    return start + 1, end


def to_zero_based(start: int, end: int) -> tuple[int, int]:
    """1-based inclusive [start, end] -> 0-based half-open [start, end)."""
    if end < start:
        raise ValueError(f"inverted interval [{start}, {end}]")
    return start - 1, end


def length(start: int, end: int) -> int:
    return end - start + 1


def overlaps(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return a_start <= b_end and b_start <= a_end


def strand_symbol(value: int | str | None) -> str:
    if value in (1, "+", "1"):
        return "+"
    if value in (-1, "-", "-1"):
        return "-"
    raise ValueError(f"located feature has no strand: {value!r}")
