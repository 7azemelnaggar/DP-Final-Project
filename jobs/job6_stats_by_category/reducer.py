#!/usr/bin/env python
"""
Job 6 reducer.
Output: category    total_bookings    total_revenue    average_booking_price
"""
import sys

current_event = None
category = "UNKNOWN"
bookings = 0
revenue = 0.0
category_totals = {}


def close_event(cat, count, total):
    if cat not in category_totals:
        category_totals[cat] = [0, 0.0]
    category_totals[cat][0] += count
    category_totals[cat][1] += total


for line in sys.stdin:
    parts = line.rstrip("\n").split("\t")
    if len(parts) < 3:
        continue
    event_id, tag, value = parts[0], parts[1], parts[2]

    if event_id != current_event:
        if current_event is not None:
            close_event(category, bookings, revenue)
        current_event = event_id
        category = "UNKNOWN"
        bookings = 0
        revenue = 0.0

    if tag == "E":
        category = value
    elif tag == "B":
        bookings += 1
        revenue += float(value)

if current_event is not None:
    close_event(category, bookings, revenue)

for cat in sorted(category_totals):
    count, total = category_totals[cat]
    average = (total / count) if count else 0.0
    print("{}\t{}\t{:.2f}\t{:.2f}".format(cat, count, total, average))
