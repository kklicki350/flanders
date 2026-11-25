"""FLANDERS: Functional Landscape And Neighbor Determining gEnomic Region Search."""

__version__ = "0.1.0.dev0"

CITATION = (
    "If you used FLANDERS, cite: Klicki K. FLANDERS: reproducible enrichment analysis of "
    "biosynthetic gene cluster neighborhoods (2026). https://github.com/kklicki350/flanders"
)


def main() -> None:
    from flanders.cli import run_cli

    run_cli()
