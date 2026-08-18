from __future__ import annotations

import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from booking_service.store import BookingStore


ROOT = Path(__file__).resolve().parents[1]


class BookingConcurrencyTests(unittest.TestCase):
    def make_store(self) -> BookingStore:
        self.tmpdir = tempfile.TemporaryDirectory()
        tmp = Path(self.tmpdir.name)
        seats = [
            {
                "seat_id": "S10001",
                "event_id": "E001",
                "section": "A",
                "row": "1",
                "seat_number": "1",
                "price": 50.0,
                "status": "available",
                "user_id": None,
            },
            {
                "seat_id": "S10002",
                "event_id": "E001",
                "section": "A",
                "row": "1",
                "seat_number": "2",
                "price": 50.0,
                "status": "available",
                "user_id": None,
            },
            {
                "seat_id": "S10003",
                "event_id": "E001",
                "section": "A",
                "row": "1",
                "seat_number": "3",
                "price": 50.0,
                "status": "available",
                "user_id": None,
            },
        ]
        seats_file = tmp / "seats.json"
        seats_file.write_text(json.dumps(seats), encoding="utf-8")
        self.addCleanup(self.tmpdir.cleanup)
        return BookingStore(
            seats_file=seats_file,
            events_file=ROOT / "data" / "events.csv",
            users_file=ROOT / "data" / "users.csv",
            state_file=tmp / "seats_state.json",
            change_log_file=tmp / "booking_changes.csv",
        )

    def test_same_seat_concurrent_booking_allows_only_one_success(self) -> None:
        store = self.make_store()
        store._sync_change_log_to_hdfs = lambda: None
        user_ids = ["U001", "U002", "U003", "U004", "U005"]

        with ThreadPoolExecutor(max_workers=len(user_ids)) as executor:
            results = list(
                executor.map(lambda user_id: store.book_seat(user_id, "E001", "S10001"), user_ids)
            )

        successes = [result for result in results if result["success"]]
        failures = [result for result in results if not result["success"]]

        self.assertEqual(1, len(successes))
        self.assertEqual(4, len(failures))
        self.assertTrue(all(result["message"] == "Seat already booked." for result in failures))
        self.assertEqual("booked", store.seats["S10001"]["status"])
        self.assertEqual(successes[0]["seat"]["user_id"], store.seats["S10001"]["user_id"])

    def test_different_seats_concurrent_booking_can_all_succeed(self) -> None:
        store = self.make_store()
        store._sync_change_log_to_hdfs = lambda: None
        requests = [("U001", "S10001"), ("U002", "S10002"), ("U003", "S10003")]

        with ThreadPoolExecutor(max_workers=len(requests)) as executor:
            results = list(
                executor.map(lambda item: store.book_seat(item[0], "E001", item[1]), requests)
            )

        self.assertTrue(all(result["success"] for result in results))
        self.assertTrue(all(result["message"] == "Booking successful." for result in results))
        self.assertEqual(0, store.seat_availability("E001")["available_count"])

    def test_cancel_booking_releases_seat(self) -> None:
        store = self.make_store()
        store._sync_change_log_to_hdfs = lambda: None

        booked = store.book_seat("U001", "E001", "S10001")
        cancelled = store.cancel_booking("U001", "E001", "S10001")

        self.assertTrue(booked["success"])
        self.assertTrue(cancelled["success"])
        self.assertEqual("Booking cancelled.", cancelled["message"])
        self.assertEqual("available", store.seats["S10001"]["status"])
        self.assertIsNone(store.seats["S10001"]["user_id"])


if __name__ == "__main__":
    unittest.main()
