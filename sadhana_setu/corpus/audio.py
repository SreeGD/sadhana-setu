"""ffmpeg-based audio helpers: probe, decode to 16 kHz mono WAV, and chunk.

Long lectures are split into ~``chunk_seconds`` pieces at silence boundaries so
whisper.cpp transcribes them within bounded memory; each chunk records its start
offset so segment timestamps can be made continuous again (research R7).
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from sadhana_setu.corpus.config import CorpusConfig


@dataclass
class Chunk:
    path: Path
    offset_seconds: float


def probe_duration(cfg: CorpusConfig, src: Path) -> float:
    """Return media duration in seconds via ffprobe."""
    out = subprocess.run(
        [cfg.ffprobe(), "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(src)],
        check=True, capture_output=True, text=True,
    )
    return float(json.loads(out.stdout)["format"]["duration"])


def decode_to_wav(cfg: CorpusConfig, src: Path, dst: Path) -> Path:
    """Decode any input to 16 kHz mono PCM WAV (whisper.cpp's expected input)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [cfg.ffmpeg(), "-y", "-i", str(src), "-ar", "16000", "-ac", "1",
         "-c:a", "pcm_s16le", str(dst)],
        check=True, capture_output=True,
    )
    return dst


def segment(cfg: CorpusConfig, wav: Path, out_dir: Path) -> list[Chunk]:
    """Split ``wav`` into ~chunk_seconds pieces, returning chunks with offsets.

    Uses ffmpeg's segment muxer on the decoded WAV. Boundaries land on
    ``chunk_seconds`` marks; because the input is already mono PCM, splits do not
    re-encode and stay sample-accurate. Short inputs return a single chunk.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    duration = probe_duration(cfg, wav)
    if duration <= cfg.chunk_seconds:
        return [Chunk(path=wav, offset_seconds=0.0)]

    pattern = str(out_dir / "chunk_%04d.wav")
    subprocess.run(
        [cfg.ffmpeg(), "-y", "-i", str(wav), "-f", "segment",
         "-segment_time", str(cfg.chunk_seconds), "-c", "copy", pattern],
        check=True, capture_output=True,
    )
    chunks: list[Chunk] = []
    for idx, path in enumerate(sorted(out_dir.glob("chunk_*.wav"))):
        chunks.append(Chunk(path=path, offset_seconds=idx * cfg.chunk_seconds))
    return chunks
