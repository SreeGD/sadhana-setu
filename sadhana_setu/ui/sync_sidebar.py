"""Sidebar panel for Google Drive sync — Connect / Sync now / status / Disconnect."""
from __future__ import annotations

from datetime import datetime, timedelta

import streamlit as st

from sadhana_setu import sync


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


def _auto_pull_once() -> None:
    """Pull at most once per session, only if connected."""
    if not sync.is_connected():
        return
    if st.session_state.get("_did_auto_pull"):
        return
    try:
        sync.pull()
    except Exception as e:  # noqa: BLE001
        st.session_state["_sync_last_error"] = f"auto-pull: {e}"
    st.session_state["_did_auto_pull"] = True


def render() -> None:
    st.markdown("---")
    st.caption("**Google Drive**")

    if not sync.is_available():
        st.caption(
            "_Install:_\n"
            "`pip install google-auth google-auth-oauthlib google-api-python-client`"
        )
        return

    if not sync.is_configured():
        st.caption("_Setup required — see `docs/GDRIVE_SETUP.md`._")
        return

    # OAuth callback: ?code=... lands here after the user authorizes.
    code = st.query_params.get("code")
    if code and not sync.is_connected():
        try:
            sync.finalize_oauth(code)
            st.query_params.clear()
            st.success("Connected to Drive.")
        except Exception as e:  # noqa: BLE001
            st.error(f"Auth failed: {e}")

    _auto_pull_once()

    s = sync.status()
    if not s.connected:
        try:
            url = sync.start_oauth()
            st.link_button("Connect Drive", url, use_container_width=True)
        except Exception as e:  # noqa: BLE001
            st.error(str(e))
        return

    st.caption(f"Last pull: {_relative(s.last_pull)}")
    st.caption(f"Last push: {_relative(s.last_push)}")

    if st.button("Sync now", use_container_width=True):
        try:
            d_in, w_in = sync.pull()
            d_out, w_out = sync.push()
            st.success(
                f"Pulled {d_in + w_in} new rows · pushed daily ({d_out}) + weekly ({w_out})."
            )
        except Exception as e:  # noqa: BLE001
            st.error(f"Sync failed: {e}")

    if st.button("Disconnect", use_container_width=True):
        sync.disconnect()
        st.session_state.pop("_did_auto_pull", None)
        st.rerun()

    err = st.session_state.get("_sync_last_error")
    if err:
        st.caption(f"_{err}_")
