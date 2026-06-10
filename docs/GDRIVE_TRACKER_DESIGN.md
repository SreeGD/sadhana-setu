# Google Drive as the Tracker Store — Design

Goal: persist the daily tracker (rounds, hearing minutes, hearing notes,
tip-done) and the weekly tracker (Saturday check-in) on the user's own
Google Drive, with no backend server. Works whether the app is the
current Streamlit version or the future static version.

## Why GDrive over the alternatives

| Store | User owns? | Multi-device? | Setup | Sync model |
|---|---|---|---|---|
| Browser localStorage | yes (local) | no | none | none |
| **Google Drive (this doc)** | **yes (cloud)** | **yes** | **one-time OAuth** | **last-write-wins per file** |
| Google Sheets | yes | yes | one-time OAuth | row append |
| GitHub Gist | yes | yes | one-time OAuth | git-style |
| Managed Postgres | rented | yes | infra | row-level |

GDrive wins for a personal sadhana app: your data, your account,
familiar interface (you can open the file in Drive directly), no
infrastructure cost, no vendor lock-in (it's just a JSON file).

## File layout in Drive

Recommended single folder, two files:

```
My Drive/
└── Sadhana Setu/
    ├── tracker_daily.json      # one row per day
    ├── tracker_weekly.json     # one row per Saturday check-in
    └── backup_2026-06-10.json  # optional snapshots (manual button)
```

Why two files instead of one master:
- Daily is small per row, grows linearly (~365/year × 100 bytes ≈ 40 KB/year)
- Weekly is small per row, grows slowly (~52/year × 500 bytes ≈ 26 KB/year)
- Patterns engine reads both, writes neither — keeping them separate
  keeps file conflicts contained
- A weekly check-in won't accidentally collide with a daily write

### Schema — `tracker_daily.json`

```json
{
  "version": 1,
  "entries": [
    {
      "date": "2026-06-10",
      "rounds": 16,
      "hearing_minutes": 30,
      "hearing_note": "SB 1.1.1 morning class — Sūta Gosvāmī invocations",
      "tip_id": "samadhaya_mano_hrdi",
      "tip_done": true,
      "block_chant_door": 2,
      "updated_at": "2026-06-10T07:42:00Z"
    }
  ]
}
```

### Schema — `tracker_weekly.json`

```json
{
  "version": 1,
  "entries": [
    {
      "week_start": "2026-06-08",
      "japa_score": 4,
      "hearing_score": 3,
      "morning_score": 4,
      "yoga_score": 2,
      "sleep_score": 4,
      "highlights": "Tuesday and Thursday were attentive throughout",
      "anarthas_noticed": "krodha on Wednesday evening",
      "next_week_sankalpa": "Sleep by 10:30 PM every weekday",
      "updated_at": "2026-06-13T19:10:00Z"
    }
  ]
}
```

## OAuth + Drive integration (Streamlit version)

For the current Streamlit app, two clean options:

### Option A — Google service account (server-side)
The Streamlit app authenticates as a service account, writes to a
Drive folder shared with the user.
- Pro: simplest auth
- Con: NOT the user's personal Drive — it's the service account's
  Drive that you share with your account. Doesn't really meet the
  "store in user's Drive" goal.

### Option B — OAuth 2.0 user flow (recommended)
The user clicks "Connect Drive" → Streamlit opens a Google consent
screen → user authorizes → app gets a refresh token → stored locally
in `.streamlit/secrets.toml` or a sqlite row.
- Pro: real user-owned data in the user's actual Drive
- Con: one-time OAuth setup in Google Cloud Console

### One-time setup (Option B)

1. Google Cloud Console → New project "Sadhana Setu"
2. Enable Google Drive API
3. OAuth consent screen → External → add your email as test user
4. Credentials → Create OAuth client ID → Web application
   - Authorized redirect URI: `http://localhost:8501/` (dev),
     `https://your-streamlit-cloud-url/` (prod)
5. Download client_id.json → place in `.streamlit/google_oauth.json`

### Streamlit integration (sketch)

```python
# sadhana_setu/db/gdrive_sync.py
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import json, pathlib, streamlit as st

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
TOKEN_PATH = pathlib.Path("data/google_token.json")

def connect():
    if TOKEN_PATH.exists():
        return Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    flow = Flow.from_client_secrets_file(".streamlit/google_oauth.json", SCOPES,
                                          redirect_uri="http://localhost:8501/")
    auth_url, _ = flow.authorization_url(prompt="consent")
    st.markdown(f"[Connect Google Drive]({auth_url})")
    code = st.query_params.get("code")
    if code:
        flow.fetch_token(code=code)
        TOKEN_PATH.write_text(flow.credentials.to_json())
        st.rerun()
    return None

def ensure_folder(creds, name="Sadhana Setu"):
    svc = build("drive", "v3", credentials=creds)
    q = f"mimeType='application/vnd.google-apps.folder' and name='{name}'"
    r = svc.files().list(q=q, fields="files(id,name)").execute()
    if r["files"]: return r["files"][0]["id"]
    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    return svc.files().create(body=meta, fields="id").execute()["id"]

def upload_json(creds, folder_id, filename, data: dict):
    svc = build("drive", "v3", credentials=creds)
    media = MediaInMemoryUpload(json.dumps(data, indent=2).encode(),
                                 mimetype="application/json")
    q = f"name='{filename}' and '{folder_id}' in parents"
    r = svc.files().list(q=q, fields="files(id)").execute()
    if r["files"]:
        svc.files().update(fileId=r["files"][0]["id"], media_body=media).execute()
    else:
        meta = {"name": filename, "parents": [folder_id]}
        svc.files().create(body=meta, media_body=media).execute()

def download_json(creds, folder_id, filename):
    svc = build("drive", "v3", credentials=creds)
    q = f"name='{filename}' and '{folder_id}' in parents"
    r = svc.files().list(q=q, fields="files(id)").execute()
    if not r["files"]: return None
    raw = svc.files().get_media(fileId=r["files"][0]["id"]).execute()
    return json.loads(raw.decode())
```

### Sync model — when to push/pull

Three patterns, increasing complexity:

1. **Manual** — Sidebar buttons "Pull from Drive" and "Push to Drive".
   User decides when. No surprises, no merge conflicts.
2. **Pull on open, push on Saturday** — Auto-pull at app start.
   Auto-push on each Saturday check-in submit. Daily edits stay local
   until Saturday consolidates them.
3. **Pull on open, debounced push on every change** — Most "live"
   feel. Risk: API quota burn, conflicts if two devices open at once.

**Recommendation: #2.** Matches the weekly-primary rhythm of the app
(`primary cadence is Saturday`). Saturday is when sync naturally happens;
no need to hammer Drive every time you tap a round.

### Failure handling

- Network down on push → log to local SQLite as "pending sync", retry
  next session. The local DB stays authoritative.
- Token expired → show "Reconnect Drive" button. Don't auto-redirect.
- Drive file conflict (two devices same week) → newer `updated_at` wins
  at the entry level (each daily/weekly entry has its own timestamp,
  so merges happen row-by-row, not file-by-file).

### What stays local

SQLite remains the source of truth on each device. Drive is the
mirror. This is important because:

- The pattern engine needs fast random reads (don't make it depend on
  the network).
- Offline edits must always work.
- Drive is "the home base your devices sync to," not "the database."

The merge algorithm: at pull time, for each row in Drive's entries,
upsert into SQLite by primary key (`date` for daily, `week_start` for
weekly), keeping the row with the later `updated_at`.

## For the future static version

If you go static (HTML+JS on GitHub Pages), the same Drive file layout
works, but the auth uses **Google Identity Services (GIS)** + **Drive
REST API directly from the browser**:

```js
// Load GIS
google.accounts.oauth2.initTokenClient({
  client_id: "YOUR_CLIENT_ID.apps.googleusercontent.com",
  scope: "https://www.googleapis.com/auth/drive.file",
  callback: (resp) => {
    accessToken = resp.access_token;
    syncTracker();
  }
});

// Upload tracker_daily.json
async function uploadDaily(data) {
  const metadata = { name: "tracker_daily.json", parents: [folderId] };
  const body = new FormData();
  body.append("metadata", new Blob([JSON.stringify(metadata)], {type: "application/json"}));
  body.append("file", new Blob([JSON.stringify(data)], {type: "application/json"}));
  await fetch("https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
    { method: "POST", headers: {Authorization: `Bearer ${accessToken}`}, body });
}
```

Same OAuth Client ID works for both Streamlit and the browser flow.
The Google Cloud Console project is shared.

## Effort estimate

| Step | Effort |
|---|---|
| Google Cloud Console + OAuth client | 20 min (one-time) |
| `gdrive_sync.py` module + tests | ~250 lines, half-day |
| Sidebar buttons for pull/push | ~50 lines, hour |
| Saturday auto-push hook | ~30 lines, hour |
| Conflict-merge logic | ~80 lines, 2 hours |

Total: ~1 day of focused work. Lowest-risk option for cloud-backed
personal data with the current Streamlit app.

## Recommendation

1. **Now (Streamlit app):** Implement Option B with sync model #2
   (pull on open, push on Saturday check-in). Manual "Sync now" button
   in the sidebar as escape hatch.
2. **Later (if going static):** Reuse the same Google Cloud project,
   port the auth+upload to GIS + Drive REST in the browser.
3. **Out of scope for now:** Auto-debounced push, Google Sheets,
   service accounts.
