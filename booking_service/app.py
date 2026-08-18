import os
import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from booking_service.analytics import JobOutputReader
from booking_service.store import BookingStore

UI_DIR = PROJECT_ROOT / "ui"


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(UI_DIR), static_url_path="")
    store = BookingStore()
    job_outputs = JobOutputReader()
    app.config["booking_store"] = store

    @app.get("/")
    def index():
        return send_from_directory(UI_DIR, "index.html")

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/api/events")
    def events():
        return jsonify({"events": store.list_events()})

    @app.get("/api/events/<event_id>/seats")
    def seats(event_id: str):
        return jsonify(store.seat_availability(event_id))

    @app.get("/api/job-outputs")
    def analytics():
        return jsonify(job_outputs.read_all())

    @app.post("/api/book")
    def book():
        payload = request.get_json(silent=True) or {}
        result = store.book_seat(
            user_id=str(payload.get("user_id", "")).strip(),
            event_id=str(payload.get("event_id", "")).strip(),
            seat_id=str(payload.get("seat_id", "")).strip(),
        )
        return jsonify(result), 200 if result["success"] else 409

    @app.post("/api/cancel")
    def cancel():
        payload = request.get_json(silent=True) or {}
        result = store.cancel_booking(
            user_id=str(payload.get("user_id", "")).strip(),
            event_id=str(payload.get("event_id", "")).strip(),
            seat_id=str(payload.get("seat_id", "")).strip(),
        )
        return jsonify(result), 200 if result["success"] else 409

    return app


app = create_app()


if __name__ == "__main__":
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "5000"))
    app.run(host=host, port=port, threaded=True)
