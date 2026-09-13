# Data Model: Localization

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

YAML catalogs on disk + a small in-memory locale state. English source data (`data/*.yaml`) is
unchanged.

## Entity: Locale

| Field | Type | Notes |
|---|---|---|
| `code` | enum `en` \| `te` \| `kn` \| `ta` | Supported languages. |
| (selection) | `st.session_state["locale"]` + settings file | Persists across sessions; default `en`. |
| `show_machine_drafts` | bool in `data/i18n/settings.yaml` (git-ignored) | Explicit opt-in to preview unreviewed drafts locally; default `false`. |

## Entity: UI Message Catalog — `data/i18n/ui/<locale>.yaml`

A flat `key → string` map plus a catalog-level review record under the reserved `_meta` key.
`en` is authored (source of keys); te/kn/ta are drafted into `<locale>.draft.yaml` and promoted
into the live `<locale>.yaml` by the reviewer.

```yaml
# data/i18n/ui/te.yaml  (LIVE)
_meta:
  reviewed: false          # flipped to true by the native-devotee reviewer (T019)
  reviewer: null
  date: null
view.pre_japa: "జప-పూర్వ"
view.notes: "గమనికలు"
# ... missing key ⇒ English fallback (FR-002)
```

Rules: any key absent in `<locale>.yaml` falls back to `en` (never blank); a catalog whose
`_meta.reviewed` is not `true` is withheld entirely (English) unless the practitioner has opted in
via `show_machine_drafts: true` in `settings.yaml` (Constitution V, T021/T027). `_meta` is never a
UI string.

## Entity: Translated Content Item — `data/i18n/content/<locale>/<library>.yaml`

Per-library overlay keyed by the item's id/index; each entry carries the translated field(s) and a
**review status**. Machine drafts are written to `<library>.draft.yaml` (never read on the
reviewed path); the reviewer promotes approved rows into the live `<library>.yaml`.

```yaml
# data/i18n/content/te/affirmations.yaml  (LIVE; drafts live in affirmations.draft.yaml)
- id: 0
  text: "<telugu translation>"
  reviewed: true            # only reviewed entries are published (Constitution V)
- id: 1
  text: "<draft>"
  reviewed: false           # ⇒ English shown instead
```

| Field | Type | Notes |
|---|---|---|
| `id` | int/str | Matches the English item's index/id in `data/<library>.yaml`. |
| translated fields | str | e.g. `text`, `summary`, `teaching`, `prompt` — per library. |
| `reviewed` | bool | False ⇒ withheld; English shown (FR-004). |
| `citation` | (inherited) | Preserved from the English item (FR-006). |

State: `reviewed: false` in `<library>.draft.yaml` (Claude Code draft) → row promoted into
`<library>.yaml` with `reviewed: true` (native-devotee approval via file; git diff is the trail).

## Entity: Transliteration (runtime, not stored)

`translit.to_script(text, locale, src="iast")` → the same Sanskrit rendered in the locale's script
(sounds preserved). Used for verses + Sanskrit terms in a vernacular locale; **IAST fallback** on
any failure. Optionally memoized.

## Relationships

```text
UI render --i18n.t(key)--> ui/<locale>.yaml[key]  (else en)
Content render --i18n.localize_content(lib,id,field,en)--> content/<locale>/<lib>.yaml[id][field] if reviewed (else en)
Verse/term render (vernacular locale) --translit.to_script(iast, locale)--> vernacular script (else IAST)
build_static.py --emits--> data/i18n/* for the static runtime (FR-012)
```
