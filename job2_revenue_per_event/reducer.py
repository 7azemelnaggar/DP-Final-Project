#!/usr/bin/env python3
"""
Job 2: Total Revenue per Event
For each event_id key, Hadoop groups together its "E" record (event name,
at most one) and all its "B" records (one per booking). The reducer joins
them by simply accumulating both while the key stays the same.

Output: event_id \t event_name \t total_revenue \t total_bookings
"""
import sys

current_key = None
event_name = None
total_revenue = 0.0
booking_count = 0


def emit(key, name, revenue, count):
    if key is None:
        return
    print(f"{key}\t{name or 'UNKNOWN'}\t{revenue:.2f}\t{count}")


for line in sys.stdin:
    line = line.rstrip("\n")
    if not line:
        continue
    key, tag, value = line.split("\t")

    if key != current_key:
        emit(current_key, event_name, total_revenue, booking_count)
        current_key = key
        event_name = None
        total_revenue = 0.0
        booking_count = 0

    if tag == "E":
        event_name = value
    else:  # tag == "B"
        total_revenue += float(value)
        booking_count += 1

emit(current_key, event_name, total_revenue, booking_count)
