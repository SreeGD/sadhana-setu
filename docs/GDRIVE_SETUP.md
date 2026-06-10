# Google Drive Sync — One-Time Setup

The app uses **OAuth 2.0 with the `drive.file` scope**, which means the app
can only see files it created (your `Sadhana Setu/` folder), nothing else
in your Drive. Tokens live on your machine, not in any cloud.

## 1. Create a Google Cloud project

1. Open <https://console.cloud.google.com/>
2. Click the project picker (top bar) → **New Project**
3. Name: `Sadhana Setu` · Location: No organization → **Create**
4. After creation, make sure the new project is selected in the picker.

## 2. Enable the Drive API

1. Left nav → **APIs & Services → Library**
2. Search for "Google Drive API" → **Enable**

## 3. Configure the OAuth consent screen

1. Left nav → **APIs & Services → OAuth consent screen**
2. User Type: **External** → Create
3. App information:
   - App name: `Sadhana Setu`
   - User support email: your Gmail
   - Developer contact: your Gmail
   - Leave logo, domains, etc. empty
4. **Save and Continue** through Scopes (no changes needed)
5. **Test users** → Add Users → add your own Gmail → Save and Continue
6. Back to dashboard.

## 4. Create the OAuth client ID

1. Left nav → **APIs & Services → Credentials**
2. **+ Create Credentials → OAuth client ID**
3. Application type: **Web application**
4. Name: `Sadhana Setu (local)`
5. **Authorized redirect URIs** — add exactly:
   - `http://localhost:8501/`
   - (later, if you deploy: add `https://<your-app>.streamlit.app/`)
6. **Create**
7. Download the JSON.

## 5. Drop the JSON in place

Rename the downloaded file to `google_oauth.json` and move it into the
repo's `.streamlit/` directory:

```
.streamlit/google_oauth.json
```

(This file is in `.gitignore` — it won't be committed.)

## 6. Restart Streamlit and connect

1. `streamlit run sadhana_setu/ui/app.py`
2. In the sidebar, under **Google Drive**, click **Connect Drive**
3. Google's consent screen opens. You'll see a "Google hasn't verified this
   app" warning because the app is in test mode — click **Advanced → Go to
   Sadhana Setu (unsafe)**. This is expected for a personal app; you're
   the test user.
4. Approve the `drive.file` scope.
5. You'll be redirected back to `http://localhost:8501/?code=…`. The
   sidebar will say **Connected**.

## 7. Verify

In the sidebar click **Sync now**. The app should:

- Create `Sadhana Setu/` in your Drive (visible in <https://drive.google.com>)
- Upload `tracker_daily.json` and `tracker_weekly.json`
- Show `Last pull: just now · Last push: just now`

Open <https://drive.google.com>, find the folder, open one of the JSONs —
it will mirror your SQLite tracker tables.

## Day-to-day behaviour

- **App start:** auto-pulls once per session (silent — won't interrupt you).
- **Saturday check-in submit:** auto-pushes after save.
- **Sidebar "Sync now":** pull + push at any time.
- **Sidebar "Disconnect":** removes the local token. Drive files stay.

## Troubleshooting

- **"Google hasn't verified this app"** — expected for unpublished apps.
  As the test user you can proceed via Advanced.
- **"redirect_uri_mismatch"** — the URI in step 4 must match exactly,
  including the trailing slash and `http` vs `https`.
- **"Token has been expired or revoked"** — click Disconnect then
  Connect Drive again.
- **Two devices, conflicting edits in the same week** — last-write-wins
  at the row level, not the file level. The newer `captured_at` /
  `submitted_at` wins for that row.

## Privacy

- Scope is `drive.file` — the app cannot list, read, or touch files it
  didn't create.
- Tokens never leave your machine.
- Drive files are private to your account.
- Disconnecting just deletes the local token; you can also revoke the
  app's access at <https://myaccount.google.com/permissions>.
