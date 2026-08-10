#!/usr/bin/env bash
# Run this INSIDE the namenode container:
#   docker exec -it namenode bash /app/02_run_jobs.sh
set -euo pipefail

STREAMING_JAR=$(find /opt/hadoop-*/share/hadoop/tools/lib -name 'hadoop-streaming*.jar' | head -1)
RAW=/data/raw
OUT=/data/output/member1

echo "Using streaming jar: $STREAMING_JAR"

# ---- Job 1: Total Bookings per Event ----
hdfs dfs -rm -r -f $OUT/job1_bookings_per_event

hadoop jar "$STREAMING_JAR" \
  -files /app/job1_bookings_per_event/mapper.py,/app/job1_bookings_per_event/reducer.py \
  -mapper mapper.py \
  -reducer reducer.py \
  -input $RAW/bookings.csv \
  -output $OUT/job1_bookings_per_event

echo "--- Job 1 output ---"
hdfs dfs -cat $OUT/job1_bookings_per_event/part-* | sort

# ---- Job 2: Total Revenue per Event (join events + bookings) ----
hdfs dfs -rm -r -f $OUT/job2_revenue_per_event

hadoop jar "$STREAMING_JAR" \
  -files /app/job2_revenue_per_event/mapper.py,/app/job2_revenue_per_event/reducer.py \
  -mapper mapper.py \
  -reducer reducer.py \
  -input $RAW/events.csv \
  -input $RAW/bookings.csv \
  -output $OUT/job2_revenue_per_event

echo "--- Job 2 output ---"
hdfs dfs -cat $OUT/job2_revenue_per_event/part-* | sort
