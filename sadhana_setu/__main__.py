"""CLI entry point for Sadhana Setu.

Usage:
    python -m sadhana_setu smoke       # test kg-mcp connection
    python -m sadhana_setu migrate     # create SQLite tables
    python -m sadhana_setu ekadasi [YYYY-MM-DD]   # lookup ekadasi
"""
import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m sadhana_setu {smoke,migrate,ekadasi}")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "smoke":
        from sadhana_setu.mcp_client import smoke
        smoke()
    elif cmd == "migrate":
        from sadhana_setu.db.schema import migrate
        path = migrate()
        print(f"Migration complete: {path}")
    elif cmd == "ekadasi":
        from sadhana_setu.calendar import main as cal_main
        cal_main(sys.argv[2:])
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
