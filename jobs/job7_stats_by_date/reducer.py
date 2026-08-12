#!/usr/bin/env python
"""
Job 7 reducer.
Output: event_date    total_bookings    total_revenue    average_booking_price
"""
import sys

current_date = None
bookings = 0
revenue = 0.0


def emit(date_value, count, total):
    if date_value is None:
        return
    average = (total / count) if count else 0.0
    print("{}\t{}\t{:.2f}\t{:.2f}".format(date_value, count, total, average))


for line in sys.stdin:
    parts = line.rstrip("\n").split("\t")
    if len(parts) < 3:
        continue
    date_value, count, price = parts[0], int(parts[1]), float(parts[2])

    if date_value != current_date:
        emit(current_date, bookings, revenue)
        current_date = date_value
        bookings = 0
        revenue = 0.0

    bookings += count
    revenue += price

emit(current_date, bookings, revenue)
