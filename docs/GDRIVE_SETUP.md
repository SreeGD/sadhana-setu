# Google Drive Sync — Setup

The developer sets this up **once**. Every user after that just clicks
**Sign in with Google** in the sidebar.

There are two roles in this doc: the **developer** (you, deploying the
app — does the one-time work) and the **end user** (anyone who later
opens the app — does nothing).

---

## End-user experience (after the developer sets up)

1. Open the app
2. Sidebar → **Sign in with Google**
3. Google's consent screen — approve the `drive.file` permission
4. Done. The app pulls/pushes their tracker data to their own Drive at
   `My Drive/Sadhana Setu/`

No JSON files, no Cloud Console, no developer tools. One click.

---

## Developer one-time setup

### 1. Google Cloud project + OAuth client

1. <https://console.cloud.google.com/> → New Project: `Sadhana Setu`
2. **APIs & Services → Library** → enable **Google Drive API**
3. **APIs & Services → OAuth consent screen**:
   - User Type: **External** → Create
   - App name: `Sadhana Setu`
   - Support email + developer contact: your email
   - Add `.../auth/drive.file` and `openid email` scopes
   - **Test users** → add yourself + anyone you want to give access (up
     to 100). For a family-and-devotee-circle app, this is plenty.
4. **APIs & Services → Credentials → + Create Credentials → OAuth client ID**:
   - Application type: **Web application**
   - Name: `Sadhana Setu`
   - Authorized redirect URIs:
     - `http://localhost:8501/` (local dev)
     - `https://<your-app>.streamlit.app/` (production — add after deploy)
   - **Create** → copy the **Client ID** and **Client secret**

### 2. Drop the credentials into Streamlit secrets

Locally:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edit the file, paste your client_id / client_secret
```

Both `secrets.toml` and `secrets.toml.example` are gitignored.

The shape:

```toml
[google_oauth]
client_id = "1234567890-abc...apps.googleusercontent.com"
client_secret = "GOCSPX-..."
redirect_uri = "http://localhost:8501/"
```

### 3. Restart Streamlit

```bash
streamlit run sadhana_setu/ui/app.py
```

Sidebar shows **Sign in with Google**. Click, authorize, you're in.

### 4. Deploy (optional, for inviting others)

#### Streamlit Cloud (recommended — free)

1. Push your `sadhana-setu` repo to GitHub
2. <https://share.streamlit.io> → **New app** → pick the repo + branch
3. Main file: `sadhana_setu/ui/app.py`
4. **Advanced settings → Secrets** → paste the same `[google_oauth]`
   block, but with `redirect_uri = "https://<your-app>.streamlit.app/"`
5. Back in Google Cloud Console → your OAuth client → Authorized
   redirect URIs → add `https://<your-app>.streamlit.app/`
6. Deploy. Share the URL with anyone you've added as a test user.

#### Hugging Face Spaces

Similar — create a Streamlit Space, add the secrets via the UI, add the
HF Space URL to the OAuth client's redirect URIs.

---

## Adding more users (test mode)

While the OAuth client is in "test mode" (the default), only Gmail
addresses you've explicitly added can sign in. To add someone:

1. Cloud Console → APIs & Services → OAuth consent screen
2. Scroll to **Test users** → Add Users → enter their Gmail
3. They can now sign in immediately

Limit: **100 test users.** For a personal/family/small-community app
this is plenty. To go past it, submit for OAuth verification (Google
review, ~3–6 weeks; for `drive.file` it's lightweight).

---

## Day-to-day behaviour

- **Sign in:** one click, opens Google consent in same tab, returns to
  the app
- **App start (after sign-in):** auto-pulls from Drive once per session
- **Saturday check-in submit:** auto-pushes to Drive
- **Sidebar "Sync now":** pull + push
- **Sidebar "Sign out":** clears the session token. Drive files stay.

Token lives in `st.session_state` — not on disk. Sign back in any time
to resume.

---

## Privacy

- Scope is `drive.file` — the app can only see files **it** created
  (your `Sadhana Setu/` folder). Your other Drive files are invisible
  to it.
- Tokens never leave the browser session (cloud) or session_state
  (local). No persistent token files.
- Drive files are private to each user's account.
- Revoke any time at <https://myaccount.google.com/permissions>.

---

## Troubleshooting

- **"Google hasn't verified this app"** — expected in test mode. As a
  test user click **Advanced → Go to Sadhana Setu (unsafe)**. This is
  normal for unverified personal apps.
- **`redirect_uri_mismatch`** — the URI in Cloud Console must match
  exactly, including the trailing `/` and `http` vs `https`.
- **Token expired / invalid** — click **Sign out** then **Sign in
  with Google** again.
- **Multi-device same-week edits** — last-write-wins at the row level
  (per date / per week_start), not the whole file. So phone + laptop
  edits in different days, or even different fields of the same week
  if `submitted_at` differs by one second, both reconcile cleanly.
- **Streamlit Cloud SQLite resets** — yes, the local SQLite is
  ephemeral on Streamlit Cloud. Drive is the source of truth in that
  deployment: auto-pull-on-sign-in restores everything, auto-push
  saves it again. For local dev, the SQLite persists normally.
