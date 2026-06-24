"""CLI wiring smoke tests (offline: status + seed --html)."""
import json

from sadhana_setu.corpus import cli

LISTING = (
    '<a href="/audio/japa-and-the-holy-name.mp3">Japa and the Holy Name</a>'
    '<a href="/audio/gita-class.mp3">Gītā Class</a>'
)


def test_status_json(cfg, manifest, capsys):
    rc = cli.main(["--manifest", str(cfg.manifest_path), "status", "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["grand_total"] == 0
    assert {s["id"] for s in out["sets"]} == {"bhurijana-prabhu", "holy-name-seminar"}


def test_seed_from_html_then_status(cfg, manifest, tmp_path, capsys):
    listing = tmp_path / "listing.html"
    listing.write_text(LISTING, encoding="utf-8")
    rc = cli.main(["--manifest", str(cfg.manifest_path), "--set", "bhurijana-prabhu",
                   "seed", "--html", str(listing), "--url", "https://site.test/"])
    assert rc == 0
    capsys.readouterr()  # drain the seed command's stdout
    # Speaker set: only the Holy-Name/japa lecture passes the topic filter.
    rc = cli.main(["--manifest", str(cfg.manifest_path), "--set", "bhurijana-prabhu",
                   "status", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert out["sets"][0]["counts"]["pending"] == 1
