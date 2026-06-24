"""Reproducibility check: re-fetch from the manifest and compare checksums (US4, SC-004).

Proves the corpus is reproducible from text + manifest alone — the audio set can be
rebuilt and every checksum still matches what the transcripts were derived from.
"""
from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from sadhana_setu.corpus.config import CorpusConfig
from sadhana_setu.corpus.fetch import _ext_for, _http_download, _sha256_file, _Unavailable
from sadhana_setu.corpus.manifest import Manifest, Status

_CHECKED = (Status.FETCHED, Status.TRANSCRIBED)


@dataclass
class VerifyReport:
    matched: list[str] = field(default_factory=list)
    mismatched: list[tuple[str, str, str]] = field(default_factory=list)  # id, expected, got
    unavailable: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.mismatched and not self.unavailable


def verify_set(cfg: CorpusConfig, manifest: Manifest, set_id: str | None = None,
               *, downloader=None) -> VerifyReport:
    """Re-fetch each checksummed lecture to a temp dir and compare to the recorded hash."""
    download = downloader or _http_download
    report = VerifyReport()
    with tempfile.TemporaryDirectory(prefix="corpus-verify-") as td:
        tmpdir = Path(td)
        for _, lec in manifest.iter_lectures(set_id):
            if lec.status not in _CHECKED or not lec.sha256:
                continue
            dest = tmpdir / f"{lec.id}{_ext_for(lec.urls[0])}"
            try:
                download(lec.urls[0], dest, cfg)
            except _Unavailable as exc:
                report.unavailable.append(f"{lec.id}: {exc}")
                continue
            actual = _sha256_file(dest)
            dest.unlink(missing_ok=True)
            if actual == lec.sha256:
                report.matched.append(lec.id)
            else:
                report.mismatched.append((lec.id, lec.sha256, actual))
    return report
