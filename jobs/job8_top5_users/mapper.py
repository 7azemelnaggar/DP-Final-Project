#!/usr/bin/env python
"""
Job 8 mapper: Top 5 users by number of bookings.
Inputs: users.csv + bookings.csv
"""
import csv
import os
import sys

input_file = os.environ.get("mapreduce_map_input_file", os.environ.get("map_input_file", "")).lower()
is_users = "users" in input_file

reader = csv.reader(sys.stdin)
for row in reader:
    if not row:
        continue
    if is_users:
        if row[0] == "user_id":
            continue
        print("{}\tU\t{}".format(row[0], row[1]))
    else:
        if row[0] == "seat_id":
            continue
        print("{}\tB\t1".format(row[6]))
