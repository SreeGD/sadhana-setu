"""Sidebar: Sign in with Google + Sync — driven by st.secrets, not per-user files."""
from __future__ import annotations

from datetime import datetime, timedelta

import streamlit as st

from sadhana_setu import sync

_SESSION_CREDS_KEY = "_gdrive_creds_json"
_SESSION_EMAIL_KEY = "_gdrive_email"
_SESSION_DID_PULL = "_gdrive_did_pull"


def _relative(ts: str | None) -> str:
    if not ts:
        return "never"
    try:
        when = datetime.fromisoformat(ts)
    except ValueError:
        return ts
    delta = datetime.now() - when
    if delta < timedelta(minutes=1):
        return "just now"
    if delta < timedelta(hours=1):
        return f"{int(delta.total_seconds() // 60)} min ago"
    if delta < timedelta(days=1):
        return f"{int(delta.total_seconds() // 3600)} h ago"
    return when.strftime("%b %d %H:%M")


def _read_secrets() -> tuple[dict | None, str | None]:
    """Return (client_config, redirect_uri) or (None, None) if not configured."""
    try:
        section = st.secrets.get("google_oauth")
    except (AttributeError, KeyError, FileNotFoundError):
        return None, None
    if not section:
        return None, None
    cid = section.get("client_id")
    csec = section.get("client_secret")
    redirect = section.get("redirect_uri") or "http://localhost:8501/"
    if not cid or not csec:
        return None, None
    return sync.build_client_config(cid, csec, redirect), redirect


def _load_creds():
    blob = st.session_state.get(_SESSION_CREDS_KEY)
    if not blob:
        return None
    try:
        return sync.credentials_from_json(blob)
    except Exception:  # noqa: BLE001
        st.session_state.pop(_SESSION_CREDS_KEY, None)
        return None


def _store_creds(creds) -> None:
    st.session_state[_SESSION_CREDS_KEY] = sync.credentials_to_json(creds)


def _signed_in() -> bool:
    return _SESSION_CREDS_KEY in st.session_state


def _auto_pull_once(creds) -> None:
    if st.session_state.get(_SESSION_DID_PULL):
        return
    try:
        sync.pull(creds)
        if sync.refresh_if_needed(creds):
            _store_creds(creds)
    except Exception as e:  # noqa: BLE001
        st.session_state["_sync_last_error"] = f"auto-pull: {e}"
    st.session_state[_SESSION_DID_PULL] = True


def get_active_credentials():
    """Used by other UI views (e.g. saturday auto-push) to get the active creds."""
    return _load_creds() if _signed_in() else None


def render() -> None:
    st.markdown("---")
    st.caption("**Google Drive**")

    if not sync.is_available():
        st.caption(
            "_Install:_\n"
            "`pip install google-auth google-auth-oauthlib google-api-python-client`"
        )
        return

    client_config, redirect_uri = _read_secrets()
    if not client_config:
        st.caption(
            "_Not configured. See `docs/GDRIVE_SETUP.md` — developer adds "
            "`google_oauth` block to `.streamlit/secrets.toml`._"
        )
        return

    # OAuth callback handler — Google redirects back to redirect_uri?code=...
    code = st.query_params.get("code")
    if code and not _signed_in():
        try:
            creds = sync.finalize_oauth(client_config, redirect_uri, code)
            _store_creds(creds)
            email = sync.user_email(creds)
            if email:
                st.session_state[_SESSION_EMAIL_KEY] = email
            st.query_params.clear()
            st.success("Signed in.")
        except Exception as e:  # noqa: BLE001
            st.error(f"Sign-in failed: {e}")

    if not _signed_in():
        try:
            url = sync.start_oauth(client_config, redirect_uri)
            st.link_button(
                "Sign in with Google", url, use_container_width=True, type="primary"
            )
        except Exception as e:  # noqa: BLE001
            st.error(str(e))
        return

    creds = _load_creds()
    if creds is None:
        # session was cleared between checks; force re-signin
        return

    _auto_pull_once(creds)

    email = st.session_state.get(_SESSION_EMAIL_KEY)
    if email:
        st.caption(f"✓ {email}")

    s = sync.status()
    st.caption(f"Last pull: {_relative(s.last_pull)}")
    st.caption(f"Last push: {_relative(s.last_push)}")

    if st.button("Sync now", use_container_width=True):
        try:
            d_in, w_in = sync.pull(creds)
            d_out, w_out = sync.push(creds)
            if sync.refresh_if_needed(creds):
                _store_creds(creds)
            st.success(
                f"Pulled {d_in + w_in} new rows · pushed daily ({d_out}) + weekly ({w_out})."
            )
        except Exception as e:  # noqa: BLE001
            st.error(f"Sync failed: {e}")

    if st.button("Sign out", use_container_width=True):
        for k in (_SESSION_CREDS_KEY, _SESSION_EMAIL_KEY, _SESSION_DID_PULL):
            st.session_state.pop(k, None)
        st.rerun()

    err = st.session_state.get("_sync_last_error")
    if err:
        st.caption(f"_{err}_")
