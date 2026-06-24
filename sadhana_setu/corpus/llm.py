"""Enrichment LLM provider — Claude Code headless (`claude -p`), not the Anthropic API.

`Provider.complete(prompt) -> str` returns the model's raw text answer; `parse_enrichment`
turns that into a validated dict matching ``contracts/enrichment-output.schema.json``. The model
returns reference *identifiers* only — grounding.py supplies final verse text (Constitution I).
"""
from __future__ import annotations

import json
import re
import subprocess
import time
from abc import ABC, abstractmethod

from sadhana_setu.corpus.config import CorpusConfig

_TS_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}$")
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)
# `claude -p` exits non-zero on transient API overloads; retry with backoff before giving up
# so one blip during a long batch doesn't lose a whole lecture's enrichment.
_MAX_TRIES = 3
_RETRY_SLEEP = 5.0  # seconds; grows per attempt


class EnrichmentError(RuntimeError):
    pass


class Provider(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> str:
        """Return the model's raw text answer for ``prompt``."""


class ClaudeCodeProvider(Provider):
    """Shells out to `claude -p --output-format json` (reuses the Claude Code subscription)."""

    def __init__(self, cfg: CorpusConfig):
        self.cfg = cfg

    def complete(self, prompt: str) -> str:
        cmd = [self.cfg.claude_cli(), *self.cfg.claude_flags]
        last = None
        for attempt in range(1, _MAX_TRIES + 1):
            proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True)
            if proc.returncode == 0:
                return _extract_result(proc.stdout)
            last = proc
            if attempt < _MAX_TRIES:
                time.sleep(_RETRY_SLEEP * attempt)
        detail = (last.stderr or last.stdout or "").strip().replace("\n", " ")[:400]
        raise EnrichmentError(
            f"`claude -p` failed after {_MAX_TRIES} attempts (exit {last.returncode}): {detail}"
        )


def _extract_result(stdout: str) -> str:
    """Pull the model's answer out of `claude --output-format json` envelope."""
    try:
        env = json.loads(stdout)
    except json.JSONDecodeError:
        return stdout  # already raw text
    if isinstance(env, dict):
        return env.get("result") or env.get("text") or stdout
    return stdout


def _parse_json(raw: str) -> dict:
    text = _FENCE_RE.sub("", raw).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise EnrichmentError(f"enrichment output is not valid JSON: {exc}") from exc


def parse_enrichment(raw: str) -> dict:
    """Parse + validate a full (combined) enrichment object."""
    obj = _parse_json(raw)
    validate_enrichment(obj)
    return obj


def parse_section(raw: str) -> dict:
    """Parse + validate one transcript-window's enrichment (key_teachings + candidates)."""
    obj = _parse_json(raw)
    validate_section(obj)
    return obj


def parse_synthesis(raw: str) -> dict:
    """Parse + validate the synthesis pass (theme, practical application, glossary)."""
    obj = _parse_json(raw)
    if not obj.get("theme_summary") or not obj.get("practical_application"):
        raise EnrichmentError("synthesis missing theme_summary / practical_application")
    return obj


def validate_section(obj: dict) -> None:
    if not isinstance(obj, dict) or not isinstance(obj.get("key_teachings"), list):
        raise EnrichmentError("section output must have a key_teachings list")
    for i, kt in enumerate(obj["key_teachings"]):
        if not isinstance(kt, dict) or not kt.get("point") or not kt.get("timestamp"):
            raise EnrichmentError(f"section key_teachings[{i}] needs point + timestamp")
        if not _TS_RE.match(str(kt["timestamp"])):
            raise EnrichmentError(f"section key_teachings[{i}].timestamp must be HH:MM:SS.mmm")


def validate_enrichment(obj: dict) -> None:
    """Structural validation mirroring contracts/enrichment-output.schema.json."""
    if not isinstance(obj, dict):
        raise EnrichmentError("enrichment output must be a JSON object")
    for key in ("theme_summary", "key_teachings", "practical_application"):
        if not obj.get(key):
            raise EnrichmentError(f"enrichment output missing required '{key}'")
    if not isinstance(obj["key_teachings"], list) or not obj["key_teachings"]:
        raise EnrichmentError("key_teachings must be a non-empty list")
    for i, kt in enumerate(obj["key_teachings"]):
        if not isinstance(kt, dict) or not kt.get("point") or not kt.get("timestamp"):
            raise EnrichmentError(f"key_teachings[{i}] needs point + timestamp")
        if not _TS_RE.match(str(kt["timestamp"])):
            raise EnrichmentError(
                f"key_teachings[{i}].timestamp must be HH:MM:SS.mmm (SC-002)"
            )
