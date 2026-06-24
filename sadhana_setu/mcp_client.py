"""MCP client for the kg-mcp server (vidya-karana-kg).

Async wrapper around the MCP SDK plus sync convenience helpers and a
smoke entry. The synchronous `smoke()` entry validates that the kg-mcp
binary launches, the snapshot loads, and at least two representative
tools return data.
"""
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

KG_MCP_BIN = os.environ.get(
    "KG_MCP_BIN",
    "/Users/sree/Projects/vidya-karana-kg/.venv/bin/kg-mcp",
)


def _kg_mcp_cwd(bin_path: str) -> str:
    """Infer kg-mcp project root from the bin path.

    `/.../vidya-karana-kg/.venv/bin/kg-mcp` -> `/.../vidya-karana-kg`
    kg-mcp's .env uses relative paths (`./data/snapshots`), so it must
    run with its own project root as CWD.
    """
    return str(Path(bin_path).parent.parent.parent)


class KGMCPClient:
    """Async client that spawns kg-mcp over stdio."""

    def __init__(self, bin_path: str | None = None):
        self.bin_path = bin_path or KG_MCP_BIN
        self._stdio_ctx = None
        self._session_ctx = None
        self.session = None

    async def connect(self) -> None:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command=self.bin_path,
            cwd=_kg_mcp_cwd(self.bin_path),
        )
        self._stdio_ctx = stdio_client(params)
        read, write = await self._stdio_ctx.__aenter__()
        self._session_ctx = ClientSession(read, write)
        self.session = await self._session_ctx.__aenter__()
        await self.session.initialize()

    async def close(self) -> None:
        if self._session_ctx is not None:
            await self._session_ctx.__aexit__(None, None, None)
        if self._stdio_ctx is not None:
            await self._stdio_ctx.__aexit__(None, None, None)

    async def call_tool(self, name: str, arguments: dict) -> Any:
        if self.session is None:
            raise RuntimeError("Not connected. Call connect() first.")
        return await self.session.call_tool(name, arguments)


def parse_response(result: Any) -> Any:
    """Extract data from an MCP CallToolResult. Tries structuredContent, then JSON-parses text content."""
    sc = getattr(result, "structuredContent", None)
    if sc:
        return sc
    for item in getattr(result, "content", []) or []:
        text = getattr(item, "text", None)
        if text is None:
            continue
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    return None


def call_tool_sync(name: str, args: dict, bin_path: str | None = None) -> Any:
    """Single-shot synchronous tool call. Spawns kg-mcp, calls one tool, parses, closes."""
    async def _run():
        client = KGMCPClient(bin_path=bin_path)
        try:
            await client.connect()
            result = await client.call_tool(name, args)
            return parse_response(result)
        finally:
            try:
                await client.close()
            except Exception:
                pass
    return asyncio.run(_run())


class _SyncKGSession:
    """A persistent synchronous kg-mcp session.

    Keeps ONE kg-mcp subprocess + loaded graph alive across many tool calls — the connect,
    every call, and the close all run in a single coroutine on a dedicated background loop, so
    the graph (145K+ nodes) loads once instead of per lookup. Use via ``kg_session()``.
    """

    def __init__(self, bin_path: str | None = None):
        self._bin = bin_path
        self._loop = None
        self._thread = None
        self._req: "asyncio.Queue | None" = None
        self._ready = None  # threading.Event
        self._err: Exception | None = None

    def __enter__(self) -> "_SyncKGSession":
        import threading

        self._ready = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready.wait()
        if self._err is not None:
            raise self._err
        return self

    def _run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve())
        finally:
            self._loop.close()

    async def _serve(self) -> None:
        self._req = asyncio.Queue()
        client = KGMCPClient(bin_path=self._bin)
        try:
            await client.connect()
        except Exception as exc:  # noqa: BLE001
            self._err = exc
            self._ready.set()
            return
        self._ready.set()
        while True:
            name, args, done = await self._req.get()
            if name is None:
                break
            try:
                done(("ok", parse_response(await client.call_tool(name, args))))
            except Exception as exc:  # noqa: BLE001
                done(("err", exc))
        try:
            await client.close()
        except Exception:  # noqa: BLE001
            pass

    def call(self, name: str, args: dict):
        import threading

        box: dict = {}
        done_evt = threading.Event()

        def done(val):
            box["v"] = val
            done_evt.set()

        asyncio.run_coroutine_threadsafe(self._req.put((name, args, done)), self._loop)
        done_evt.wait()
        kind, val = box["v"]
        if kind == "err":
            raise val
        return val

    def __exit__(self, *exc) -> None:
        try:
            asyncio.run_coroutine_threadsafe(self._req.put((None, None, None)), self._loop)
        except Exception:  # noqa: BLE001
            pass
        if self._thread is not None:
            self._thread.join(timeout=10)


def kg_session(bin_path: str | None = None) -> _SyncKGSession:
    """Context manager yielding a persistent sync kg-mcp session (one graph load for many calls)."""
    return _SyncKGSession(bin_path)


async def _smoke() -> bool:
    print(f"[smoke] kg-mcp binary: {KG_MCP_BIN}")
    if not os.path.exists(KG_MCP_BIN):
        print(f"[smoke] FAIL: binary not found at {KG_MCP_BIN}.")
        print("[smoke]       Set KG_MCP_BIN in your .env.")
        return False

    client = KGMCPClient()
    try:
        print("[smoke] connecting (allow ~1.5s for snapshot pre-warm)...")
        await client.connect()
        print("[smoke] connected.")

        print("[smoke] calling kg_status()...")
        status = await client.call_tool("kg_status", {})
        print(f"[smoke] kg_status -> {status}")

        print("[smoke] calling get_verse('BG 18.66')...")
        verse = await client.call_tool("get_verse", {"verse_ref": "BG 18.66"})
        print(f"[smoke] get_verse -> {verse}")

        await client.close()
        print("[smoke] OK")
        return True
    except Exception as exc:
        print(f"[smoke] FAIL: {type(exc).__name__}: {exc}")
        return False


def smoke() -> None:
    """Sync entry point. Exits with code 0 on success, 1 on failure."""
    success = asyncio.run(_smoke())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    smoke()
