"""Seed the manifest from a source listing (FR-015, hybrid).

``parse_listing`` is pure (HTML → candidate entries) so it is unit-testable against a
saved fixture; ``seed_set`` applies the FR-014 topic filter and writes draft
``pending`` entries for maintainer verification. Speaker sets are topic-filtered;
seminar sets are taken in full. The concrete site DOM is captured here at build time
(research R2); the default parser extracts anchors to audio files.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urljoin

from sadhana_setu.corpus.manifest import Lecture, Manifest, SourceSet, Status

# FR-014 Holy-Name topic filter (applied to speaker sets only).
TOPIC_KEYWORDS = (
    "holy name", "holy-name", "holyname", "harinam", "hari-nam", "harinām", "nama",
    "nāma", "naam", "japa", "chant", "offens", "aparadha", "aparādha", "bhava",
    "bhāva", "sixteen rounds", "namatattva", "nama-tattva",
)
_AUDIO_EXT = (".mp3", ".m4a", ".ogg", ".opus", ".wav")
_DATE_RE = re.compile(r"(\d{4})[-/](\d{2})[-/](\d{2})")


@dataclass
class ListingEntry:
    title: str
    url: str
    date: str | None = None


class _AudioLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.entries: list[tuple[str, str]] = []  # (href, link_text)
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            if href and href.lower().split("?")[0].endswith(_AUDIO_EXT):
                self._href = href
                self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.entries.append((self._href, "".join(self._text).strip()))
            self._href = None
            self._text = []


def parse_listing(html: str, base_url: str = "") -> list[ListingEntry]:
    """Extract audio-lecture entries from a listing page."""
    parser = _AudioLinkParser()
    parser.feed(html)
    entries: list[ListingEntry] = []
    for href, text in parser.entries:
        url = urljoin(base_url, href)
        # Apache autoindex truncates the visible link text (e.g. "BJP_Seminar_-_Holyna..>");
        # the href is the canonical full filename (carries date + topic words), so prefer it
        # whenever the anchor text is missing or looks truncated.
        title = text if text and not _looks_truncated(text) else _title_from_url(url)
        entries.append(ListingEntry(title=title, url=url, date=_extract_date(title, url)))
    return entries


def _looks_truncated(text: str) -> bool:
    """True for an autoindex-truncated anchor (e.g. 'BJP_Seminar_-_Holyna..>')."""
    t = text.rstrip().rstrip(">").rstrip()
    return t.endswith("..") or t.endswith("…")


def seed_set(manifest: Manifest, set_id: str, entries: list[ListingEntry],
             *, language: str = "en") -> list[Lecture]:
    """Add draft ``pending`` lectures to ``set_id``; return the newly added ones.

    Existing lectures (matched by URL) are left untouched (idempotent). Speaker sets
    apply the topic filter; seminar sets include everything.
    """
    sset: SourceSet = manifest.get_set(set_id)
    apply_filter = sset.kind == "speaker"
    existing_urls = {u for lec in sset.lectures for u in lec.urls}
    existing_ids = {lec.id for _, lec in manifest.iter_lectures()}

    added: list[Lecture] = []
    for entry in entries:
        if entry.url in existing_urls:
            continue
        tags = matched_topics(entry.title)
        if apply_filter and not tags:
            continue
        lec_id = _unique_slug(make_slug(entry.title, entry.date), existing_ids)
        existing_ids.add(lec_id)
        added.append(Lecture(
            id=lec_id, title=entry.title, urls=[entry.url], status=Status.PENDING,
            date=entry.date, language=language, topic_tags=tags,
        ))
    sset.lectures.extend(added)
    return added


def matched_topics(title: str) -> list[str]:
    low = title.lower()
    return [kw for kw in TOPIC_KEYWORDS if kw in low]


def make_slug(title: str, date: str | None = None) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    base = re.sub(r"-{2,}", "-", base)[:60].strip("-") or "lecture"
    return f"{base}-{date}" if date else base


def _unique_slug(slug: str, taken: set[str]) -> str:
    if slug not in taken:
        return slug
    n = 2
    while f"{slug}-{n}" in taken:
        n += 1
    return f"{slug}-{n}"


def _title_from_url(url: str) -> str:
    stem = url.rstrip("/").split("/")[-1]
    for ext in _AUDIO_EXT:
        if stem.lower().endswith(ext):
            stem = stem[: -len(ext)]
    return re.sub(r"[-_]+", " ", stem).strip() or stem


def _extract_date(*texts: str) -> str | None:
    for t in texts:
        m = _DATE_RE.search(t or "")
        if m:
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None
