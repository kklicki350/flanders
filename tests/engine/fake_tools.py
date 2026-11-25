"""Stand-in executables for the external tools, so the engine can be tested end to end.

The fake genomes: each has 60 CDS on one record. ORFs 30-33 are the query cluster.
Upstream ORFs 26-29 carry signal peptides (and so does every 25th background ORF).
"""

from __future__ import annotations

import json
import stat
import sys
import textwrap
from pathlib import Path

GENOMES = {
    "GCF_000000001.1": ("NC_900001.1", "Fakeus primus"),
    "GCF_000000002.1": ("NC_900002.1", "Fakeus secundus"),
    "GCF_000000003.1": ("NC_900003.1", "Fakeus nohitus"),  # no cluster
}
N_ORF = 60
SEED = range(30, 34)
SP_UPSTREAM = range(26, 30)


def protein_id(record: str, i: int) -> str:
    return f"WP_{record[3:9]}{i:03d}.1"


def write_genbank(path: Path, record: str, organism: str) -> None:
    import numpy as np
    from Bio.Seq import Seq
    from Bio.SeqFeature import FeatureLocation, SeqFeature
    from Bio.SeqIO import write
    from Bio.SeqRecord import SeqRecord

    rng = np.random.Generator(np.random.PCG64(int(record[3:9])))
    gene_len = 300
    seq = "".join(rng.choice(list("ACGT"), size=N_ORF * (gene_len + 60)))
    rec = SeqRecord(Seq(seq), id=record, name=record.split(".")[0], description=organism,
                    annotations={"molecule_type": "DNA", "organism": organism})
    for i in range(N_ORF):
        start = i * (gene_len + 60)
        aa = "M" + "".join(rng.choice(list("ACDEFGHIKLMNPQRSTVWY"), size=gene_len // 3 - 1))
        rec.features.append(SeqFeature(FeatureLocation(start, start + gene_len, strand=1), type="CDS",
                                       qualifiers={"protein_id": [protein_id(record, i)],
                                                   "locus_tag": [f"FK{i:04d}"], "product": [f"protein {i}"],
                                                   "translation": [aa]}))
    write(rec, path, "genbank")


SCRIPTS = {
    "datasets": r'''
        import sys, zipfile, os, pathlib
        args = sys.argv[1:]
        if args[:1] == ["--version"]:
            print("datasets version: 18.41.1"); sys.exit(0)
        acc = args[args.index("accession") + 1]
        out = args[args.index("--filename") + 1]
        src = pathlib.Path(os.environ["FAKE_GENOMES"]) / f"{acc}.gbff"
        with zipfile.ZipFile(out, "w") as z:
            z.write(src, f"ncbi_dataset/data/{acc}/genomic.gbff")
    ''',
    "cblaster": r'''
        import sys, json, os, pathlib
        args = sys.argv[1:]
        if args[:1] == ["--version"]:
            print("cblaster 1.4.2"); sys.exit(0)
        if args[0] == "config":
            sys.exit(0)
        if args[0] == "makedb":
            name = args[args.index("--name") + 1]
            pathlib.Path(f"{name}.dmnd").write_text("db"); pathlib.Path(f"{name}.sqlite3").write_text("db")
            sys.exit(0)
        if "--bogus_flag" in args:
            print("cblaster search: error: unrecognized arguments: --bogus_flag", file=sys.stderr); sys.exit(2)
        session = args[args.index("--session_file") + 1]
        pathlib.Path(session).write_text(pathlib.Path(os.environ["FAKE_SESSION"]).read_text())
    ''',
    "deepsig": r'''
        import sys, os
        args = sys.argv[1:]
        if args[:1] == ["--version"]:
            print("DeepSig 1.2.5"); sys.exit(0)
        fasta, out = args[args.index("-f") + 1], args[args.index("-o") + 1]
        sp = set(open(os.environ["FAKE_SP"]).read().split())
        with open(out, "w") as fh:
            for line in open(fasta):
                if line.startswith(">"):
                    pid = line[1:].split()[0]
                    kind = "Signal peptide" if pid in sp else "Chain"
                    fh.write(f"{pid}\tDeepSig\t{kind}\t1\t25\t0.9\t.\t.\t.\n")
    ''',
    "hmmsearch": r'''
        import sys, os
        args = sys.argv[1:]
        if args[:1] == ["-h"]:
            print("# hmmsearch :: search profile(s) against a sequence database\n# HMMER 3.4 (Aug 2023); http://hmmer.org/"); sys.exit(0)
        domtbl = args[args.index("--domtblout") + 1]
        hits = [l.split() for l in open(os.environ["FAKE_PFAM"]).read().splitlines() if l.strip()]
        with open(domtbl, "w") as fh:
            fh.write("# target name accession tlen query name accession qlen ...\n")
            for pid, pf in hits:
                cols = [pid, "-", "100", "ABC_tran", pf + ".30", "137"] + ["1"] * 16 + ["ABC", "transporter"]
                fh.write(" ".join(cols) + "\n")
    ''',
    "mmseqs": r'''
        import sys
        args = sys.argv[1:]
        if args[:1] == ["version"]:
            print("17.b804f"); sys.exit(0)
        fasta, prefix = args[1], args[2]
        ids = [l[1:].split()[0] for l in open(fasta) if l.startswith(">")]
        with open(prefix + "_cluster.tsv", "w") as fh:
            for i, pid in enumerate(ids):
                rep = ids[i - 1] if i % 10 == 1 and i < 25 else pid  # a few paralog pairs, not near the seed
                fh.write(f"{rep}\t{pid}\n")
    ''',
    "antismash": r'''
        import sys, json, pathlib
        args = sys.argv[1:]
        if args[:1] == ["--version"]:
            print("antiSMASH 8.0.4"); sys.exit(0)
        out = pathlib.Path(args[args.index("--output-dir") + 1]); out.mkdir(parents=True, exist_ok=True)
        gbff = args[-1]
        rec = open(gbff).readline().split()[1]
        record = next(l.split()[1] for l in open(gbff) if l.startswith("VERSION"))
        data = {"records": [{"id": record, "features": [
            {"type": "region", "location": "[10800:12300](+)", "qualifiers": {"product": ["NRPS"]}}]}]}
        (out / "genome.json").write_text(json.dumps(data))
    ''',
}


def install(bin_dir: Path, data_dir: Path) -> dict[str, str]:
    bin_dir.mkdir(parents=True, exist_ok=True)
    for name, body in SCRIPTS.items():
        p = bin_dir / name
        p.write_text(f"#!{sys.executable}\n" + textwrap.dedent(body))
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
    data_dir.mkdir(parents=True, exist_ok=True)
    sp, pfam = [], []
    organisms = []
    for acc, (record, organism) in GENOMES.items():
        write_genbank(data_dir / f"{acc}.gbff", record, organism)
        for i in range(N_ORF):
            pid = protein_id(record, i)
            if i in SP_UPSTREAM or i % 25 == 0:
                sp.append(pid)
            if i in SEED:
                pfam.append(f"{pid} PF00005")
        if acc != "GCF_000000003.1":
            subjects = [{"name": protein_id(record, i), "start": i * 360 + 1, "end": i * 360 + 300,
                         "strand": 1, "ipg": None, "hits": [{"query": f"Q{i - 29}"}]} for i in SEED]
            organisms.append({"name": organism, "strain": "", "scaffolds": [{
                "accession": record, "subjects": subjects,
                "clusters": [{"indices": [0, 1, 2, 3], "score": 4.0, "start": 30 * 360 + 1,
                              "end": 33 * 360 + 300, "number": 1}]}]})
    (data_dir / "session.json").write_text(json.dumps({"queries": [], "params": {}, "organisms": organisms}))
    (data_dir / "sp.txt").write_text("\n".join(sp))
    (data_dir / "pfam.txt").write_text("\n".join(pfam))
    return {"FAKE_GENOMES": str(data_dir), "FAKE_SESSION": str(data_dir / "session.json"),
            "FAKE_SP": str(data_dir / "sp.txt"), "FAKE_PFAM": str(data_dir / "pfam.txt")}
