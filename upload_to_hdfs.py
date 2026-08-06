#!/usr/bin/env python3
"""
upload_to_hdfs.py
Uploads the sample ticket-reservation data (events.csv, users.csv, seats.json)
from local disk into HDFS under /data/, using WebHDFS.

Usage:
    python3 upload_to_hdfs.py --namenode http://localhost:9870 --local-dir ./data
"""

import argparse
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


# Files we expect to upload, and the HDFS path they should land at.
FILES_TO_UPLOAD = {
    "events.csv": "/data/events.csv",
    "users.csv": "/data/users.csv",
    "seats.json": "/data/seats.json",
}


def upload_files(client: InsecureClient, local_dir: str) -> None:
    missing_files = [
        os.path.join(local_dir, filename)
        for filename in FILES_TO_UPLOAD
        if not os.path.isfile(os.path.join(local_dir, filename))
    ]
    if missing_files:
        missing = "\n  - ".join(missing_files)
        raise FileNotFoundError(f"Required sample data file(s) missing:\n  - {missing}")

    # Make sure the target directory exists in HDFS.
    client.makedirs("/data")

    for filename, hdfs_path in FILES_TO_UPLOAD.items():
        local_path = os.path.join(local_dir, filename)

        print(f"[UPLOAD] {local_path} -> {hdfs_path}")
        # overwrite=True so the script is safely re-runnable
        client.upload(hdfs_path, local_path, overwrite=True)

        # Basic sanity check: file exists and has non-zero size on HDFS
        status = client.status(hdfs_path)
        local_size = os.path.getsize(local_path)
        hdfs_size = status["length"]

        if local_size != hdfs_size:
            raise ValueError(
                f"Size mismatch for {filename}: "
                f"local={local_size} bytes, hdfs={hdfs_size} bytes"
            )

        print(f"[OK] {filename} uploaded successfully ({hdfs_size} bytes)")


def main():
    parser = argparse.ArgumentParser(description="Upload sample data to HDFS.")
    parser.add_argument(
        "--namenode",
        default="http://localhost:9870",
        help="WebHDFS URL of the namenode (default: http://localhost:9870)",
    )
    parser.add_argument(
        "--local-dir",
        default="./data",
        help="Local directory containing events.csv, users.csv, seats.json",
    )
    args = parser.parse_args()

    client = InsecureClient(args.namenode, user="root")

    try:
        upload_files(client, args.local_dir)
    except Exception as e:
        print(f"[ERROR] Upload failed: {e}", file=sys.stderr)
        sys.exit(1)

    print("\nDone. Run verify_hdfs.py to confirm the data reads back correctly.")


if __name__ == "__main__":
    main()
