"""Fetch audio to the git-ignored cache and record provenance (US1).

Downloads are serial and rate-limited (Constitution III). Audio is keyed in the cache
by its SHA-256 and never committed (Constitution III/VI). Re-runs are idempotent;
a cache file whose hash diverges from the recorded checksum stops the run with a
``ProvenanceError`` (FR-012).
"""
from __future__ import annotations

import hashlib
import time
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from sadhana_setu.corpus.audio import probe_duration
from sadhana_setu.corpus.config import CorpusConfig
from sadhana_setu.corpus.manifest import Lecture, Manifest, ProvenanceError, Status

_AUDIO_EXT = (".mp3", ".m4a", ".ogg", ".opus", ".wav")


class FetchResult:
    def __init__(self) -> None:
        self.fetched: list[str] = []
        self.deferred: list[str] = []
        self.unavailable: list[str] = []
        self.excluded: list[str] = []
        self.skipped: list[str] = []


def fetch_set(cfg: CorpusConfig, manifest: Manifest, set_id: str | None = None,
              *, downloader=None, sleep=time.sleep) -> FetchResult:
    """Fetch all ``pending`` lectures (optionally scoped to ``set_id``)."""
    cfg.audio_cache.mkdir(parents=True, exist_ok=True)
    result = FetchResult()
    download = downloader or _http_download
    first = True
    for _, lec in manifest.iter_lectures(set_id):
        if lec.status is not Status.PENDING:
            result.skipped.append(lec.id)
            continue
        if not first and cfg.fetch_rate_limit_seconds:
            sleep(cfg.fetch_rate_limit_seconds)
        first = False
        _fetch_one(cfg, manifest, lec, download, result)
    return result


def _fetch_one(cfg, manifest, lec: Lecture, download, result: FetchResult) -> None:
    # Non-English declared at seed ⇒ deferred before any download (FR-013).
    if lec.language != "en":
        lec.set_status(Status.DEFERRED)
        result.deferred.append(lec.id)
        return

    ext = _ext_for(lec.urls[0])

    # Idempotent: already-known checksum with a matching cache file ⇒ verify, skip.
    if lec.sha256:
        cached = cfg.audio_cache / f"{lec.sha256}{ext}"
        if cached.exists():
            actual = _sha256_file(cached)
            if actual != lec.sha256:
                raise ProvenanceError(
                    f"{lec.id}: cache {cached.name} hash {actual[:12]} != recorded "
                    f"{lec.sha256[:12]}"
                )
            result.skipped.append(lec.id)
            return

    tmp = cfg.audio_cache / f".{lec.id}{ext}.part"
    try:
        download(lec.urls[0], tmp, cfg)
    except _Unavailable as exc:
        lec.notes = (lec.notes + f" unavailable:{exc}").strip()
        lec.set_status(Status.UNAVAILABLE)
        result.unavailable.append(lec.id)
        tmp.unlink(missing_ok=True)
        return

    digest = _sha256_file(tmp)
    if lec.sha256 and digest != lec.sha256:
        tmp.unlink(missing_ok=True)
        raise ProvenanceError(f"{lec.id}: downloaded hash {digest[:12]} != recorded "
                              f"{lec.sha256[:12]}")

    # Duplicate audio across the corpus (FR-009).
    dup = manifest.find_by_sha256(digest, exclude_id=lec.id)
    final = cfg.audio_cache / f"{digest}{ext}"
    tmp.replace(final)

    if dup is not None:
        for url in lec.urls:
            if url not in dup.urls:
                dup.urls.append(url)
        lec.sha256 = digest
        lec.notes = (lec.notes + f" duplicate-of:{dup.id}").strip()
        lec.set_status(Status.EXCLUDED)
        result.excluded.append(lec.id)
        return

    lec.sha256 = digest
    try:
        lec.duration_seconds = int(round(probe_duration(cfg, final)))
    except Exception:
        lec.duration_seconds = None
    lec.set_status(Status.FETCHED)
    result.fetched.append(lec.id)


class _Unavailable(Exception):
    pass


def _http_download(url: str, dest: Path, cfg: CorpusConfig) -> None:
    headers = {"User-Agent": cfg.user_agent}
    try:
        with httpx.stream("GET", url, headers=headers, follow_redirects=True,
                          timeout=60.0) as resp:
            if resp.status_code != 200:
                raise _Unavailable(f"HTTP {resp.status_code}")
            with dest.open("wb") as fh:
                for block in resp.iter_bytes():
                    fh.write(block)
    except httpx.HTTPError as exc:  # network/DNS/timeout
        raise _Unavailable(str(exc)) from exc


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _ext_for(url: str) -> str:
    path = urlsplit(url).path.lower()
    for ext in _AUDIO_EXT:
        if path.endswith(ext):
            return ext
    return ".mp3"
