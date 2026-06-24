"""Command-line entry point for the corpus pipeline.

    python -m sadhana_setu.corpus <seed|fetch|transcribe|status|verify> [options]

See ``specs/001-corpus-pipeline/contracts/cli.md`` for the full contract, including
exit codes: 0 success, 1 provenance error, 2 source/terms error, 3 tool missing.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

import httpx

from sadhana_setu.corpus import fetch as fetch_mod
from sadhana_setu.corpus import sets as sets_mod
from sadhana_setu.corpus import transcribe as transcribe_mod
from sadhana_setu.corpus import verify as verify_mod
from sadhana_setu.corpus import seed as seed_mod
from sadhana_setu.corpus.config import CorpusConfig, ToolMissingError
from sadhana_setu.corpus.manifest import Manifest, ProvenanceError

EXIT_OK = 0
EXIT_PROVENANCE = 1
EXIT_SOURCE = 2
EXIT_TOOL = 3


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    # Globals use SUPPRESS so a value given before the subcommand is not clobbered
    # by the subparser default; backfill the absent ones here.
    args.manifest = getattr(args, "manifest", None)
    args.set = getattr(args, "set", None)
    args.cache = getattr(args, "cache", None)
    args.json = getattr(args, "json", False)
    cfg = _config(args)
    try:
        return args.func(args, cfg)
    except ToolMissingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_TOOL
    except ProvenanceError as exc:
        print(f"provenance error: {exc}", file=sys.stderr)
        return EXIT_PROVENANCE


# --- commands -----------------------------------------------------------

def _cmd_seed(args, cfg: CorpusConfig) -> int:
    manifest = Manifest.load(cfg.manifest_path)
    if args.html:
        html = Path(args.html).read_text(encoding="utf-8")
        base = args.url or ""
    elif args.url:
        html = httpx.get(args.url, headers={"User-Agent": cfg.user_agent},
                         follow_redirects=True, timeout=60.0).text
        base = args.url
    else:
        print("error: seed requires --url or --html", file=sys.stderr)
        return EXIT_SOURCE
    entries = seed_mod.parse_listing(html, base)
    added = seed_mod.seed_set(manifest, args.set, entries, language=args.language)
    if manifest.manifest_status == "stub":
        manifest.manifest_status = "active"
    manifest.save()
    print(f"seed: +{len(added)} lecture(s) into '{args.set}' "
          f"(from {len(entries)} listed)")
    return EXIT_OK


def _cmd_fetch(args, cfg: CorpusConfig) -> int:
    cfg.preflight(require_model=False)
    manifest = Manifest.load(cfg.manifest_path)
    result = fetch_mod.fetch_set(cfg, manifest, args.set)
    manifest.save()
    payload = {k: getattr(result, k) for k in
               ("fetched", "deferred", "unavailable", "excluded", "skipped")}
    _emit(args, payload,
          "fetch: " + ", ".join(f"{k}={len(v)}" for k, v in payload.items()))
    return EXIT_OK


def _cmd_transcribe(args, cfg: CorpusConfig) -> int:
    cfg.preflight(require_model=True)
    manifest = Manifest.load(cfg.manifest_path)
    result = transcribe_mod.transcribe_set(cfg, manifest, args.set,
                                           retranscribe=args.retranscribe)
    manifest.save()
    payload = {"transcribed": result.transcribed, "skipped": result.skipped,
               "quarantined": result.quarantined}
    _emit(args, payload,
          "transcribe: " + ", ".join(f"{k}={len(v)}" for k, v in payload.items()))
    return EXIT_OK


def _cmd_status(args, cfg: CorpusConfig) -> int:
    manifest = Manifest.load(cfg.manifest_path)
    report = sets_mod.status_report(manifest, args.set)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(sets_mod.format_status(report))
    return EXIT_OK


def _cmd_verify(args, cfg: CorpusConfig) -> int:
    manifest = Manifest.load(cfg.manifest_path)
    report = verify_mod.verify_set(cfg, manifest, args.set)
    payload = {"matched": report.matched,
               "mismatched": [{"id": i, "expected": e, "got": g}
                              for i, e, g in report.mismatched],
               "unavailable": report.unavailable}
    _emit(args, payload,
          f"verify: matched={len(report.matched)} "
          f"mismatched={len(report.mismatched)} unavailable={len(report.unavailable)}")
    return EXIT_OK if report.ok else EXIT_PROVENANCE


# --- wiring -------------------------------------------------------------

def _config(args) -> CorpusConfig:
    cfg = CorpusConfig.from_env()
    overrides = {}
    if args.manifest:
        overrides["manifest_path"] = Path(args.manifest)
    if args.cache:
        overrides["audio_cache"] = Path(args.cache)
    return dataclasses.replace(cfg, **overrides) if overrides else cfg


def _emit(args, payload: dict, human: str) -> None:
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(human)


def _parser() -> argparse.ArgumentParser:
    # Global options usable either before or after the subcommand.
    common = argparse.ArgumentParser(add_help=False)
    s = argparse.SUPPRESS
    common.add_argument("--manifest", default=s,
                        help="manifest path (default corpus/sources/manifest.yaml)")
    common.add_argument("--set", default=s, help="scope the run to one source set id")
    common.add_argument("--cache", default=s, help="audio cache dir (default corpus/.audio-cache)")
    common.add_argument("--json", action="store_true", default=s,
                        help="machine-readable output")

    p = argparse.ArgumentParser(prog="python -m sadhana_setu.corpus",
                                description="Hari-Nāma corpus pipeline", parents=[common])
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("seed", parents=[common], help="seed the manifest from a listing")
    sp.add_argument("--url", help="listing page URL to fetch + parse")
    sp.add_argument("--html", help="local listing HTML file (offline)")
    sp.add_argument("--language", default="en", help="declared language (default en)")
    sp.set_defaults(func=_cmd_seed)

    sf = sub.add_parser("fetch", parents=[common], help="download audio to the cache")
    sf.set_defaults(func=_cmd_fetch)

    st = sub.add_parser("transcribe", parents=[common], help="transcribe fetched audio")
    st.add_argument("--retranscribe", action="store_true",
                    help="re-transcribe even if a transcript exists")
    st.set_defaults(func=_cmd_transcribe)

    ss = sub.add_parser("status", parents=[common], help="per-set progress report")
    ss.set_defaults(func=_cmd_status)

    sv = sub.add_parser("verify", parents=[common], help="re-fetch and compare checksums")
    sv.set_defaults(func=_cmd_verify)
    return p


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
