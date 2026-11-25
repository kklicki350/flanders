"""Read annotated CDS from GenBank flat files (the adapter boundary for Biopython)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from flanders.genomics import coords
from flanders.genomics.models import Orf


def gc_fraction(seq: str) -> float:
    seq = seq.upper()
    acgt = sum(seq.count(b) for b in "ACGT")
    if acgt == 0:
        return 0.0
    return (seq.count("G") + seq.count("C")) / acgt


def iter_orfs(path: Path) -> Iterator[tuple[Orf, str]]:
    """Yield (Orf, protein sequence) for every translated CDS, in file order."""
    from Bio import SeqIO

    opener = _open(path)
    with opener as handle:
        for rec in SeqIO.parse(handle, "genbank"):
            record_acc = rec.id if "." in rec.id else f"{rec.id}.{rec.annotations.get('sequence_version', 1)}"
            for feat in rec.features:
                if feat.type != "CDS" or "pseudo" in feat.qualifiers:
                    continue
                translation = feat.qualifiers.get("translation", [None])[0]
                if not translation:
                    continue
                loc = feat.location
                start, end = coords.from_zero_based(int(loc.start), int(loc.end))
                protein_id = feat.qualifiers.get("protein_id", [None])[0]
                locus_tag = feat.qualifiers.get("locus_tag", [None])[0]
                orf_id = protein_id or f"{record_acc}:{locus_tag or f'{start}-{end}'}"
                try:
                    nt = str(feat.extract(rec.seq))
                except Exception:  # noqa: BLE001 - sequence may be absent (CON records)
                    nt = ""
                yield (
                    Orf(
                        orf_id=orf_id,
                        record=record_acc,
                        start=start,
                        end=end,
                        strand=coords.strand_symbol(loc.strand),
                        locus_tag=locus_tag,
                        product=feat.qualifiers.get("product", [None])[0],
                        length_aa=len(translation),
                        gc=gc_fraction(nt),
                    ),
                    translation,
                )


def organism_name(path: Path) -> str | None:
    from Bio import SeqIO

    with _open(path) as handle:
        for rec in SeqIO.parse(handle, "genbank"):
            return rec.annotations.get("organism")
    return None


def _open(path: Path):
    if path.suffix == ".gz":
        import gzip

        return gzip.open(path, "rt")
    return open(path)
