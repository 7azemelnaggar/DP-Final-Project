from __future__ import annotations

import csv
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

try:
    from hdfs import InsecureClient
except Exception:  # pragma: no cover - hdfs is optional during local tests
    InsecureClient = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RUNTIME_DIR = PROJECT_ROOT / "booking_service" / "runtime"

DEFAULT_SEATS_FILE = DATA_DIR / "seats.json"
DEFAULT_EVENTS_FILE = DATA_DIR / "events.csv"
DEFAULT_USERS_FILE = DATA_DIR / "users.csv"

STATE_FILE = Path(os.getenv("BOOKING_STATE_FILE", RUNTIME_DIR / "seats_state.json"))
CHANGE_LOG_FILE = Path(os.getenv("BOOKING_CHANGE_LOG_FILE", RUNTIME_DIR / "booking_changes.csv"))

HDFS_URL = os.getenv("BOOKING_HDFS_URL", "http://localhost:9870")
HDFS_USER = os.getenv("BOOKING_HDFS_USER", "root")
HDFS_CHANGE_LOG_PATH = os.getenv("BOOKING_HDFS_CHANGE_LOG_PATH", "/data/raw/booking_changes.csv")
HDFS_SEATS_PATH = os.getenv("BOOKING_HDFS_SEATS_PATH", "/data/raw/seats.json")
HDFS_ENABLED = os.getenv("BOOKING_HDFS_ENABLED", "1") != "0"
HDFS_TIMEOUT = float(os.getenv("BOOKING_HDFS_TIMEOUT", "2"))

CHANGE_LOG_FIELDS = [
    "timestamp",
    "action",
    "result",
    "event_id",
    "seat_id",
    "user_id",
    "message",
]


class BookingStore:
    def __init__(
        self,
        seats_file: Path = DEFAULT_SEATS_FILE,
        events_file: Path = DEFAULT_EVENTS_FILE,
        users_file: Path = DEFAULT_USERS_FILE,
        state_file: Path = STATE_FILE,
        change_log_file: Path = CHANGE_LOG_FILE,
    ) -> None:
        self.seats_file = Path(seats_file)
        self.events_file = Path(events_file)
        self.users_file = Path(users_file)
        self.state_file = Path(state_file)
        self.change_log_file = Path(change_log_file)
        self._lock = threading.RLock()
        self.events = self._load_events()
        self.users = self._load_users()
        self.seats = self._load_seats()

    def list_events(self) -> list[dict[str, Any]]:
        with self._lock:
            return [
                {
                    **event,
                    "available_seats": self._count_seats(event["event_id"], "available"),
                    "booked_seats": self._count_seats(event["event_id"], "booked"),
                }
                for event in self.events.values()
            ]

    def seat_availability(self, event_id: str) -> dict[str, Any]:
        with self._lock:
            event_seats = [seat.copy() for seat in self.seats.values() if seat["event_id"] == event_id]
            return {
                "event": self.events.get(event_id),
                "available_count": sum(1 for seat in event_seats if seat["status"] == "available"),
                "booked_count": sum(1 for seat in event_seats if seat["status"] == "booked"),
                "seats": sorted(event_seats, key=lambda s: (s["section"], int(s["row"]), int(s["seat_number"]))),
            }

    def all_seats(self) -> dict[str, Any]:
        with self._lock:
            seats = [seat.copy() for seat in self.seats.values()]
            return {
                "available_count": sum(1 for seat in seats if seat["status"] == "available"),
                "booked_count": sum(1 for seat in seats if seat["status"] == "booked"),
                "seats": sorted(
                    seats,
                    key=lambda s: (s["event_id"], s["section"], int(s["row"]), int(s["seat_number"])),
                ),
            }

    def list_users(self) -> list[dict[str, Any]]:
        with self._lock:
            booked_by_user = {user_id: [] for user_id in self.users}
            for seat in self.seats.values():
                if seat["status"] == "booked" and seat.get("user_id") in booked_by_user:
                    booked_by_user[seat["user_id"]].append(
                        {
                            "seat_id": seat["seat_id"],
                            "event_id": seat["event_id"],
                        }
                    )

            return [
                {
                    **user,
                    "can_book": True,
                    "booked_seats": booked_by_user[user_id],
                    "booked_count": len(booked_by_user[user_id]),
                }
                for user_id, user in self.users.items()
            ]

    def book_seat(self, user_id: str, event_id: str, seat_id: str) -> dict[str, Any]:
        with self._lock:
            validation = self._validate_request(user_id, event_id, seat_id)
            if validation is not None:
                return validation

            seat = self.seats[seat_id]
            if seat["event_id"] != event_id:
                return self._failure("Seat unavailable.", event_id, seat_id, user_id)

            if seat["status"] == "booked":
                message = (
                    "Seat already booked."
                    if self._count_seats(event_id, "available") > 0
                    else "Seat unavailable."
                )
                return self._failure(message, event_id, seat_id, user_id)

            seat["status"] = "booked"
            seat["user_id"] = user_id
            self._persist("book", "success", event_id, seat_id, user_id, "Booking successful.")
            return self._success("Booking successful.", seat)

    def cancel_booking(self, user_id: str, event_id: str, seat_id: str) -> dict[str, Any]:
        with self._lock:
            validation = self._validate_request(user_id, event_id, seat_id)
            if validation is not None:
                return validation

            seat = self.seats[seat_id]
            if seat["event_id"] != event_id or seat["status"] != "booked":
                return self._failure("Seat unavailable.", event_id, seat_id, user_id)

            if seat.get("user_id") != user_id:
                return self._failure("Seat already booked.", event_id, seat_id, user_id)

            seat["status"] = "available"
            seat["user_id"] = None
            self._persist("cancel", "success", event_id, seat_id, user_id, "Booking cancelled.")
            return self._success("Booking cancelled.", seat)

    def _validate_request(self, user_id: str, event_id: str, seat_id: str) -> dict[str, Any] | None:
        if not user_id or not event_id or not seat_id:
            return self._failure("user_id, event_id, and seat_id are required.", event_id, seat_id, user_id)
        if user_id not in self.users:
            return self._failure("Seat unavailable.", event_id, seat_id, user_id)
        if event_id not in self.events:
            return self._failure("Seat unavailable.", event_id, seat_id, user_id)
        if seat_id not in self.seats:
            return self._failure("Seat unavailable.", event_id, seat_id, user_id)
        return None

    def _load_events(self) -> dict[str, dict[str, str]]:
        with self.events_file.open(newline="", encoding="utf-8") as handle:
            return {row["event_id"]: row for row in csv.DictReader(handle)}

    def _load_users(self) -> dict[str, dict[str, str]]:
        with self.users_file.open(newline="", encoding="utf-8") as handle:
            return {row["user_id"]: row for row in csv.DictReader(handle)}

    def _load_seats(self) -> dict[str, dict[str, Any]]:
        source = self.state_file if self.state_file.exists() else self.seats_file
        with source.open(encoding="utf-8") as handle:
            seats = json.load(handle)
        return {seat["seat_id"]: seat for seat in seats}

    def _persist(
        self,
        action: str,
        result: str,
        event_id: str,
        seat_id: str,
        user_id: str,
        message: str,
    ) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.change_log_file.parent.mkdir(parents=True, exist_ok=True)
        with self.state_file.open("w", encoding="utf-8") as handle:
            json.dump(list(self.seats.values()), handle, indent=2)

        write_header = not self.change_log_file.exists()
        with self.change_log_file.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=CHANGE_LOG_FIELDS)
            if write_header:
                writer.writeheader()
            writer.writerow(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": action,
                    "result": result,
                    "event_id": event_id,
                    "seat_id": seat_id,
                    "user_id": user_id,
                    "message": message,
                }
            )
        self._sync_to_hdfs()

    def _sync_to_hdfs(self) -> None:
        self._sync_change_log_to_hdfs()
        self._sync_seats_to_hdfs()

    def _sync_seats_to_hdfs(self) -> None:
        if not HDFS_ENABLED or InsecureClient is None:
            return
        try:
            client = InsecureClient(HDFS_URL, user=HDFS_USER, timeout=HDFS_TIMEOUT)
            client.makedirs(str(PurePosixPath(HDFS_SEATS_PATH).parent))
            client.upload(HDFS_SEATS_PATH, str(self.state_file), overwrite=True)
        except Exception:
            return

    def _sync_change_log_to_hdfs(self) -> None:
        if not HDFS_ENABLED or InsecureClient is None:
            return
        try:
            client = InsecureClient(HDFS_URL, user=HDFS_USER, timeout=HDFS_TIMEOUT)
            client.makedirs(str(PurePosixPath(HDFS_CHANGE_LOG_PATH).parent))
            client.upload(HDFS_CHANGE_LOG_PATH, str(self.change_log_file), overwrite=True)
        except Exception:
            # Local development and tests can run without Hadoop; the durable
            # local log will be uploaded on the next successful HDFS sync.
            return

    def _count_seats(self, event_id: str, status: str) -> int:
        return sum(1 for seat in self.seats.values() if seat["event_id"] == event_id and seat["status"] == status)

    @staticmethod
    def _success(message: str, seat: dict[str, Any]) -> dict[str, Any]:
        return {"success": True, "message": message, "seat": seat.copy()}

    @staticmethod
    def _failure(message: str, event_id: str, seat_id: str, user_id: str) -> dict[str, Any]:
        return {
            "success": False,
            "message": message,
            "event_id": event_id,
            "seat_id": seat_id,
            "user_id": user_id,
        }
