#!/usr/bin/env python
"""
Job 6 mapper: Booking statistics by event category.
Inputs: events.csv + bookings.csv
"""
import csv
import os
import sys

input_file = os.environ.get("mapreduce_map_input_file", os.environ.get("map_input_file", "")).lower()
is_events = "events" in input_file

reader = csv.reader(sys.stdin)
for row in reader:
    if not row:
        continue
    if is_events:
        if row[0] == "event_id":
            continue
        print("{}\tE\t{}".format(row[0], row[5]))
    else:
        if row[0] == "seat_id":
            continue
        print("{}\tB\t{}".format(row[1], row[-1]))
