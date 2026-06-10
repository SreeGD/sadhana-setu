"""Google Drive sync for the tracker tables.

Design (see docs/GDRIVE_TRACKER_DESIGN.md):
- One Drive folder, two files: tracker_daily.json, tracker_weekly.json
- OAuth drive.file scope: only files this app creates are visible to it
- SQLite remains source of truth; Drive is the mirror
- Pull on app start; push manually + on Saturday check-in submit
- Row-level merge by primary key, keeping the later updated_at

This module is framework-agnostic. Credentials are passed in by the caller
(the Streamlit UI in this app); token persistence is the caller's job too.
"""
from __future__ import annotations

import io
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from sadhana_setu.db.connection import connect

# Imports are deferred / wrapped so the app still runs if the user
# hasn't installed google-auth yet.
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    _LIBS_OK = True
except ImportError:  # pragma: no cover - exercised in install-checks
    _LIBS_OK = False

SCOPES = ["https://www.googleapis.com/auth/drive.file", "openid", "email"]
FOLDER_NAME = "Sadhana Setu"
DAILY_FILENAME = "tracker_daily.json"
WEEKLY_FILENAME = "tracker_weekly.json"


@dataclass
class DriveSyncStatus:
    available: bool
    last_pull: str | None
    last_push: str | None
    user_email: str | None = None
    last_error: str | None = None


# ---------- client config ----------

def build_client_config(client_id: str, client_secret: str, redirect_uri: str) -> dict:
    """Shape the dict Flow.from_client_config expects."""
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [redirect_uri],
        }
    }


# ---------- availability ----------

def is_available() -> bool:
    """True if the google-* libs are importable."""
    return _LIBS_OK


# ---------- OAuth ----------

def start_oauth(client_config: dict, redirect_uri: str) -> str:
    """Return the URL the user should visit to authorize.

    Caller renders this as a link button.
    """
    _require_libs()
    flow = Flow.from_client_config(
        client_config, scopes=SCOPES, redirect_uri=redirect_uri
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", prompt="consent"
    )
    return auth_url


def finalize_oauth(client_config: dict, redirect_uri: str, code: str):
    """Exchange auth code for credentials. Returns google.oauth2.credentials.Credentials."""
    _require_libs()
    flow = Flow.from_client_config(
        client_config, scopes=SCOPES, redirect_uri=redirect_uri
    )
    flow.fetch_token(code=code)
    return flow.credentials


def credentials_from_json(blob: str):
    """Rehydrate credentials from the JSON the caller persisted in session_state."""
    _require_libs()
    return Credentials.from_authorized_user_info(json.loads(blob), SCOPES)


def credentials_to_json(creds) -> str:
    return creds.to_json()


def refresh_if_needed(creds) -> bool:
    """Returns True if creds were refreshed (caller should re-persist)."""
    _require_libs()
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        return True
    return False


def user_email(creds) -> str | None:
    """Best-effort: pull email from the id_token claims if present."""
    _require_libs()
    try:
        from google.oauth2 import id_token
        from google.auth.transport.requests import Request as _Req
        if not creds.id_token:
            return None
        claims = id_token.verify_oauth2_token(creds.id_token, _Req(), audience=None)
        return claims.get("email")
    except Exception:  # noqa: BLE001
        return None


# ---------- sync ops ----------

def pull(creds) -> tuple[int, int]:
    """Pull both files from Drive, merge into SQLite.

    Returns (daily_rows_applied, weekly_rows_applied).
    """
    svc = _drive_service(creds)
    folder_id = _ensure_folder(svc)
    daily = _download_json(svc, folder_id, DAILY_FILENAME) or {}
    weekly = _download_json(svc, folder_id, WEEKLY_FILENAME) or {}
    applied_d = _merge_daily(daily)
    applied_w = _merge_weekly(weekly)
    _write_meta("last_pull", _now())
    return applied_d, applied_w


def push(creds) -> tuple[int, int]:
    """Push SQLite tracker tables to Drive.

    Returns (daily_rows, weekly_rows) written.
    """
    svc = _drive_service(creds)
    folder_id = _ensure_folder(svc)
    daily_doc = _export_daily()
    weekly_doc = _export_weekly()
    _upload_json(svc, folder_id, DAILY_FILENAME, daily_doc)
    _upload_json(svc, folder_id, WEEKLY_FILENAME, weekly_doc)
    _write_meta("last_push", _now())
    return (
        len(daily_doc["rounds"]) + len(daily_doc["hearing_notes"]),
        len(weekly_doc["checkins"]),
    )


def status() -> DriveSyncStatus:
    return DriveSyncStatus(
        available=is_available(),
        last_pull=_read_meta("last_pull"),
        last_push=_read_meta("last_push"),
    )


# ---------- export ----------

def _export_daily() -> dict[str, Any]:
    with connect() as conn:
        rounds = [dict(r) for r in conn.execute(
            "SELECT date, count, captured_at, note FROM rounds ORDER BY date"
        ).fetchall()]
        notes = [dict(r) for r in conn.execute(
            "SELECT date, source, line, captured_at FROM hearing_notes "
            "ORDER BY date, captured_at"
        ).fetchall()]
    return {"version": 1, "rounds": rounds, "hearing_notes": notes}


def _export_weekly() -> dict[str, Any]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT week_start, survey_answers, tone, mood_bhava, practices, "
            "priorities, tools_needed, surfaced_pattern, submitted_at "
            "FROM weekly_checkins ORDER BY week_start"
        ).fetchall()
    checkins = []
    for r in rows:
        checkins.append({
            "week_start": r["week_start"],
            "survey_answers": _json_loads(r["survey_answers"], []),
            "tone": r["tone"] or "",
            "mood_bhava": r["mood_bhava"] or "",
            "practices": _json_loads(r["practices"], []),
            "priorities": _json_loads(r["priorities"], []),
            "tools_needed": _json_loads(r["tools_needed"], []),
            "surfaced_pattern": r["surfaced_pattern"],
            "submitted_at": r["submitted_at"],
        })
    return {"version": 1, "checkins": checkins}


# ---------- merge (row-level, later updated_at wins) ----------

def merge_daily(local: dict[str, Any], remote: dict[str, Any]) -> dict[str, Any]:
    """Pure merge function — used by tests and by the SQLite-write path."""
    merged_rounds: dict[str, dict] = {r["date"]: r for r in local.get("rounds", [])}
    for r in remote.get("rounds", []):
        existing = merged_rounds.get(r["date"])
        if not existing or (r.get("captured_at") or "") > (existing.get("captured_at") or ""):
            merged_rounds[r["date"]] = r

    seen: set[tuple] = set()
    merged_notes: list[dict] = []
    for n in list(local.get("hearing_notes", [])) + list(remote.get("hearing_notes", [])):
        key = (n.get("date"), n.get("captured_at"), n.get("line"))
        if key in seen:
            continue
        seen.add(key)
        merged_notes.append(n)
    merged_notes.sort(key=lambda n: (n.get("date") or "", n.get("captured_at") or ""))

    return {
        "version": 1,
        "rounds": sorted(merged_rounds.values(), key=lambda r: r["date"]),
        "hearing_notes": merged_notes,
    }


def merge_weekly(local: dict[str, Any], remote: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, dict] = {c["week_start"]: c for c in local.get("checkins", [])}
    for c in remote.get("checkins", []):
        existing = merged.get(c["week_start"])
        if not existing or (c.get("submitted_at") or "") > (existing.get("submitted_at") or ""):
            merged[c["week_start"]] = c
    return {"version": 1, "checkins": sorted(merged.values(), key=lambda c: c["week_start"])}


def _merge_daily(remote: dict[str, Any]) -> int:
    local = _export_daily()
    merged = merge_daily(local, remote)
    return _write_daily(merged, local)


def _merge_weekly(remote: dict[str, Any]) -> int:
    local = _export_weekly()
    merged = merge_weekly(local, remote)
    return _write_weekly(merged, local)


def _write_daily(merged: dict[str, Any], local: dict[str, Any]) -> int:
    local_rounds = {r["date"]: r for r in local["rounds"]}
    local_notes = {(n["date"], n["captured_at"], n["line"]) for n in local["hearing_notes"]}
    applied = 0
    with connect() as conn:
        for r in merged["rounds"]:
            if local_rounds.get(r["date"]) == r:
                continue
            conn.execute(
                """
                INSERT INTO rounds(date, count, captured_at, note)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    count = excluded.count,
                    captured_at = excluded.captured_at,
                    note = excluded.note
                """,
                (r["date"], r["count"], r.get("captured_at"), r.get("note")),
            )
            applied += 1
        for n in merged["hearing_notes"]:
            key = (n["date"], n.get("captured_at"), n["line"])
            if key in local_notes:
                continue
            conn.execute(
                "INSERT INTO hearing_notes(date, source, line, captured_at) "
                "VALUES (?, ?, ?, ?)",
                (n["date"], n.get("source"), n["line"], n.get("captured_at")),
            )
            applied += 1
        conn.commit()
    return applied


def _write_weekly(merged: dict[str, Any], local: dict[str, Any]) -> int:
    local_map = {c["week_start"]: c for c in local["checkins"]}
    applied = 0
    with connect() as conn:
        for c in merged["checkins"]:
            if local_map.get(c["week_start"]) == c:
                continue
            conn.execute(
                """
                INSERT INTO weekly_checkins(
                    week_start, survey_answers, tone, mood_bhava,
                    practices, priorities, tools_needed,
                    surfaced_pattern, submitted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(week_start) DO UPDATE SET
                    survey_answers = excluded.survey_answers,
                    tone = excluded.tone,
                    mood_bhava = excluded.mood_bhava,
                    practices = excluded.practices,
                    priorities = excluded.priorities,
                    tools_needed = excluded.tools_needed,
                    surfaced_pattern = excluded.surfaced_pattern,
                    submitted_at = excluded.submitted_at
                """,
                (
                    c["week_start"],
                    json.dumps(c.get("survey_answers") or [], ensure_ascii=False),
                    c.get("tone") or "",
                    c.get("mood_bhava") or "",
                    json.dumps(c.get("practices") or [], ensure_ascii=False),
                    json.dumps(c.get("priorities") or [], ensure_ascii=False),
                    json.dumps(c.get("tools_needed") or [], ensure_ascii=False),
                    c.get("surfaced_pattern"),
                    c.get("submitted_at") or "",
                ),
            )
            applied += 1
        conn.commit()
    return applied


# ---------- Drive REST ----------

def _drive_service(creds):
    _require_libs()
    refresh_if_needed(creds)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _ensure_folder(svc) -> str:
    q = (
        "mimeType='application/vnd.google-apps.folder' "
        f"and name='{FOLDER_NAME}' and trashed=false"
    )
    r = svc.files().list(q=q, fields="files(id,name)", spaces="drive").execute()
    if r.get("files"):
        return r["files"][0]["id"]
    body = {"name": FOLDER_NAME, "mimeType": "application/vnd.google-apps.folder"}
    return svc.files().create(body=body, fields="id").execute()["id"]


def _find_file(svc, folder_id: str, filename: str) -> str | None:
    q = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
    r = svc.files().list(q=q, fields="files(id)", spaces="drive").execute()
    files = r.get("files") or []
    return files[0]["id"] if files else None


def _download_json(svc, folder_id: str, filename: str) -> dict[str, Any] | None:
    fid = _find_file(svc, folder_id, filename)
    if not fid:
        return None
    raw = svc.files().get_media(fileId=fid).execute()
    try:
        return json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
    except json.JSONDecodeError:
        return None


def _upload_json(svc, folder_id: str, filename: str, data: dict[str, Any]) -> None:
    body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
    media = MediaIoBaseUpload(io.BytesIO(body), mimetype="application/json", resumable=False)
    fid = _find_file(svc, folder_id, filename)
    if fid:
        svc.files().update(fileId=fid, media_body=media).execute()
    else:
        meta = {"name": filename, "parents": [folder_id]}
        svc.files().create(body=meta, media_body=media, fields="id").execute()


# ---------- meta (sync timestamps) ----------

_META_PATH = Path("data/sync_meta.json")


def _read_meta(key: str) -> str | None:
    if not _META_PATH.exists():
        return None
    try:
        return json.loads(_META_PATH.read_text()).get(key)
    except (json.JSONDecodeError, OSError):
        return None


def _write_meta(key: str, value: str) -> None:
    _META_PATH.parent.mkdir(parents=True, exist_ok=True)
    doc = {}
    if _META_PATH.exists():
        try:
            doc = json.loads(_META_PATH.read_text())
        except json.JSONDecodeError:
            doc = {}
    doc[key] = value
    _META_PATH.write_text(json.dumps(doc, indent=2))


# ---------- helpers ----------

def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _require_libs() -> None:
    if not _LIBS_OK:
        raise RuntimeError(
            "Google libraries not installed. Run: pip install google-auth "
            "google-auth-oauthlib google-api-python-client"
        )


def _json_loads(s: str | None, default):
    if not s:
        return default
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return default
