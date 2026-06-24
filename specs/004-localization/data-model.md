# Data Model: Localization

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

YAML catalogs on disk + a small in-memory locale state. English source data (`data/*.yaml`) is
unchanged.

## Entity: Locale

| Field | Type | Notes |
|---|---|---|
| `code` | enum `en` \| `te` \| `kn` \| `ta` | Supported languages. |
| (selection) | `st.session_state["locale"]` + settings file | Persists across sessions; default `en`. |

## Entity: UI Message Catalog — `data/i18n/ui/<locale>.yaml`

A flat `key → string` map. `en` is authored (source of keys); te/kn/ta are drafted + reviewed.

```yaml
# data/i18n/ui/te.yaml
view.pre_japa: "జప-పూర్వ"
view.notes: "గమనికలు"
# ... missing key ⇒ English fallback (FR-002)
```

Rule: any key absent in `<locale>.yaml` falls back to `en` (never blank).

## Entity: Translated Content Item — `data/i18n/content/<locale>/<library>.yaml`

Per-library overlay keyed by the item's id/index; each entry carries the translated field(s) and a
**review status**.

```yaml
# data/i18n/content/te/affirmations.yaml
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

State: `reviewed: false` (Claude Code draft) → `reviewed: true` (native-devotee approval via file).

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
