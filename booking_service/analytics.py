from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

try:
    from hdfs import InsecureClient
except Exception:  # pragma: no cover - optional for local-only use
    InsecureClient = None


HDFS_URL = os.getenv("BOOKING_HDFS_URL", "http://localhost:9870")
HDFS_USER = os.getenv("BOOKING_HDFS_USER", "root")
HDFS_OUTPUT_ROOT = os.getenv("BOOKING_HDFS_OUTPUT_ROOT", "/data/output/member1")
HDFS_TIMEOUT = float(os.getenv("BOOKING_HDFS_TIMEOUT", "2"))
HDFS_ENABLED = os.getenv("BOOKING_HDFS_ENABLED", "1") != "0"
HDFS_READ_MODE = os.getenv("BOOKING_HDFS_READ_MODE", "auto")
DOCKER_HDFS_CONTAINER = os.getenv("BOOKING_DOCKER_HDFS_CONTAINER", "namenode")

JOB_COLUMNS = {
    "job1_bookings_per_event": ["event_id", "total_bookings"],
    "job2_revenue_per_event": ["event_id", "event_name", "total_revenue", "total_bookings"],
    "job3_occupancy_per_event": [
        "event_id",
        "event_name",
        "booked_seats",
        "total_seats",
        "occupancy_percentage",
    ],
    "job4_available_seats_per_event": [
        "event_id",
        "event_name",
        "total_seats",
        "booked_seats",
        "available_seats",
    ],
    "job5_top5_events": ["rank", "event_id", "event_name", "total_bookings"],
    "job6_stats_by_category": [
        "category",
        "total_bookings",
        "total_revenue",
        "average_booking_price",
    ],
    "job7_stats_by_date": [
        "event_date",
        "total_bookings",
        "total_revenue",
        "average_booking_price",
    ],
    "job8_top5_users": ["rank", "user_id", "user_name", "total_bookings"],
}


@dataclass
class JobOutputReader:
    output_root: str = HDFS_OUTPUT_ROOT
    hdfs_url: str = HDFS_URL
    hdfs_user: str = HDFS_USER
    hdfs_timeout: float = HDFS_TIMEOUT
    hdfs_enabled: bool = HDFS_ENABLED
    read_mode: str = HDFS_READ_MODE
    docker_container: str = DOCKER_HDFS_CONTAINER

    def read_all(self) -> dict[str, Any]:
        if not self.hdfs_enabled:
            return self._unavailable("HDFS job output loading is disabled.")

        webhdfs_error = None
        if self.read_mode in ("auto", "webhdfs"):
            result = self._read_all_webhdfs()
            if result["available"] or self.read_mode == "webhdfs":
                return result
            webhdfs_error = result["message"]

        if self.read_mode in ("auto", "docker"):
            result = self._read_all_docker()
            if result["available"] or self.read_mode == "docker":
                return result

            if webhdfs_error:
                result["message"] = f"{webhdfs_error} Docker fallback also failed: {result['message']}"
            return result

        return self._unavailable(f"Unknown BOOKING_HDFS_READ_MODE: {self.read_mode}")

    def _read_all_webhdfs(self) -> dict[str, Any]:
        if InsecureClient is None:
            return self._unavailable("Install hdfs dependency to read Hadoop job outputs.")
        try:
            client = InsecureClient(self.hdfs_url, user=self.hdfs_user, timeout=self.hdfs_timeout)
            jobs = {}
            for job_name, columns in JOB_COLUMNS.items():
                jobs[job_name] = self._read_job_webhdfs(client, job_name, columns)
            return {
                "available": True,
                "source": "webhdfs",
                "output_root": self.output_root,
                "jobs": jobs,
            }
        except Exception as exc:
            return self._unavailable(f"Could not read HDFS job outputs: {exc}")

    def _read_job_webhdfs(self, client: Any, job_name: str, columns: list[str]) -> dict[str, Any]:
        job_dir = str(PurePosixPath(self.output_root) / job_name)
        rows = []
        try:
            part_files = [name for name in client.list(job_dir) if name.startswith("part-")]
        except Exception as exc:
            return {"available": False, "columns": columns, "rows": [], "message": str(exc)}

        for part_file in sorted(part_files):
            part_path = str(PurePosixPath(job_dir) / part_file)
            with client.read(part_path, encoding="utf-8") as reader:
                for line in reader:
                    values = line.rstrip("\n").split("\t")
                    rows.append(dict(zip(columns, values)))

        return {"available": True, "columns": columns, "rows": rows}

    def _read_all_docker(self) -> dict[str, Any]:
        try:
            jobs = {}
            for job_name, columns in JOB_COLUMNS.items():
                jobs[job_name] = self._read_job_docker(job_name, columns)
            return {
                "available": True,
                "source": "docker",
                "output_root": self.output_root,
                "jobs": jobs,
            }
        except Exception as exc:
            return self._unavailable(str(exc))

    def _read_job_docker(self, job_name: str, columns: list[str]) -> dict[str, Any]:
        job_dir = str(PurePosixPath(self.output_root) / job_name)
        command = [
            "docker",
            "exec",
            self.docker_container,
            "hdfs",
            "dfs",
            "-cat",
            f"{job_dir}/part-*",
        ]
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=max(self.hdfs_timeout, 1),
        )
        if completed.returncode != 0:
            message = completed.stderr.strip() or completed.stdout.strip() or "No output returned."
            return {"available": False, "columns": columns, "rows": [], "message": message}

        rows = []
        for line in completed.stdout.splitlines():
            values = line.rstrip("\n").split("\t")
            rows.append(dict(zip(columns, values)))

        return {"available": True, "columns": columns, "rows": rows}

    def _unavailable(self, message: str) -> dict[str, Any]:
        return {
            "available": False,
            "source": None,
            "output_root": self.output_root,
            "message": message,
            "jobs": {},
        }
