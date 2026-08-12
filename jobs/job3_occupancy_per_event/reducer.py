#!/usr/bin/env python
"""
Job 3 reducer.
Output: event_id    event_name    booked_seats    total_seats    occupancy_percentage
"""
import sys

current_event = None
event_name = "UNKNOWN"
total_seats = 0
booked = 0


def emit(event_id, name, seats, bookings):
    if event_id is None:
        return
    percentage = (bookings * 100.0 / seats) if seats else 0.0
    print("{}\t{}\t{}\t{}\t{:.2f}".format(event_id, name, bookings, seats, percentage))


for line in sys.stdin:
    parts = line.rstrip("\n").split("\t")
    if len(parts) < 3:
        continue
    event_id, tag = parts[0], parts[1]

    if event_id != current_event:
        emit(current_event, event_name, total_seats, booked)
        current_event = event_id
        event_name = "UNKNOWN"
        total_seats = 0
        booked = 0

    if tag == "E" and len(parts) >= 4:
        event_name = parts[2]
        total_seats = int(parts[3])
    elif tag == "B":
        booked += 1

emit(current_event, event_name, total_seats, booked)
