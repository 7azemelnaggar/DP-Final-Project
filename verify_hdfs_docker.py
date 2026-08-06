#!/usr/bin/env python3
"""
verify_hdfs_docker.py
Reads events.csv, users.csv, seats.json back from HDFS via `docker exec`
(using the native hdfs CLI inside the namenode container), then verifies:
  - files exist and are non-empty
  - record counts
  - a sample record from each file
  - referential integrity: every seats.event_id matches a real event,
    and every non-null seats.user_id matches a real user

This avoids WebHDFS entirely, so it works even when datanode hostnames
aren't resolvable from the host machine.

Usage:
    python3 verify_hdfs_docker.py --container namenode
"""

import argparse
import csv
import io
import json
import subprocess
import sys


def read_hdfs_file(container: str, hdfs_path: str) -> str:
    """Read a file from HDFS by running `hdfs dfs -cat` inside the container."""
    result = subprocess.run(
        ["docker", "exec", container, "hdfs", "dfs", "-cat", hdfs_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to read {hdfs_path} from container '{container}': "
            f"{result.stderr.strip()}"
        )
    return result.stdout


def verify_events(container: str):
    print("\n--- Verifying /data/events.csv ---")
    content = read_hdfs_file(container, "/data/events.csv")
    rows = list(csv.DictReader(io.StringIO(content)))
    if not rows:
        raise RuntimeError("events.csv read back empty")
    print(f"Record count: {len(rows)}")
    print(f"Sample record: {rows[0]}")
    return {row["event_id"] for row in rows}


def verify_users(container: str):
    print("\n--- Verifying /data/users.csv ---")
    content = read_hdfs_file(container, "/data/users.csv")
    rows = list(csv.DictReader(io.StringIO(content)))
    if not rows:
        raise RuntimeError("users.csv read back empty")
    print(f"Record count: {len(rows)}")
    print(f"Sample record: {rows[0]}")
    return {row["user_id"] for row in rows}


def verify_seats(container: str, event_ids: set, user_ids: set):
    print("\n--- Verifying /data/seats.json ---")
    content = read_hdfs_file(container, "/data/seats.json")
    seats = json.loads(content)
    if not seats:
        raise RuntimeError("seats.json read back empty")
    print(f"Record count: {len(seats)}")
    print(f"Sample record: {seats[0]}")

    bad_event_refs = [s for s in seats if s["event_id"] not in event_ids]
    bad_user_refs = [
        s for s in seats if s["user_id"] is not None and s["user_id"] not in user_ids
    ]

    if bad_event_refs:
        print(f"[WARN] {len(bad_event_refs)} seats reference an unknown event_id:")
        for s in bad_event_refs[:5]:
            print(f"        seat_id={s['seat_id']} event_id={s['event_id']}")
    else:
        print("[OK] All seats.event_id values match a known event")

    if bad_user_refs:
        print(f"[WARN] {len(bad_user_refs)} seats reference an unknown user_id:")
        for s in bad_user_refs[:5]:
            print(f"        seat_id={s['seat_id']} user_id={s['user_id']}")
    else:
        print("[OK] All non-null seats.user_id values match a known user")

    return bad_event_refs, bad_user_refs


def main():
    parser = argparse.ArgumentParser(
        description="Verify HDFS data + referential integrity via docker exec."
    )
    parser.add_argument(
        "--container",
        default="namenode",
        help="Name of the namenode container (default: namenode)",
    )
    args = parser.parse_args()

    try:
        event_ids = verify_events(args.container)
        user_ids = verify_users(args.container)
        bad_event_refs, bad_user_refs = verify_seats(args.container, event_ids, user_ids)
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}", file=sys.stderr)
        sys.exit(1)

    print("\n--- Summary ---")
    if not bad_event_refs and not bad_user_refs:
        print("PASS: all data stored and read back correctly, referential integrity intact.")
    else:
        print("FAIL: referential integrity issues found (see warnings above).")
        sys.exit(1)


if __name__ == "__main__":
    main()
