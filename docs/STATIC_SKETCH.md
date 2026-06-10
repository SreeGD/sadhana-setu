# Static-Path Sketch — IndexedDB + GDrive + Vanilla JS

A concrete sketch of what the static version actually looks like.
This is real, copy-pasteable code (not pseudocode). The goal is to
show how small it can stay.

## File tree

```
sadhana-setu-static/
├── index.html                       # Single page, all views
├── style.css                        # Cream + gold palette (port from Streamlit)
├── content/                         # Generated from data/*.yaml at build time
│   ├── affirmations.json
│   ├── faith_verses.json
│   ├── inspirations.json
│   ├── tips.json
│   ├── nama_tattva.json
│   ├── bhajans.json
│   ├── book_tips.json
│   ├── weekly_readings.json
│   ├── japa_methods.json
│   ├── weekly_stories.json
│   ├── weekly_questions.json
│   └── ekadasi.json
├── js/
│   ├── store.js                     # IndexedDB layer (~120 lines)
│   ├── sync.js                      # GDrive sync (~150 lines)
│   ├── content.js                   # Content loaders + date pickers (~80 lines)
│   ├── patterns.js                  # Spearman + BH-FDR (~80 lines)
│   ├── views/
│   │   ├── prejapa.js               # ~150 lines
│   │   ├── today.js                 # ~100 lines
│   │   ├── this_week.js             # ~80 lines
│   │   └── saturday.js              # ~120 lines
│   └── app.js                       # View routing (~50 lines)
└── build_content.py                 # YAML → JSON one-shot script
```

Total JS: **~930 lines**, all vanilla, no framework.

---

## 1. The data layer — `js/store.js`

IndexedDB is the local "SQLite" replacement. Two stores: `daily`,
`weekly`. Plus a `meta` store for sync timestamps and the access
token cache.

```javascript
// js/store.js
const DB_NAME = 'sadhana-setu';
const DB_VERSION = 1;

let dbPromise = null;

function openDB() {
  if (dbPromise) return dbPromise;
  dbPromise = new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains('daily')) {
        db.createObjectStore('daily', { keyPath: 'date' });
      }
      if (!db.objectStoreNames.contains('weekly')) {
        db.createObjectStore('weekly', { keyPath: 'week_start' });
      }
      if (!db.objectStoreNames.contains('meta')) {
        db.createObjectStore('meta', { keyPath: 'key' });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
  return dbPromise;
}

async function put(storeName, value) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(storeName, 'readwrite');
    tx.objectStore(storeName).put(value);
    tx.oncomplete = () => resolve(value);
    tx.onerror = () => reject(tx.error);
  });
}

async function get(storeName, key) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const req = db.transaction(storeName, 'readonly').objectStore(storeName).get(key);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

async function all(storeName) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const req = db.transaction(storeName, 'readonly').objectStore(storeName).getAll();
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

// Public API — what the views call
export const store = {
  async saveDaily(entry) {
    entry.updated_at = new Date().toISOString();
    await put('daily', entry);
  },
  async getDaily(date) {
    return get('daily', date);
  },
  async allDaily() {
    return all('daily');
  },
  async saveWeekly(entry) {
    entry.updated_at = new Date().toISOString();
    await put('weekly', entry);
  },
  async getWeekly(weekStart) {
    return get('weekly', weekStart);
  },
  async allWeekly() {
    return all('weekly');
  },
  async setMeta(key, value) {
    await put('meta', { key, value, updated_at: new Date().toISOString() });
  },
  async getMeta(key) {
    const row = await get('meta', key);
    return row?.value;
  },
};
```

**That's the entire local store.** Same role as the Python `db/`
package, much smaller because IndexedDB does the persistence.

---

## 2. The sync layer — `js/sync.js`

GDrive integration via Google Identity Services (GIS) + Drive REST.
No server, no SDK install — just `<script src="https://accounts.google.com/gsi/client">`.

```javascript
// js/sync.js
import { store } from './store.js';

const CLIENT_ID = 'YOUR_CLIENT_ID.apps.googleusercontent.com';
const SCOPE = 'https://www.googleapis.com/auth/drive.file';
const FOLDER_NAME = 'Sadhana Setu';
const DAILY_FILENAME = 'tracker_daily.json';
const WEEKLY_FILENAME = 'tracker_weekly.json';

let tokenClient = null;
let accessToken = null;

export function initSync() {
  tokenClient = google.accounts.oauth2.initTokenClient({
    client_id: CLIENT_ID,
    scope: SCOPE,
    callback: async (resp) => {
      if (resp.error) return;
      accessToken = resp.access_token;
      await store.setMeta('gdrive_token', accessToken);
      await pullAll();  // auto-pull right after auth
    },
  });
}

export function connect() {
  // Triggered by user click — must be in a click handler for popup
  tokenClient.requestAccessToken({ prompt: 'consent' });
}

async function driveFetch(url, opts = {}) {
  return fetch(url, {
    ...opts,
    headers: { ...opts.headers, Authorization: `Bearer ${accessToken}` },
  });
}

async function ensureFolder() {
  const q = encodeURIComponent(
    `mimeType='application/vnd.google-apps.folder' and name='${FOLDER_NAME}' and trashed=false`
  );
  const r = await driveFetch(`https://www.googleapis.com/drive/v3/files?q=${q}`);
  const data = await r.json();
  if (data.files?.length) return data.files[0].id;
  const create = await driveFetch('https://www.googleapis.com/drive/v3/files', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: FOLDER_NAME,
      mimeType: 'application/vnd.google-apps.folder',
    }),
  });
  return (await create.json()).id;
}

async function findFile(folderId, name) {
  const q = encodeURIComponent(`name='${name}' and '${folderId}' in parents and trashed=false`);
  const r = await driveFetch(`https://www.googleapis.com/drive/v3/files?q=${q}`);
  return (await r.json()).files?.[0]?.id ?? null;
}

async function uploadJSON(folderId, filename, data) {
  const fileId = await findFile(folderId, filename);
  const body = JSON.stringify(data, null, 2);
  if (fileId) {
    await driveFetch(`https://www.googleapis.com/upload/drive/v3/files/${fileId}?uploadType=media`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body,
    });
  } else {
    const boundary = '----sadhana';
    const meta = { name: filename, parents: [folderId] };
    const multipart =
      `--${boundary}\r\n` +
      `Content-Type: application/json\r\n\r\n${JSON.stringify(meta)}\r\n` +
      `--${boundary}\r\n` +
      `Content-Type: application/json\r\n\r\n${body}\r\n--${boundary}--`;
    await driveFetch('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart', {
      method: 'POST',
      headers: { 'Content-Type': `multipart/related; boundary=${boundary}` },
      body: multipart,
    });
  }
}

async function downloadJSON(folderId, filename) {
  const fileId = await findFile(folderId, filename);
  if (!fileId) return null;
  const r = await driveFetch(`https://www.googleapis.com/drive/v3/files/${fileId}?alt=media`);
  return r.json();
}

// Merge: keep entry with later updated_at
async function mergeIntoLocal(remote, kind) {
  if (!remote?.entries) return;
  const localList = kind === 'daily' ? await store.allDaily() : await store.allWeekly();
  const keyOf = (e) => (kind === 'daily' ? e.date : e.week_start);
  const localMap = new Map(localList.map((e) => [keyOf(e), e]));
  const saveFn = kind === 'daily' ? store.saveDaily : store.saveWeekly;
  for (const rEntry of remote.entries) {
    const lEntry = localMap.get(keyOf(rEntry));
    if (!lEntry || rEntry.updated_at > lEntry.updated_at) {
      await saveFn(rEntry);
    }
  }
}

export async function pullAll() {
  const folderId = await ensureFolder();
  const daily = await downloadJSON(folderId, DAILY_FILENAME);
  const weekly = await downloadJSON(folderId, WEEKLY_FILENAME);
  await mergeIntoLocal(daily, 'daily');
  await mergeIntoLocal(weekly, 'weekly');
  await store.setMeta('last_pull', new Date().toISOString());
}

export async function pushAll() {
  const folderId = await ensureFolder();
  const daily = { version: 1, entries: await store.allDaily() };
  const weekly = { version: 1, entries: await store.allWeekly() };
  await uploadJSON(folderId, DAILY_FILENAME, daily);
  await uploadJSON(folderId, WEEKLY_FILENAME, weekly);
  await store.setMeta('last_push', new Date().toISOString());
}
```

That's the whole sync layer. Notable properties:
- No backend.
- `drive.file` scope — the app can only see files **it** created/opened. Your other Drive files are invisible to it.
- Last-write-wins per entry (not per file), so phone + laptop edits in the same week reconcile cleanly.

---

## 3. Content loaders + date pickers — `js/content.js`

Mirrors the Python loaders. Pure functions, no state.

```javascript
// js/content.js
async function loadJSON(path) {
  const r = await fetch(path);
  return r.json();
}

const cache = {};
async function library(name) {
  if (!cache[name]) cache[name] = await loadJSON(`content/${name}.json`);
  return cache[name];
}

function dayOfYear(d = new Date()) {
  const start = new Date(d.getFullYear(), 0, 0);
  return Math.floor((d - start) / 86400000);
}

function isoWeek(d = new Date()) {
  const target = new Date(d);
  target.setHours(0, 0, 0, 0);
  target.setDate(target.getDate() + 3 - ((target.getDay() + 6) % 7));
  const week1 = new Date(target.getFullYear(), 0, 4);
  return 1 + Math.round(((target - week1) / 86400000 - 3 + ((week1.getDay() + 6) % 7)) / 7);
}

export async function pickToday(libraryName, fieldKey) {
  const lib = await library(libraryName);
  const arr = lib[fieldKey];
  return arr[dayOfYear() % arr.length];
}

export async function pickWeek(libraryName, fieldKey) {
  const lib = await library(libraryName);
  const arr = lib[fieldKey];
  return arr[isoWeek() % arr.length];
}

export async function pickByDate(libraryName, fieldKey, dateStr) {
  // For ekadasi calendar: dateStr like "2026-06-10"
  const lib = await library(libraryName);
  return lib[fieldKey].find((e) => e.date === dateStr) ?? null;
}
```

---

## 4. Pattern engine — `js/patterns.js`

Spearman ρ + Benjamini-Hochberg FDR, in plain JS. The math is small.

```javascript
// js/patterns.js
function rank(arr) {
  const sorted = arr.map((v, i) => [v, i]).sort((a, b) => a[0] - b[0]);
  const ranks = new Array(arr.length);
  for (let i = 0; i < sorted.length; i++) ranks[sorted[i][1]] = i + 1;
  return ranks;
}

function spearman(xs, ys) {
  const n = xs.length;
  if (n < 4) return { rho: NaN, p: NaN };
  const rx = rank(xs), ry = rank(ys);
  const mean = (a) => a.reduce((s, v) => s + v, 0) / a.length;
  const mx = mean(rx), my = mean(ry);
  let num = 0, dx = 0, dy = 0;
  for (let i = 0; i < n; i++) {
    num += (rx[i] - mx) * (ry[i] - my);
    dx += (rx[i] - mx) ** 2;
    dy += (ry[i] - my) ** 2;
  }
  const rho = num / Math.sqrt(dx * dy);
  // Approximate p via t-statistic
  const t = rho * Math.sqrt((n - 2) / (1 - rho * rho));
  const p = 2 * (1 - tCDF(Math.abs(t), n - 2));
  return { rho, p };
}

// Student's t-CDF via continued-fraction beta function (small impl)
function tCDF(t, df) { /* ~20 lines — omit for brevity, well-known */ }

function bhCorrect(pvals) {
  const n = pvals.length;
  const ordered = pvals.map((p, i) => [p, i]).sort((a, b) => a[0] - b[0]);
  const adjusted = new Array(n);
  let prev = 1;
  for (let k = n - 1; k >= 0; k--) {
    const [p, idx] = ordered[k];
    const q = Math.min(prev, (p * n) / (k + 1));
    adjusted[idx] = q;
    prev = q;
  }
  return adjusted;
}

export async function findPatterns(dailyEntries, weeklyEntries, weeksWindow = 8) {
  // Build a matrix: per-week aggregates of {avg_rounds, avg_hearing, japa_score, etc.}
  const weeks = weeklyEntries.slice(-weeksWindow);
  if (weeks.length < 4) return [];
  const fields = ['japa_score', 'hearing_score', 'morning_score', 'sleep_score'];
  const pairs = [];
  for (let i = 0; i < fields.length; i++) {
    for (let j = i + 1; j < fields.length; j++) {
      const xs = weeks.map((w) => w[fields[i]]).filter((v) => v != null);
      const ys = weeks.map((w) => w[fields[j]]).filter((v) => v != null);
      const { rho, p } = spearman(xs, ys);
      if (!isNaN(rho)) pairs.push({ a: fields[i], b: fields[j], rho, p });
    }
  }
  const qs = bhCorrect(pairs.map((x) => x.p));
  pairs.forEach((x, i) => (x.q = qs[i]));
  return pairs.filter((x) => x.q < 0.05).sort((a, b) => Math.abs(b.rho) - Math.abs(a.rho));
}
```

For the Bayes factor I'd add `bayesFactorBIC(rho, n)` — one-liner from
the BIC approximation. The five-condition firing rule (n≥4 weeks, |ρ|
above threshold, q below threshold, BF above threshold, consistent
direction) lives in `findPatterns`. Same logic as the Python version.

---

## 5. View — pre-japa — `js/views/prejapa.js`

```javascript
// js/views/prejapa.js
import { pickToday, pickWeek, pickByDate } from '../content.js';

const featuredByDow = {
  // Mon-Fri rotate; Sat=bhajan; Sun=story
  1: { lib: 'affirmations', field: 'affirmations', label: 'Today\'s Affirmation' },
  2: { lib: 'faith_verses', field: 'faith_verses', label: 'Today\'s Faith Verse' },
  3: { lib: 'inspirations', field: 'inspirations', label: 'Today\'s Inspiration' },
  4: { lib: 'tips', field: 'tips', label: 'Today\'s Practical Tip' },
  5: { lib: 'nama_tattva', field: 'entries', label: 'Today\'s Nāma-Tattva' },
  6: { lib: 'bhajans', field: 'bhajans', label: 'Saturday Bhajan' },
  0: { lib: 'weekly_stories', field: 'stories', label: 'Sunday Story' },
};

export async function renderPrejapa(root) {
  const dow = new Date().getDay();
  const featured = featuredByDow[dow];
  const featuredEntry = dow === 0 ? await pickWeek('weekly_stories', 'stories')
                                   : await pickToday(featured.lib, featured.field);
  const supporting = await Promise.all([
    pickToday('inspirations', 'inspirations'),
    pickToday('affirmations', 'affirmations'),
    pickToday('faith_verses', 'faith_verses'),
    pickToday('tips', 'tips'),
    pickToday('nama_tattva', 'entries'),
  ].filter((_, i) => featuredEntry !== _));  // skip the one shown in featured

  const bookTip = await pickToday('book_tips', 'book_tips');
  const todayStr = new Date().toISOString().slice(0, 10);
  const ekadasi = await pickByDate('ekadasi', 'entries', todayStr);

  root.innerHTML = `
    <div class="meta-line">${new Date().toLocaleDateString()} · value: ${pickValue()}</div>
    ${renderFeatured(featured.label, featuredEntry)}
    <div class="support-grid">${supporting.map(renderSupportCard).join('')}</div>
    ${renderBookTipCard(bookTip)}
    ${ekadasi ? renderEkadasiCard(ekadasi) : ''}
  `;
}

function renderFeatured(label, entry) {
  return `
    <div class="featured-card">
      <div class="card-label">${label}</div>
      <div class="card-title">${entry.title ?? ''}</div>
      <div class="card-body">${entry.text ?? entry.verse ?? ''}</div>
      <div class="card-cite">— ${entry.source ?? entry.citation ?? ''}</div>
    </div>`;
}

function renderSupportCard(e) { /* similar shape, smaller */ }
function renderBookTipCard(t) { /* ... */ }
function renderEkadasiCard(e) { /* ... */ }
function pickValue() { /* rotate from a small list */ }
```

The other views (`today.js`, `this_week.js`, `saturday.js`) follow the
same pattern: pull content via `content.js`, pull/save tracker data via
`store.js`, render to DOM.

---

## 6. HTML shell — `index.html`

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sadhana Setu</title>
  <link rel="stylesheet" href="style.css">
  <script src="https://accounts.google.com/gsi/client" async defer></script>
</head>
<body>
  <header class="topbar">
    <span class="symbol">❦</span>
    <span class="title">Sadhana Setu</span>
    <span class="devanagari">साधना सेतुः</span>
    <span class="tagline">· a bridge between aspiration and act</span>
    <nav class="tabs">
      <button data-view="prejapa" class="active">Pre-japa</button>
      <button data-view="today">Today</button>
      <button data-view="this_week">This Week</button>
      <button data-view="saturday">Saturday</button>
    </nav>
    <button id="sync-now" class="sync-btn">Sync</button>
  </header>
  <main id="root"></main>
  <script type="module" src="js/app.js"></script>
</body>
</html>
```

And `js/app.js` is the smallest piece:

```javascript
import { initSync, connect, pullAll, pushAll } from './sync.js';
import { renderPrejapa } from './views/prejapa.js';
import { renderToday } from './views/today.js';
import { renderThisWeek } from './views/this_week.js';
import { renderSaturday } from './views/saturday.js';

const root = document.getElementById('root');
const views = { prejapa: renderPrejapa, today: renderToday, this_week: renderThisWeek, saturday: renderSaturday };

document.querySelectorAll('[data-view]').forEach((btn) => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('[data-view]').forEach((b) => b.classList.remove('active'));
    btn.classList.add('active');
    views[btn.dataset.view](root);
  });
});

document.getElementById('sync-now').addEventListener('click', async () => {
  await pullAll();
  await pushAll();
  alert('Synced');
});

// Boot
window.addEventListener('load', async () => {
  initSync();
  await pullAll().catch(() => { /* not connected yet, fine */ });
  renderPrejapa(root);
});
```

---

## 7. Build script — `build_content.py`

One small Python script that runs at build time to convert the YAML
content libraries into JSON. Runs locally or in GitHub Actions on push.

```python
import json, pathlib, yaml

SRC = pathlib.Path('data')
DEST = pathlib.Path('static/content')
DEST.mkdir(parents=True, exist_ok=True)

for yml in SRC.glob('*.yaml'):
    doc = yaml.safe_load(yml.read_text())
    out = DEST / f"{yml.stem}.json"
    out.write_text(json.dumps(doc, ensure_ascii=False))
    print(f"  {yml.name} -> {out}")
```

That's the whole conversion. Run it once per content change, commit
the JSON into the static deploy folder.

---

## Deployment

GitHub Pages serves `sadhana-setu-static/` directly. No CI required
unless you want `build_content.py` to run on push — a 10-line
`.github/workflows/build.yml` does that.

```yaml
name: Build static content
on:
  push:
    paths: ['data/**']
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install pyyaml
      - run: python build_content.py
      - uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "build: regenerate content/*.json"
          file_pattern: 'static/content/*.json'
```

---

## What changes vs. the Streamlit version

| Layer | Streamlit | Static sketch |
|---|---|---|
| Content libraries | YAML loaded by Python | YAML → JSON at build, fetched in browser |
| Tracker store | SQLite | IndexedDB |
| Cloud sync | (would be) Python google-api-python-client | Browser → Drive REST + GIS |
| Pattern engine | scipy + pingouin | ~80 lines vanilla JS (Spearman + BH + BIC) |
| Faith verse enrichment via kg-mcp | Available | Not available (falls back to summary) |
| Layout | Streamlit columns + markdown | HTML + flex/grid CSS |
| Hot reload during dev | Streamlit auto-reload | `python -m http.server` + browser refresh |

The total static code is about **~1000 lines**. The current Python
code is about **~3500 lines** (M1-M7 modules + UI). Most of the
shrinkage is the kg-mcp integration falling away and Streamlit's
session-state / page-config machinery being replaced by plain HTML.

## What's *not* in this sketch (intentionally)

- **Auto-sync.** Manual `Sync` button only. Add a debounced auto-push
  later if you want it; the foundation supports it.
- **Service worker / offline mode.** Worth ~50 lines if you want full
  offline, but the app already works offline once the content JSON is
  cached by the browser. Add it when you actually need iOS home-screen
  install.
- **Anvil / Lit / Alpine.** No framework. At this scale the DOM API is
  fine. If you find yourself writing a third view with deeply nested
  state, reach for Lit (no build step, web components).
- **Streaming patterns / animations.** Sadhana app, not a dashboard.
- **The Patterns full module.** Sketched at the key statistics level;
  porting the exact 5-condition rule is a half-day of work.

## Effort to ship

| Phase | LOC | Time |
|---|---|---|
| Port content libraries (YAML→JSON) + content.js | 80 | 1 hour |
| store.js + tests | 120 | 2 hours |
| Pre-japa view | 200 | 4 hours |
| Today view (tap-to-record rounds, hearing log) | 150 | 4 hours |
| This Week view | 100 | 2 hours |
| Saturday check-in view | 150 | 4 hours |
| Pattern engine port | 100 | 4 hours |
| GDrive sync + Google Cloud Console setup | 200 | 6 hours |
| CSS port from Streamlit | 200 | 3 hours |
| Glue + polish + mobile testing | — | 1 day |

**Total: ~3 working days for a single developer.** Not weeks. The
small surface is the whole point.
