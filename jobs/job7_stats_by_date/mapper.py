#!/usr/bin/env python
"""
Job 7 mapper: Booking statistics by event date.
Input: bookings.csv
"""
import csv
import sys

reader = csv.reader(sys.stdin)
for row in reader:
    if not row or row[0] == "seat_id":
        continue
    event_date = row[5].split("T")[0]
    price = row[-1]
    print("{}\t1\t{}".format(event_date, price))
