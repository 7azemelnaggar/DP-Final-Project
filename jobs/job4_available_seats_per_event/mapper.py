#!/usr/bin/env python
"""
Job 4 mapper: Number of available seats per event.
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
        print("{}\tE\t{}\t{}".format(row[0], row[1], row[6]))
    else:
        if row[0] == "seat_id":
            continue
        print("{}\tB\t1".format(row[1]))
