# Sadhana Setu — Static Version

A no-server, no-account, browser-native version of the app. Deployed to
GitHub Pages. Anyone can open the URL and use it immediately.

## Two paths, same repo

| | Streamlit version (`sadhana_setu/`) | Static version (`static/`) |
|---|---|---|
| Runtime | Python + Streamlit on your laptop | Just a browser |
| Tracker store | SQLite at `data/sadhana_setu.db` | Browser localStorage |
| Multi-user | One user, the developer | Anyone with the URL |
| Cloud sync | (was) GDrive OAuth | None — export/import JSON instead |
| Pattern engine | scipy + pingouin | Not ported yet (Saturday view shows raw fields) |
| kg-mcp live verses | Available locally | Not available (curated summary only) |
| Where it runs | localhost, Streamlit Cloud | GitHub Pages, Netlify, Cloudflare Pages |

Pick the version that fits the moment. They share the same content
libraries and roughly the same visual design.

## Run the static version locally

```bash
python build_static.py            # regenerate content/*.json from data/*.yaml
python -m http.server -d static 9000
open http://localhost:9000/
```

## Backup / restore

Built into the **Backup** tab in the app:

- **Download backup** — emits `sadhana-setu-backup-YYYY-MM-DD.json` to
  your Downloads folder. Save it anywhere — Desktop, iCloud Drive,
  Dropbox, email to yourself, AirDrop to phone.
- **Restore from backup** — choose a backup JSON file + a strategy:
  - *Merge* — keeps both sets, later edits win at the row level
  - *Replace* — wipes local data and uses the backup as-is
- **Clear all local data** — removes everything on this device. The
  content libraries stay; only your tracker data is cleared.

This is how you move data between devices: download on phone, save to
iCloud Drive via Files app, open the file from your laptop's Files app
to AirDrop it, upload there. No accounts, no APIs.

## Deploy to GitHub Pages

1. The repo includes `.github/workflows/pages.yml` — pushes to `main`
   that touch `static/`, `data/`, or `build_static.py` auto-deploy.
2. In GitHub repo settings → **Pages** → Source: **GitHub Actions**.
3. First push triggers the workflow. The URL is shown in the workflow
   summary (typically `https://<user>.github.io/sadhana-setu/`).

## Editing content

1. Edit any `data/*.yaml` file.
2. Run `python build_static.py` locally if you want to preview.
3. Push to `main`. The Actions workflow rebuilds and redeploys.

## What's not (yet) in the static version

- **Pattern engine** (M5) — the statistics module isn't ported to JS yet.
  Saturday Check-in shows the form but not the surfaced pattern card.
- **History view** — query/filter UI isn't built. The data is all in
  localStorage; you can `console.log(JSON.parse(localStorage.getItem("sadhana_setu_v1")))`
  to inspect it directly until then.
- **Multi-device live sync** — by design. The backup/restore flow is the
  multi-device story.
- **kg-mcp Sanskrit enrichment** — the verse retrieval depends on the
  knowledge graph running on your laptop. The static deploy can't reach
  it.

## Adding multi-device sync later (when you want it)

The data-merge logic in `static/js/store.js` (`importAll`) is identical
to the Python merge in `sadhana_setu/sync/gdrive.py`. So adding a
"sync to JSONbin" or "sync to a personal Gist" later is ~50 LOC of
extra UI without changing the storage model. The backup file IS the
sync wire format.
