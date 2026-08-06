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
import hashlib
import io
import json
import os
import sys

try:
    from hdfs import InsecureClient
except ImportError:
    print(
        "[ERROR] Missing dependency: install requirements with "
        "`python -m pip install -r requirements.txt`.",
        file=sys.stderr,
    )
    sys.exit(1)


EXPECTED_FILES = {
    "events.csv": "/data/events.csv",
    "users.csv": "/data/users.csv",
    "seats.json": "/data/seats.json",
}

EXPECTED_COUNTS = {
    "events.csv": 10,
    "users.csv": 15,
    "seats.json": 60,
}


def read_text_file(client: InsecureClient, hdfs_path: str) -> str:
    with client.read(hdfs_path, encoding="utf-8") as reader:
        return reader.read()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def compare_with_local(filename: str, hdfs_content: str, local_dir: str) -> None:
    local_path = os.path.join(local_dir, filename)
    if not os.path.isfile(local_path):
        raise FileNotFoundError(f"Local comparison file missing: {local_path}")

    with open(local_path, "r", encoding="utf-8") as local_file:
        local_content = local_file.read()

    if sha256_text(local_content) != sha256_text(hdfs_content):
        raise ValueError(f"HDFS content does not match local file: {filename}")

    print(f"[OK] {filename} matches the local source file")


def require_count(filename: str, actual_count: int) -> None:
    expected_count = EXPECTED_COUNTS[filename]
    if actual_count != expected_count:
        raise ValueError(
            f"{filename} record count mismatch: "
            f"expected={expected_count}, actual={actual_count}"
        )

    print(f"[OK] {filename} record count is {actual_count}")


def verify_events(client: InsecureClient, local_dir: str):
    print("\n--- Verifying /data/events.csv ---")
    content = read_text_file(client, EXPECTED_FILES["events.csv"])
    compare_with_local("events.csv", content, local_dir)
    rows = list(csv.DictReader(io.StringIO(content)))
    if not rows:
        raise ValueError("events.csv is empty or has no data rows")
    require_count("events.csv", len(rows))
    print(f"Sample record: {rows[0]}")
    return {row["event_id"] for row in rows}


def verify_users(client: InsecureClient, local_dir: str):
    print("\n--- Verifying /data/users.csv ---")
    content = read_text_file(client, EXPECTED_FILES["users.csv"])
    compare_with_local("users.csv", content, local_dir)
    rows = list(csv.DictReader(io.StringIO(content)))
    if not rows:
        raise ValueError("users.csv is empty or has no data rows")
    require_count("users.csv", len(rows))
    print(f"Sample record: {rows[0]}")
    return {row["user_id"] for row in rows}


def verify_seats(client: InsecureClient, local_dir: str, event_ids: set, user_ids: set):
    print("\n--- Verifying /data/seats.json ---")
    content = read_text_file(client, EXPECTED_FILES["seats.json"])
    compare_with_local("seats.json", content, local_dir)
    seats = json.loads(content)
    if not seats:
        raise ValueError("seats.json is empty or has no records")
    require_count("seats.json", len(seats))
    print(f"Sample record: {seats[0]}")

    bad_event_refs = [s for s in seats if s["event_id"] not in event_ids]
    bad_user_refs = [
        s for s in seats if s["user_id"] is not None and s["user_id"] not in user_ids
    ]
    booked_without_user = [
        s for s in seats if s["status"] == "booked" and s["user_id"] is None
    ]
    available_with_user = [
        s for s in seats if s["status"] == "available" and s["user_id"] is not None
    ]

    if bad_event_refs:
        raise ValueError(f"{len(bad_event_refs)} seats reference unknown event_id")
    print("[OK] All seats.event_id values match a known event")

    if bad_user_refs:
        raise ValueError(f"{len(bad_user_refs)} seats reference unknown user_id")
    print("[OK] All non-null seats.user_id values match a known user")

    if booked_without_user:
        raise ValueError(f"{len(booked_without_user)} booked seats have no user_id")
    print("[OK] Every booked seat has a user_id")

    if available_with_user:
        raise ValueError(f"{len(available_with_user)} available seats have a user_id")
    print("[OK] Every available seat has a null user_id")


def main():
    parser = argparse.ArgumentParser(description="Verify data stored in HDFS.")
    parser.add_argument(
        "--namenode",
        default="http://localhost:9870",
        help="WebHDFS URL of the namenode (default: http://localhost:9870)",
    )
    parser.add_argument(
        "--local-dir",
        default="./data",
        help="Local directory used for exact HDFS-vs-local comparison",
    )
    args = parser.parse_args()

    client = InsecureClient(args.namenode, user="root")

    try:
        event_ids = verify_events(client, args.local_dir)
        user_ids = verify_users(client, args.local_dir)
        verify_seats(client, args.local_dir, event_ids, user_ids)
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}", file=sys.stderr)
        sys.exit(1)

    print("\nVerification complete.")


if __name__ == "__main__":
    main()
