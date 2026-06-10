"""Pre-japa flow — selects 1-2 sastra-cited quotes for the pre-japa view.

Calls kg-mcp's `search_corpus` (kg_augmented mode) filtered by today's
value, then tries `get_verse` to enrich each chunk with full Sanskrit +
translation. Chunks without a verse_ref are filtered out — per PRD
§10.7 the pre-japa view requires citable quotes.
"""
from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field

from sadhana_setu.mcp_client import KGMCPClient, parse_response

_LEADING_REF = re.compile(r"^\[[^\]]+\]\s*\n?")
_LEADING_NUM = re.compile(r"^\d+\.\s+")


@dataclass(frozen=True)
class Quote:
    verse_ref: str
    text: str
    source: str | None = None
    author: str | None = None
    devanagari: str | None = None
    iast: str | None = None
    translation: str | None = None


@dataclass
class PreJapaContent:
    quotes: list[Quote] = field(default_factory=list)
    mcp_ok: bool = True
    error: str | None = None
    today_value: str | None = None


async def _build_async(today_value: str) -> PreJapaContent:
    client = KGMCPClient()
    try:
        await client.connect()
        search_result = await client.call_tool(
            "search_corpus",
            {
                "query": f"attentive chanting of the Holy Name; the principle of {today_value}",
                "mode": "kg_augmented",
                "entity_filters": {"value": [today_value, "kirtan", "bhakti"]},
                "top_k": 10,
            },
        )
        search_data = parse_response(search_result) or {}
        candidates = [c for c in search_data.get("chunks", []) if c.get("verse_ref")]
        quotes: list[Quote] = []
        for chunk in candidates[:2]:
            verse_ref = chunk["verse_ref"]
            verse_extra: dict = {}
            try:
                verse_result = await client.call_tool("get_verse", {"verse_ref": verse_ref})
                verse_data = parse_response(verse_result) or {}
                if verse_data.get("found"):
                    verse_extra = {
                        "devanagari": verse_data.get("devanagari"),
                        "iast": verse_data.get("iast"),
                        "translation": verse_data.get("translation"),
                    }
            except Exception:
                pass
            cleaned = _LEADING_REF.sub("", chunk.get("text") or "")
            cleaned = _LEADING_NUM.sub("", cleaned).strip()
            quotes.append(
                Quote(
                    verse_ref=verse_ref,
                    text=cleaned,
                    source=chunk.get("source_text") or _infer_source(verse_ref),
                    author=chunk.get("author"),
                    **verse_extra,
                )
            )
        return PreJapaContent(quotes=quotes, mcp_ok=True, today_value=today_value)
    except Exception as exc:
        return PreJapaContent(
            quotes=[],
            mcp_ok=False,
            error=f"{type(exc).__name__}: {exc}",
            today_value=today_value,
        )
    finally:
        try:
            await client.close()
        except Exception:
            pass


_SOURCE_MAP = {
    "BG": "Bhagavad-gita As It Is",
    "SB": "Srimad Bhagavatam",
    "CC": "Caitanya Caritamrta",
    "BRS": "Bhakti Rasamrta Sindhu",
    "NOI": "Nectar of Instruction",
    "NOD": "Nectar of Devotion",
}


def _infer_source(verse_ref: str) -> str | None:
    prefix = verse_ref.split()[0] if verse_ref else ""
    return _SOURCE_MAP.get(prefix)


def build_prejapa(today_value: str) -> PreJapaContent:
    """Sync entry point. Calls MCP, returns PreJapaContent."""
    return asyncio.run(_build_async(today_value))
