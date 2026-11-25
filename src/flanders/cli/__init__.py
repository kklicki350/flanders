"""The `flanders` command. Only this module turns exceptions into exit codes."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import typer

from flanders import CITATION, __version__
from flanders.errors import FlandersError

app = typer.Typer(no_args_is_help=True, add_completion=True, pretty_exceptions_enable=False,
                  help="FLANDERS: enrichment analysis of biosynthetic gene cluster neighborhoods.")
reference_app = typer.Typer(no_args_is_help=True, help="Download and verify reference data.")
tools_app = typer.Typer(no_args_is_help=True, help="Signal-peptide and transmembrane predictors.")
workspace_app = typer.Typer(no_args_is_help=True, help="Workspace maintenance.")
dev_app = typer.Typer(no_args_is_help=True, hidden=True)
app.add_typer(reference_app, name="reference")
app.add_typer(tools_app, name="tools")
app.add_typer(workspace_app, name="workspace")
app.add_typer(dev_app, name="dev")


def _setup():
    from flanders.workspace import bootstrap

    bootstrap.setup()
    from flanders.workspace.layout import Workspace

    return Workspace.default()


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


@app.command()
def version() -> None:
    """Print the FLANDERS version."""
    print(__version__)


@app.command()
def run(
    config: Annotated[Path, typer.Option("--config", "-c", help="Run-configuration YAML file.")],
    set_: Annotated[list[str], typer.Option("--set", "-s", help="Override a config value: key.sub=value")] = [],  # noqa: B006
    name: Annotated[str | None, typer.Option(help="Run name shown in run history.")] = None,
    jobs: Annotated[int | None, typer.Option("--jobs", "-j", help="Parallel tasks (default: CPUs - 1).")] = None,
    out: Annotated[Path | None, typer.Option(help="Also copy final FCERs and report.json here.")] = None,
    json_out: Annotated[bool, typer.Option("--json", help="Print a JSON summary on stdout.")] = False,
) -> None:
    """Run the full pipeline headless. Never prompts; exit codes are documented."""
    ws = _setup()
    from flanders.engine import pipeline

    pipeline.recover_stale(ws)
    ctx = pipeline.prepare(config, set_, name, jobs, ws)
    _err(f"Run {ctx.run_id} -> {ctx.paths.root}")
    code = pipeline.execute(ctx, out_dir=out)
    _finish(ctx.paths.root, code, json_out)


@app.command()
def resume(run_id: str, jobs: Annotated[int | None, typer.Option("--jobs", "-j")] = None,
           json_out: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Resume an interrupted or cancelled run; completed tasks are not repeated."""
    ws = _setup()
    from flanders.engine import pipeline

    pipeline.recover_stale(ws)
    ctx = pipeline.load_existing(run_id, ws, jobs)
    code = pipeline.execute(ctx)
    _finish(ctx.paths.root, code, json_out)


def _finish(run_dir: Path, code: int, json_out: bool) -> None:
    report = json.loads((run_dir / "report.json").read_text())
    if json_out:
        print(json.dumps({"run_dir": str(run_dir), **report}))
    else:
        print(run_dir / "fcer")
        _err(f"{report['status']}: {report['fcer_count']} FCER(s); "
             f"{len(report['failed'])} failed, {len(report['excluded'])} excluded (see report.json)")
    _err(CITATION)
    raise typer.Exit(code)


@app.command()
def runs() -> None:
    """List runs in the workspace."""
    _setup()
    from flanders.workspace.models import Run

    for r in Run.objects.all():
        print(f"{r.run_id}  {r.status:24} {r.kind:12} {r.name}")


@app.command()
def status(run_id: str) -> None:
    """Per-genome task status of a run."""
    _setup()
    from flanders.workspace.models import Run

    run = Run.objects.get(pk=run_id)
    print(f"{run.run_id} {run.status} stage={run.stage or '-'} {run.message}")
    for t in run.tasks.order_by("tag", "id"):
        extra = f"  {t.reason}: {t.detail[:120]}" if t.status == "failed" else ""
        print(f"  {t.stage:18} {t.tag:20} {t.status}{extra}")


@app.command()
def gui(port: Annotated[int, typer.Option(help="Port on 127.0.0.1.")] = 8765,
        no_browser: Annotated[bool, typer.Option("--no-browser")] = False) -> None:
    """Start the local GUI (loopback only)."""
    ws = _setup()
    import os

    from django.core.management import call_command

    from flanders.engine import pipeline

    pipeline.recover_stale(ws)
    host = "0.0.0.0" if os.environ.get("FLANDERS_IN_CONTAINER") == "1" else "127.0.0.1"  # noqa: S104
    url = f"http://127.0.0.1:{port}/"
    _err(f"FLANDERS GUI at {url}  (Ctrl-C to stop)")
    if not no_browser and os.environ.get("FLANDERS_IN_CONTAINER") != "1":
        import webbrowser

        webbrowser.open(url)
    call_command("runserver", f"{host}:{port}", use_reloader=False, use_threading=True)


@reference_app.command("fetch")
def reference_fetch(
    only: Annotated[str | None, typer.Option(help="pfam or antismash")] = None,
    missing_only: Annotated[bool, typer.Option("--missing-only", help="Skip components already present.")] = False,
) -> None:
    """Download reference data (Pfam-A, antiSMASH databases) into the workspace."""
    ws = _setup()
    from flanders.reference import data

    ref = data.for_workspace(ws.reference)
    have = ref.manifest().get("components", {}) if missing_only else {}
    if only in (None, "pfam") and "pfam" not in have:
        data.fetch_pfam(ref, log=_err)
    if only in (None, "antismash") and "antismash8" not in have:
        data.fetch_antismash(ref, log=_err)
    _err(f"Reference data ready in {ref.root}")


@reference_app.command("verify")
def reference_verify() -> None:
    """Recompute every reference-data checksum."""
    ws = _setup()
    from flanders.reference import data

    problems = data.verify(data.for_workspace(ws.reference))
    for p in problems:
        _err(p)
    if problems:
        raise typer.Exit(6)
    _err("reference data verified")


@tools_app.command("status")
def tools_status() -> None:
    """Show which predictors are installed and which the fallback chain will use."""
    ws = _setup()
    from flanders.adapters import predictors as preds

    found = preds.detect(ws.tools)
    for name in ("signalp6", "signalp5", "deepsig", "phobius", "tmhmm"):
        p = found.get(name)
        print(f"{name:9} {'installed ' + p.version if p else 'not installed'}")
    sp, tm = preds.choose(preds.SIGNAL_CHAIN, found), preds.choose(preds.TM_CHAIN, found)
    print(f"\nsignal peptide -> {sp.label if sp else 'none'}")
    print(f"transmembrane  -> {tm.label if tm else 'none (install TMHMM 2.0c or Phobius)'}")
    print(f"\nRestricted predictors go in {ws.tools}/<name>/bin/ (signalp6, signalp5, tmhmm, phobius).")


@workspace_app.command("init")
def workspace_init() -> None:
    """Create the workspace folders and database."""
    ws = _setup()
    print(ws.root)


@workspace_app.command("reindex")
def workspace_reindex() -> None:
    """Rebuild run history and the FCER index from workspace files."""
    ws = _setup()
    from flanders.workspace.index import reindex

    _err(f"reindexed {reindex(ws)} run(s)")


@dev_app.command("gen-schema")
def gen_schema(root: Path = Path(".")) -> None:
    from flanders.fcer.schema import write_schema

    print(write_schema(root))


def run_cli() -> None:
    try:
        app()
    except FlandersError as exc:
        _err(f"error: {exc}")
        sys.exit(exc.exit_code)
