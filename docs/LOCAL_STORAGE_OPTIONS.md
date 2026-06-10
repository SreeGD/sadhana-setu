# Local Storage Options for Daily + Weekly Tracker

The app currently uses SQLite. Before committing to it as the long-term
home for your tracker data, here are the realistic alternatives, scored
against what actually matters for a personal sadhana journal.

## What "matters" for this data

| Concern | Why it matters here |
|---|---|
| **Human-readable** | You'll want to scan your own history; you keep paper logs already |
| **Diffable / git-friendly** | If you decide to version-control your journal, plaintext wins |
| **Easy to merge across devices** | Phone edits + laptop edits should reconcile cleanly |
| **GDrive-syncable** | Per-file granularity = only changed files re-upload |
| **Fast for the pattern engine** | M5 needs to scan 4-12 weeks of daily entries quickly |
| **Backup-safe** | Restore should be trivial: copy a folder back |
| **Small surface, low ceremony** | This is a sadhana app, not infrastructure |

## Options

### L1 — SQLite (current)
```
data/sadhana_setu.db
```
- **Read for patterns:** indexed SQL — fast
- **Human-readable:** ✗ binary
- **Diffable:** ✗ (you can run `sqlite3 .dump` but it's ugly)
- **Merge across devices:** hard — needs row-level merge logic on top
- **GDrive sync:** upload whole .db on every change (tens of KB, fine)
- **Restore:** copy file back, works

### L2 — JSON file per day + per week
```
data/journal/daily/2026-06-10.json
data/journal/weekly/2026-W23.json
```
- **Read:** load only the dates the pattern engine needs (cheap)
- **Human-readable:** ✓ JSON is fine
- **Diffable:** ✓ each day is its own file
- **Merge:** trivial — different days = different files, no conflict
- **GDrive sync:** only touched files re-upload (Drive supports this)
- **Restore:** copy folder back
- **Cost:** lots of small files (~365/year), fine on modern FS

### L3 — Append-only JSONL
```
data/journal/daily.jsonl   # one JSON object per line, append on save
data/journal/weekly.jsonl
```
- **Read:** stream-scan or load fully into memory (small)
- **Human-readable:** ✓ readable line-by-line
- **Diffable:** ✓ but edits rewrite history (append-only encourages
  "correction entries" instead of modifying past lines)
- **Merge:** sort+dedup by `(date, updated_at)` — easy
- **GDrive sync:** whole file each time, but stays under a few MB for years
- **Restore:** copy file back
- **Cost:** edits to past entries are awkward

### L4 — YAML per day + per week (matches content library style)
```
data/journal/daily/2026-06-10.yaml
data/journal/weekly/2026-W23.yaml
```
- Same shape as L2 but YAML; lines like `rounds: 16` read like a log
- **Human-readable:** ✓✓ best of all options for browse-by-eye
- **Diffable:** ✓
- **Pattern engine cost:** YAML parse ~10× slower than JSON, still
  negligible at this scale (12-week window = ~84 small files)
- **Aesthetic match:** mirrors how your content libraries are stored,
  so the whole `data/` tree looks consistent

### L5 — Markdown with frontmatter (Obsidian-style)
```
data/journal/2026-06-10.md
---
date: 2026-06-10
rounds: 16
hearing_minutes: 30
hearing_passage: "SB 1.1.1"
tip_id: samadhaya_mano_hrdi
tip_done: true
---

# Today

Heart-centering worked well in rounds 3-8 — fewer wanderings. SB class
was Sūta's invocations. Felt the connection between hearing and round-9
absorption.
```
- **Human-readable:** ✓✓✓ this is just *writing*
- **Best for free-form journaling** — you can write a paragraph next
  to the metrics
- **Diffable:** ✓
- **Compatible with Obsidian, Logseq** — if you already journal there,
  this drops in
- **Pattern engine cost:** parse frontmatter only (cheap, ignore body)
- **Cost:** introduces a "body" field that you'll be tempted to fill
  out — could be a feature (journaling) or a friction (one more thing)

### L6 — Single JSON snapshot file
```
data/tracker.json   # {daily: [...], weekly: [...]}
```
- **Read:** load once, query in-memory
- **Human-readable:** ✓ but a 300-day file gets long
- **Diffable:** ✓ but every save changes the whole file
- **Merge:** array merges, doable but more work than L2/L4
- **GDrive sync:** matches the GDrive design (single file)
- **Restore:** copy file back
- **Best fit if you go static** (one file → one upload)

### L7 — Hybrid: SQLite primary + YAML mirror
- SQLite stays the primary store (pattern engine reads from it,
  trades stay ACID)
- On every save, also write a YAML file for that day/week
- YAML files are what get synced to GDrive and backed up to git
- **Best of both:** speed of SQLite, readability of YAML
- **Cost:** two write paths to keep in sync (write a single
  `save_entry()` helper that does both, test once, forget about it)

### L8 — DuckDB
- SQL like SQLite but columnar; Parquet export trivial
- **Cost:** another binding to install; overkill at this scale
- **When you'd want it:** if the journal grows to 50+ years of multi-
  user data with analytical queries. Not now.

## Scoring matrix

| Option | Read | Human | Diff | Merge | GDrive | Restore | Verdict |
|---|---|---|---|---|---|---|---|
| L1 SQLite | ✓✓ | ✗ | ✗ | △ | △ | ✓ | currently in use |
| L2 JSON/day | ✓ | ✓ | ✓ | ✓✓ | ✓✓ | ✓ | clean, simple |
| L3 JSONL | ✓ | ✓ | △ | ✓ | ✓ | ✓ | log-style |
| L4 YAML/day | ✓ | ✓✓ | ✓ | ✓✓ | ✓✓ | ✓ | most readable |
| L5 MD frontmatter | △ | ✓✓✓ | ✓ | ✓✓ | ✓✓ | ✓ | best for journaling |
| L6 single JSON | ✓ | ✓ | △ | △ | ✓✓ | ✓ | best for static |
| L7 SQLite+YAML | ✓✓ | ✓✓ | ✓ | ✓✓ | ✓✓ | ✓ | best overall |
| L8 DuckDB | ✓✓ | ✗ | ✗ | △ | △ | ✓ | overkill |

## Decision lenses

Choose by which of these matters most to you:

- **Just keep things working (least change)** → **L1** (do nothing)
- **Want to read my own journal manually** → **L4** or **L5**
- **Want to also write paragraphs about my chanting** → **L5**
- **Going static + GDrive primary** → **L6**
- **Want speed + readability + cloud sync** → **L7** (hybrid)
- **Want git-style append history** → **L3**

## Recommendation

**L7 — SQLite primary + YAML mirror.**

Reasoning:
1. SQLite is already wired and fast — keep the pattern engine happy.
2. YAML mirror gives you something you can actually browse with your
   eyes, search with grep, and back up to GDrive with file-level
   granularity.
3. The two-write path is small: one `save_entry(date, kind, data)`
   helper that writes to both. Easy to test.
4. If you ever go static, the YAML tree is the source — drop the
   SQLite, and a small JS YAML parser reads the same files.
5. The GDrive sync only uploads files that changed — efficient.

Concretely:
```
data/
├── sadhana_setu.db                    # SQLite, primary, gitignored
└── journal/
    ├── daily/
    │   ├── 2026-06-08.yaml
    │   ├── 2026-06-09.yaml
    │   └── 2026-06-10.yaml
    └── weekly/
        └── 2026-W23.yaml
```

YAML shape — daily:
```yaml
date: 2026-06-10
rounds: 16
hearing_minutes: 30
hearing_passage: "SB 1.1.1 — Sūta's invocations"
tip_id: samadhaya_mano_hrdi
tip_done: true
block_chant_door: 2     # which "door" today's japa was through
updated_at: 2026-06-10T07:42:00Z
```

YAML shape — weekly:
```yaml
week_start: 2026-06-08
japa_score: 4
hearing_score: 3
morning_score: 4
yoga_score: 2
sleep_score: 4
highlights: |
  Tuesday and Thursday were attentive throughout.
anarthas_noticed: |
  krodha on Wednesday evening (responded to Anvi sharply)
next_week_sankalpa: |
  Sleep by 10:30 PM every weekday.
updated_at: 2026-06-13T19:10:00Z
```

If you'd rather skip the hybrid step:
- **L4** (YAML only, no SQLite) is the next-best — fully readable,
  fully diffable, no second write path. Pattern engine becomes a
  small loader. You trade ~10ms of parse latency for one less
  storage system to think about.

## Effort to migrate from current SQLite

| Target | Effort |
|---|---|
| L1 → L7 (hybrid) | ~150 lines: a `journal_yaml.py` writer + reader, hook into `db/records.py` |
| L1 → L4 (YAML-only) | ~300 lines: rewrite `db/records.py` against the file tree, retire SQLite |
| L1 → L5 (Markdown) | ~400 lines: same as L4 plus a frontmatter parser + body editor |
| L1 → L6 (single JSON) | ~200 lines: one-file ledger, in-memory dict |

L7 is the smallest move with the biggest win.
