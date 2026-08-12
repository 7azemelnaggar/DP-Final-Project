#!/usr/bin/env python
"""
Job 5 reducer.
Output: rank    event_id    event_name    total_bookings
"""
import sys

current_event = None
event_name = "UNKNOWN"
booked = 0
results = []


def close_event(event_id, name, bookings):
    if event_id is not None:
        results.append((bookings, event_id, name))


for line in sys.stdin:
    parts = line.rstrip("\n").split("\t")
    if len(parts) < 3:
        continue
    event_id, tag = parts[0], parts[1]

    if event_id != current_event:
        close_event(current_event, event_name, booked)
        current_event = event_id
        event_name = "UNKNOWN"
        booked = 0

    if tag == "E":
        event_name = parts[2]
    elif tag == "B":
        booked += 1

close_event(current_event, event_name, booked)

results.sort(key=lambda item: (-item[0], item[1]))
for rank, item in enumerate(results[:5], 1):
    bookings, event_id, name = item
    print("{}\t{}\t{}\t{}".format(rank, event_id, name, bookings))
