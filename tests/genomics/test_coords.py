import pytest

from flanders.genomics import accessions, coords


def test_round_trip():
    assert coords.from_zero_based(1000, 1500) == (1001, 1500)
    assert coords.to_zero_based(1001, 1500) == (1000, 1500)
    assert coords.length(1001, 1500) == 500


def test_slice_keeps_last_base():
    seq = "ACGTACGTAC"
    s, e = coords.to_zero_based(3, 6)  # bases 3..6 inclusive = "GTAC"
    assert seq[s:e] == "GTAC"


def test_strand():
    assert coords.strand_symbol(1) == "+"
    assert coords.strand_symbol(-1) == "-"
    with pytest.raises(ValueError):
        coords.strand_symbol(None)


def test_accessions():
    assert accessions.is_versioned("CP002198.1")
    assert accessions.is_versioned("WP_012345678.1")
    assert not accessions.is_versioned("AOGW02000018")
    assert accessions.is_assembly("GCF_000011345.1")
    with pytest.raises(ValueError):
        accessions.require_assembly("GCF_000011345")
