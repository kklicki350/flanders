"""GUI smoke tests over a real (fake-tool) run."""

import pytest
from django.test import Client


@pytest.fixture
def finished_run(env, settings, monkeypatch):
    from flanders.engine import pipeline
    from flanders.web.runs import views

    ws, cfg_dir = env
    monkeypatch.setattr(views, "WS", ws)
    ctx = pipeline.prepare(cfg_dir / "run.yaml", [], None, 2, ws)
    assert pipeline.execute(ctx) == 0
    return ctx


@pytest.mark.django_db(transaction=True)
def test_pages(finished_run):
    c = Client()
    rid = finished_run.run_id
    r = c.get("/")
    assert r.status_code == 302 and rid in r["Location"]
    r = c.get(f"/runs/{rid}/")
    body = r.content.decode()
    assert r.status_code == 200
    assert "GCF_000000001.1" in body and "2</b> genomes analyzed of 3" in body
    assert "signal_peptide · 2/2 genomes significant" in body
    assert "not a cross-genome test" in body
    r = c.get(f"/runs/{rid}/?feature=signal_peptide", HTTP_HX_REQUEST="true")
    assert r.status_code == 200 and "<html" not in r.content.decode()
    r = c.get(f"/runs/{rid}/genomes/GCF_000000001.1/?location=upstream&feature=signal_peptide")
    body = r.content.decode()
    assert r.status_code == 200 and "<svg" in body and "selected" in body and "transmembrane" in body
    r = c.get(f"/runs/{rid}/genomes/GCF_000000001.1/upstream/provenance/")
    assert r.status_code == 200 and "deepsig" in r.content.decode()
    assert c.get(f"/runs/{rid}/config.yaml").status_code == 200
    assert c.get("/runs/").status_code == 200
    assert c.get(f"/runs/{rid}/ledger/?panel=1").status_code == 200
    assert c.get("/compose/").status_code == 200
    assert c.get("/runs/nope/").status_code == 404


@pytest.mark.django_db(transaction=True)
def test_compose_review(env, monkeypatch):
    from django.core.files.uploadedfile import SimpleUploadedFile

    from flanders.web.runs import views

    ws, _ = env
    monkeypatch.setattr(views, "WS", ws)
    c = Client()
    r = c.post("/compose/", {"name": "t1", "search": "snapshot", "genomes": "GCF_000000001.1",
                             "features": ["signal_peptide"], "tests": ["binomial"], "flank_orfs": "4",
                             "cb_extra": "entrez_query=Cyanobacteria[orgn]", "action": "review",
                             "query": SimpleUploadedFile("q.faa", b">Q1\nMKK\n")})
    body = r.content.decode()
    assert r.status_code == 200, body
    assert "flanders run -c" in body and "entrez_query" in body
    assert (ws.root / "drafts" / "t1" / "query.faa").exists()
