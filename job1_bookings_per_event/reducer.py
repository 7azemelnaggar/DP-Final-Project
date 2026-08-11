    #!/usr/bin/env python
    """
    Job 1: Total Bookings per Event
    Reducer sums the 1's Hadoop groups together for each event_id key.
    Output: event_id \t total_bookings
    """
    import sys

    current_event = None
    count = 0

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        event_id, value = line.split("\t")
        value = int(value)

        if current_event == event_id:
            count += value
        else:
            if current_event is not None:
                print("{}\t{}".format(current_event, count))
            current_event = event_id
            count = value

    if current_event is not None:
        print("{}\t{}".format(current_event, count))
