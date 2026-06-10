# Static-Site Conversion + Tracker Storage — Options

The Streamlit app needs a Python server. If we want a real static deployment
(GitHub Pages, Netlify, Cloudflare Pages, etc.) we need to give up the
server. This doc lays out the realistic paths.

## What's READ-ONLY vs READ-WRITE

| Surface | Read or write? | Static-friendly? |
|---|---|---|
| Affirmation / Faith verse / Inspiration / Tip / Nama-Tattva / Book tip | Read | ✓ (just JSON + a date-picker function) |
| This Week reading / method / story | Read | ✓ |
| Bhajan (Saturday) | Read | ✓ |
| Rounds capture | Write | ✗ (needs storage) |
| Hearing notes | Write | ✗ |
| Saturday check-in | Write | ✗ |
| Pattern engine | Read + compute | ✓ (can run in JS over local data) |

Conclusion: **all content libraries port cleanly to static**. Only the
tracker (rounds, hearing notes, check-ins) needs a storage solution.

---

## Static-conversion options

### S1 — Pre-rendered HTML per day (no JS)
Generate `2026-06-10.html`, `2026-06-11.html`, … via a build step. The
landing page redirects to today's URL.

- **Pros:** Zero JS, fully static, works in any browser
- **Cons:** ~366 files per year, painful to update content, no
  client-side date detection (relies on server-side rendering at build time)
- **Refresh:** Run the build script daily via GitHub Actions cron

### S2 — Client-side JS picker (recommended for reading view)
One `index.html` + `content/*.json` files + a small `app.js` that reads
the browser's date and picks the right entry using day-of-year/ISO-week
math — same as the Python loaders do today.

- **Pros:** Tiny repo, instant updates when you edit a JSON file, daily
  refresh is automatic (the JS just reads `new Date()`)
- **Cons:** Needs JavaScript enabled
- **Refresh:** Zero work — the JS picks today every time the page loads

### S3 — Pre-rendered + JS hybrid
GitHub Actions runs daily, regenerates `index.html` with today's content
baked in. Other pages remain JS-driven.

- **Pros:** First-load speed
- **Cons:** Adds CI complexity for very little benefit

### Recommendation: **S2.**
Smallest, simplest, fully refreshes daily without infrastructure.

---

## Implementation sketch for S2

```
sadhana-setu-static/
├── index.html              # Landing — embeds all views
├── style.css               # The cream + gold palette we already have
├── app.js                  # ~300 lines: date math + render
├── content/
│   ├── affirmations.json
│   ├── faith_verses.json
│   ├── inspirations.json
│   ├── tips.json
│   ├── nama_tattva.json
│   ├── bhajans.json
│   ├── weekly_readings.json
│   ├── japa_methods.json
│   ├── weekly_stories.json
│   ├── book_tips.json
│   └── ekadasi.json
└── tracker/                # See "Tracker Storage Options" below
    └── tracker.js
```

A tiny script converts the YAML libraries to JSON at build time:

```python
import yaml, json, pathlib
for yml in pathlib.Path("data").glob("*.yaml"):
    doc = yaml.safe_load(yml.read_text())
    pathlib.Path(f"static/content/{yml.stem}.json").write_text(json.dumps(doc, ensure_ascii=False))
```

The picker JS mirrors the Python loaders:

```js
function pickForToday(library, fieldName='today') {
    const today = new Date();
    const start = new Date(today.getFullYear(), 0, 0);
    const diff = today - start;
    const dayOfYear = Math.floor(diff / (1000 * 60 * 60 * 24));
    return library[dayOfYear % library.length];
}

function pickForWeek(library) {
    const today = new Date();
    const week = getISOWeek(today);
    return library[week % library.length];
}
```

The view rendering is plain DOM construction. No framework needed for
this scale; vanilla JS is fine. Optional: use Alpine.js or Lit if you
want reactive bindings.

---

## Tracker storage options

The tracker (rounds, hearing notes, weekly check-ins) needs persistent
write storage. In a static site, this means client-side or third-party.

### T1 — Browser localStorage only
All data lives in the browser. The "Today" view's tap-to-record writes
to `localStorage`. Same browser → data persists. Different browser /
device → no data.

- **Pros:** Zero setup, works immediately, fully private
- **Cons:** Single-device. Lost if the browser data is cleared.
- **Backup:** Add "Download backup" button — emits a JSON file the user
  can save. "Restore" button reads a JSON file the user uploads.

### T2 — localStorage + Google Drive manual sync (recommended starter)
Same as T1, plus two buttons:
- **"Backup to Google Drive"** → opens Google Picker, user saves the JSON
  file to their Drive
- **"Restore from Google Drive"** → opens Google Picker, user selects
  the file to load

Uses Google Identity Services + Picker API (browser-side OAuth). No
backend. Requires the user to authorize on first use, then a token is
cached in the browser.

- **Pros:** True cloud backup, multi-device, user owns the data
- **Cons:** Manual sync (user clicks Backup occasionally). Google Cloud
  Console project setup needed once (client ID).
- **Effort:** ~200 lines of JS for the Picker integration

### T3 — Google Drive auto-sync via API
Same as T2 but automatic — every write to localStorage also fires an
upload to Drive in the background.

- **Pros:** Multi-device live sync (sort of — refresh needed)
- **Cons:** Token refresh handling, network errors, edge cases
- **Effort:** ~400 lines of JS + careful state management

### T4 — Google Sheets as the backend
User creates a Google Sheet. App reads/writes rows via the Sheets API.

- **Pros:** User can edit/inspect their data in a familiar spreadsheet
- **Cons:** Schema rigidity, sheet API quirks, slower than Drive file
- **Effort:** similar to T2

### T5 — Personal GitHub Gist
Store the tracker JSON in a private gist on the user's GitHub account.
Requires GitHub OAuth.

- **Pros:** Git history of every save
- **Cons:** GitHub OAuth more involved than Google for non-devs
- **Effort:** Similar to T2

### T6 — Managed Postgres (Neon/Supabase free tier)
Static frontend + a tiny serverless API hitting a managed DB.

- **Pros:** Proper multi-device, real DB
- **Cons:** Stops being "static" — adds infra and a deploy story
- **Effort:** Highest

### Recommendation: **T1 → T2.**
Ship T1 (localStorage + Download/Upload backup) first — it works
immediately with no setup. Add T2 (Google Drive Picker) when you want
true cloud backup. Skip T3-T6 unless you actually need multi-device
auto-sync.

---

## Combined recommended path

1. **Phase 1 — Reading view as static (S2 + T1):**
   Convert all libraries to JSON, build static `index.html` with the
   pre-japa view, This Week view, and Saturday view. Use localStorage
   for the tracker. Add Download/Upload buttons.

2. **Phase 2 — Google Drive backup (T2):**
   Add Picker integration. User can save / restore their tracker file
   to Drive.

3. **Phase 3 — Patterns in JS:**
   Port the M5 pattern engine to JavaScript (the math is small: Spearman
   ρ, Bayes factor, BH-FDR). All computation happens client-side.

4. **Phase 4 — Optional auto-sync:**
   If you want multi-device live updates, layer on auto-sync. Probably
   not worth it for a personal app.

## What about kg-mcp?

Static deployment can't reach `kg-mcp`. The Faith Verse loses live
Sanskrit enrichment, but the curated summary keeps working. The pre-
japa view stays functional. Acceptable for a static deployment.

If you ever want the live enrichment in the cloud, run `kg-mcp` as an
HTTP service on the same host as a small Streamlit/FastAPI app — at
which point you're not static anymore. The two paths (static + Drive
vs. server + DB) genuinely don't combine well; pick one.

## Effort estimate

| Phase | Lines of code | Time |
|---|---|---|
| 1 — Static reading view + localStorage tracker | ~1500 | 1–2 weeks |
| 2 — Google Drive Picker integration | ~250 | 2–3 days |
| 3 — Pattern engine in JS | ~200 | 1 day |
| 4 — Auto-sync | ~400 + careful testing | 3–5 days |

The Phase 1 line count is real — porting Streamlit's views to vanilla
HTML/CSS/JS is a genuine rewrite. The benefit is a deploy story that
works on GitHub Pages with no infrastructure.
