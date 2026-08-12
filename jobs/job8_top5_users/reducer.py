#!/usr/bin/env python
"""
Job 8 reducer.
Output: rank    user_id    user_name    total_bookings
"""
import sys

current_user = None
user_name = "UNKNOWN"
bookings = 0
results = []


def close_user(user_id, name, count):
    if user_id is not None:
        results.append((count, user_id, name))


for line in sys.stdin:
    parts = line.rstrip("\n").split("\t")
    if len(parts) < 3:
        continue
    user_id, tag = parts[0], parts[1]

    if user_id != current_user:
        close_user(current_user, user_name, bookings)
        current_user = user_id
        user_name = "UNKNOWN"
        bookings = 0

    if tag == "U":
        user_name = parts[2]
    elif tag == "B":
        bookings += 1

close_user(current_user, user_name, bookings)

results.sort(key=lambda item: (-item[0], item[1]))
for rank, item in enumerate(results[:5], 1):
    count, user_id, name = item
    print("{}\t{}\t{}\t{}".format(rank, user_id, name, count))
