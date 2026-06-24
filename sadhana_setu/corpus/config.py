"""Configuration + tool preflight for the corpus pipeline.

All settings come from the environment with sensible defaults so the pipeline is
local-first and reproducible (Constitution II/VI). The whisper model and flags are
pinned here and recorded in transcript front-matter.
"""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

# Pinned whisper.cpp model + flags (research R1). Override via env for hard lectures.
DEFAULT_MODEL = "ggml-large-v3-turbo"
# Segment-level timestamps (clarification), JSON output for stable parsing.
DEFAULT_WHISPER_FLAGS = ("--output-json", "--language", "en", "--max-context", "0")


class ToolMissingError(RuntimeError):
    """A required external tool or model is unavailable (CLI exit code 3)."""


@dataclass(frozen=True)
class CorpusConfig:
    """Resolved pipeline configuration.

    Paths are repo-relative by default but may be absolute via env.
    """

    repo_root: Path
    audio_cache: Path
    transcripts_dir: Path
    manifest_path: Path
    model_dir: Path
    model_name: str = DEFAULT_MODEL
    whisper_flags: tuple[str, ...] = DEFAULT_WHISPER_FLAGS
    fetch_rate_limit_seconds: float = 2.0
    chunk_seconds: int = 600
    user_agent: str = "sadhana-setu-corpus/0.1 (+https://github.com/SreeGD/sadhana-setu)"
    # Enrichment (spec 002): Claude Code headless, not the Anthropic API.
    notes_dir: Path = None  # set in from_env
    enrichment_version: str = "claude-code/v1"
    claude_flags: tuple[str, ...] = ("-p", "--output-format", "json")

    @classmethod
    def from_env(cls, repo_root: Path | str | None = None) -> "CorpusConfig":
        root = Path(repo_root) if repo_root else _find_repo_root()
        corpus = root / "corpus"
        return cls(
            repo_root=root,
            audio_cache=Path(os.environ.get("CORPUS_AUDIO_CACHE", corpus / ".audio-cache")),
            transcripts_dir=Path(
                os.environ.get("CORPUS_TRANSCRIPTS_DIR", corpus / "transcripts")
            ),
            notes_dir=Path(os.environ.get("CORPUS_NOTES_DIR", corpus / "notes")),
            manifest_path=Path(
                os.environ.get("CORPUS_MANIFEST", corpus / "sources" / "manifest.yaml")
            ),
            model_dir=Path(
                os.environ.get("WHISPER_MODEL_DIR", Path.home() / ".cache" / "whisper")
            ),
            model_name=os.environ.get("WHISPER_MODEL", DEFAULT_MODEL),
            fetch_rate_limit_seconds=float(os.environ.get("CORPUS_FETCH_RATE_LIMIT", "2.0")),
            chunk_seconds=int(os.environ.get("CORPUS_CHUNK_SECONDS", "600")),
        )

    @property
    def model_path(self) -> Path:
        name = self.model_name
        if not name.endswith(".bin"):
            name = f"{name}.bin"
        return self.model_dir / name

    def whisper_cli(self) -> str:
        exe = shutil.which("whisper-cli") or shutil.which("whisper-cpp") or shutil.which("main")
        if not exe:
            raise ToolMissingError(
                "whisper-cli (whisper.cpp) not found on PATH. Install via "
                "`brew install whisper-cpp`."
            )
        return exe

    def ffmpeg(self) -> str:
        exe = shutil.which("ffmpeg")
        if not exe:
            raise ToolMissingError("ffmpeg not found on PATH. Install via `brew install ffmpeg`.")
        return exe

    def ffprobe(self) -> str:
        exe = shutil.which("ffprobe")
        if not exe:
            raise ToolMissingError("ffprobe not found on PATH (ships with ffmpeg).")
        return exe

    def claude_cli(self) -> str:
        exe = shutil.which("claude")
        if not exe:
            raise ToolMissingError(
                "claude (Claude Code CLI) not found on PATH. Enrichment runs "
                "`claude -p`; install Claude Code."
            )
        return exe

    def preflight(self, *, require_model: bool = True) -> None:
        """Verify external tools (and optionally the whisper model) are present.

        Raises ``ToolMissingError`` (mapped to CLI exit code 3) on any gap.
        ``require_model`` is False for stages that don't transcribe (seed/fetch/status).
        """
        self.whisper_cli()
        self.ffmpeg()
        self.ffprobe()
        if require_model and not self.model_path.exists():
            raise ToolMissingError(
                f"whisper model not found at {self.model_path}. Download "
                f"{self.model_name} into {self.model_dir} (see quickstart.md)."
            )


def _find_repo_root(start: Path | None = None) -> Path:
    """Walk up from ``start`` (or CWD) to the directory containing ``corpus/``."""
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "corpus").is_dir() or (candidate / ".git").is_dir():
            return candidate
    return here
