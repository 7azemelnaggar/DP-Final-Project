#!/usr/bin/env python
"""
Job 2: Total Revenue per Event  (multi-dataset: events.csv + bookings.csv)

This mapper is fed BOTH files (via two -input flags in the streaming
command). It tells them apart using the map.input.file env var that
Hadoop Streaming sets for every map task, and tags each output record
so the reducer knows which dataset it came from:

  events.csv   -> event_id \t E \t event_name
  bookings.csv -> event_id \t B \t price
"""
import sys
import os
import csv

input_file = os.environ.get(
    "mapreduce_map_input_file", os.environ.get("map_input_file", "")
).lower()
is_events = "events" in input_file

reader = csv.reader(sys.stdin)

for row in reader:
    if not row:
        continue

    if is_events:
        # events.csv header: event_id,name,venue,location,date_time,category,total_seats,status
        if row[0] == "event_id":
            continue
        event_id, name = row[0], row[1]
        print("{}\tE\t{}".format(event_id, name))
    else:
        # bookings.csv header: seat_id,event_id,event_name,venue,location,
        #                       date_time,user_id,user_name,email,phone,
        #                       section,row,seat_number,price
        if row[0] == "seat_id":
            continue
        event_id, price = row[1], row[-1]
        print("{}\tB\t{}".format(event_id, price))
