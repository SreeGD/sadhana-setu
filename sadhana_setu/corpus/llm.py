"""Enrichment LLM provider — Claude Code headless (`claude -p`), not the Anthropic API.

`Provider.complete(prompt) -> str` returns the model's raw text answer; `parse_enrichment`
turns that into a validated dict matching ``contracts/enrichment-output.schema.json``. The model
returns reference *identifiers* only — grounding.py supplies final verse text (Constitution I).
"""
from __future__ import annotations

import json
import re
import subprocess
from abc import ABC, abstractmethod

from sadhana_setu.corpus.config import CorpusConfig

_TS_RE = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3}$")
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


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
        proc = subprocess.run(
            [self.cfg.claude_cli(), *self.cfg.claude_flags],
            input=prompt, capture_output=True, text=True, check=True,
        )
        return _extract_result(proc.stdout)


def _extract_result(stdout: str) -> str:
    """Pull the model's answer out of `claude --output-format json` envelope."""
    try:
        env = json.loads(stdout)
    except json.JSONDecodeError:
        return stdout  # already raw text
    if isinstance(env, dict):
        return env.get("result") or env.get("text") or stdout
    return stdout


def parse_enrichment(raw: str) -> dict:
    """Parse + validate the model's answer into the enrichment output contract."""
    text = _FENCE_RE.sub("", raw).strip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        raise EnrichmentError(f"enrichment output is not valid JSON: {exc}") from exc
    validate_enrichment(obj)
    return obj


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
