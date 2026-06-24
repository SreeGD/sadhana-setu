# Contract: Study / Notes View

`sadhana_setu/ui/notes_view.py` (+ `sadhana_setu/flows/corpus_notes.py`) — browse and read the
reviewed enriched notes (US4, FR-009). Reads files on disk; no ChromaDB.

```python
# flows/corpus_notes.py
def list_reviewed_notes(notes_dir=None) -> list[NoteRef]:
    """Enumerate corpus/notes/**/*.md with front-matter status == 'reviewed', grouped-ready.

    Each NoteRef: {set_id, lecture_id, speaker, title, path}. Drafts are excluded (Constitution V).
    """

def read_note(path) -> tuple[dict, str]:
    """Return (front_matter, body_markdown) for a reviewed note."""
```

## View behavior

- Lists reviewed notes grouped by `set_id` / speaker (e.g. "Bhūrijana Prabhu").
- Selecting one renders its Markdown body (theme, key teachings, verses, references, glossary).
- **Never** shows a `draft` note (SC: only reviewed content surfaces).
- Empty state when no reviewed notes exist yet ("No reviewed notes yet"), not an error.
- No metrics, no scoring, no tracking (Constitution IV).
