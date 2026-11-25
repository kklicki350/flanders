# FLANDERS

**Functional Landscape And Neighbor Determining gEnomic Region Search** — enrichment
analysis of biosynthetic gene cluster (BGC) neighborhoods. FLANDERS finds a query gene
cluster across a set of genomes with cblaster, annotates each genome with antiSMASH,
predicts per-ORF features (signal peptides, transmembrane helices, Pfam domains), and
tests whether features are enriched in the cluster's flanks against a paralog-collapsed
genome background. Every result is a versioned **FCER** (FLANDERS Cluster Enrichment
Record) per genome × location, with full provenance.

> Status: MVP (pre-release). Planning documents live in `docs/planning/`.

## Install (Docker)

FLANDERS runs inside one Docker image that carries every tool. Until the image is
published, build it locally:

```bash
docker build -f docker/Dockerfile -t flanders:dev .
FLANDERS_IMAGE=flanders:dev ./install-flanders.sh
```

The installer puts a `flanders` command on your PATH (it runs the image for you — you never
type Docker flags), creates the workspace at `~/flanders/`, and offers to download the
reference data (Pfam-A and antiSMASH databases, several GB):

```bash
flanders reference fetch
flanders tools status
```

**Predictors.** DeepSig ships in the image. SignalP 6, SignalP 5, TMHMM 2.0c (DTU,
academic licence) and Phobius cannot be redistributed; obtain them yourself and unpack each
into `~/flanders/tools/<signalp6|signalp5|tmhmm|phobius>/` with its program in `bin/`.
Signal peptides use SignalP 6 → SignalP 5 → DeepSig → Phobius, whichever is installed.
Transmembrane topology needs TMHMM 2.0c or Phobius; without one it is reported as not tested.

## Run

```yaml
# run.yaml
name: ebo-cyanobacteria
query: ebo_cluster.faa        # protein FASTA of the query cluster
genomes: genomes.txt          # assembly accession.version, one per line (search: snapshot)
search: snapshot              # snapshot (reproducible, default) | remote (live NCBI)
flank_orfs: 4
features: [signal_peptide, transmembrane, pfam, antismash]
organism_group: gram-negative
statistics:
  tests: [binomial, permutation]
  correction: bh              # bh | bonferroni | none
  threshold: 0.05
  background: paralog_collapsed
cblaster:                     # passed through to cblaster verbatim
  min_identity: 30
antismash:                    # passed through to antiSMASH verbatim
  taxon: bacteria
```

```bash
flanders run -c run.yaml                 # headless; prints the FCER folder on stdout
flanders run -c run.yaml --set flank_orfs=8 --out results/   # override + copy FCERs out
flanders status <run_id>                 # per-genome task status
flanders resume <run_id>                 # after an interruption; completed tasks are kept
flanders gui                             # http://127.0.0.1:8765/
```

Exit codes: `0` success · `1` completed with per-genome failures · `2` invalid configuration
· `3` a dependency rejected its parameters · `4` upstream output format not recognized ·
`5` another run is active · `6` reference data missing · `130` cancelled.

Outputs per run (`~/flanders/runs/<run_id>/`): `fcer/<genome>.<location>.json|csv`,
`report.json` (every failed or excluded genome with its reason), `inputs/` (copies of your
inputs), `invocations.jsonl` (every tool command, verbatim), `logs/`.

## Develop

```bash
uv sync
uv run pytest            # unit tests + end-to-end engine test with stand-in tools
uv run ruff check src tests && uv run lint-imports
uv run flanders dev gen-schema   # regenerate schemas/fcer/1.0/fcer.schema.json
```

License: MIT.
