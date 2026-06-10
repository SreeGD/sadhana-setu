"""Cloud-sync subsystem.

GDrive is the only backend implemented today; the package is structured so a
future Dropbox / WebDAV / iCloud backend could slot in beside it.
"""
from sadhana_setu.sync.gdrive import (
    DriveSyncStatus,
    disconnect,
    finalize_oauth,
    is_available,
    is_configured,
    is_connected,
    pull,
    push,
    start_oauth,
    status,
)

__all__ = [
    "DriveSyncStatus",
    "disconnect",
    "finalize_oauth",
    "is_available",
    "is_configured",
    "is_connected",
    "pull",
    "push",
    "start_oauth",
    "status",
]
