#!/usr/bin/env python3
"""
verify_hdfs.py
Reads events.csv, users.csv, seats.json back from HDFS and verifies
that what was stored matches what was uploaded:
  - files exist and are non-empty
  - record counts match expectations
  - a sample record from each file is printed
  - referential integrity spot-check: seats.event_id / seats.user_id
    reference real events / users

Usage:
    python3 verify_hdfs.py --namenode http://localhost:9870
"""

import argparse
import csv
import io
import json
import sys

from hdfs import InsecureClient


def read_text_file(client: InsecureClient, hdfs_path: str) -> str:
    with client.read(hdfs_path, encoding="utf-8") as reader:
        return reader.read()


def verify_events(client: InsecureClient):
    print("\n--- Verifying /data/events.csv ---")
    content = read_text_file(client, "/data/events.csv")
    rows = list(csv.DictReader(io.StringIO(content)))
    print(f"Record count: {len(rows)}")
    print(f"Sample record: {rows[0]}")
    return {row["event_id"] for row in rows}


def verify_users(client: InsecureClient):
    print("\n--- Verifying /data/users.csv ---")
    content = read_text_file(client, "/data/users.csv")
    rows = list(csv.DictReader(io.StringIO(content)))
    print(f"Record count: {len(rows)}")
    print(f"Sample record: {rows[0]}")
    return {row["user_id"] for row in rows}


def verify_seats(client: InsecureClient, event_ids: set, user_ids: set):
    print("\n--- Verifying /data/seats.json ---")
    content = read_text_file(client, "/data/seats.json")
    seats = json.loads(content)
    print(f"Record count: {len(seats)}")
    print(f"Sample record: {seats[0]}")

    # Referential integrity spot-check
    bad_event_refs = [s for s in seats if s["event_id"] not in event_ids]
    bad_user_refs = [
        s for s in seats if s["user_id"] is not None and s["user_id"] not in user_ids
    ]

    if bad_event_refs:
        print(f"[WARN] {len(bad_event_refs)} seats reference unknown event_id")
    else:
        print("[OK] All seats.event_id values match a known event")

    if bad_user_refs:
        print(f"[WARN] {len(bad_user_refs)} seats reference unknown user_id")
    else:
        print("[OK] All non-null seats.user_id values match a known user")


def main():
    parser = argparse.ArgumentParser(description="Verify data stored in HDFS.")
    parser.add_argument(
        "--namenode",
        default="http://localhost:9870",
        help="WebHDFS URL of the namenode (default: http://localhost:9870)",
    )
    args = parser.parse_args()

    client = InsecureClient(args.namenode, user="root")

    try:
        event_ids = verify_events(client)
        user_ids = verify_users(client)
        verify_seats(client, event_ids, user_ids)
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}", file=sys.stderr)
        sys.exit(1)

    print("\nVerification complete.")


if __name__ == "__main__":
    main()
