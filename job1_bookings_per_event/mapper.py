#!/usr/bin/env python3
"""
Job 1: Total Bookings per Event
Input : bookings.csv
Output: event_id \t 1   (one line per booking)
"""
import sys
import csv

reader = csv.reader(sys.stdin)

for row in reader:
    if not row:
        continue
    # skip header line
    if row[0] == "seat_id":
        continue
    event_id = row[1]
    print(f"{event_id}\t1")
