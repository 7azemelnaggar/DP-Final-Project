#!/usr/bin/env bash
# Run this INSIDE the namenode container:
#   docker exec -it namenode bash /app/02_run_jobs_python.sh
#
# This version keeps the Hadoop Streaming jobs in Python.
# It auto-detects python3, python, or python2.7 inside the container.
set -euo pipefail

STREAMING_JAR=$(find /opt/hadoop-*/share/hadoop/tools/lib -name 'hadoop-streaming*.jar' | head -1)
RAW=/data/raw
OUT=/data/output/member1

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
elif command -v python2.7 >/dev/null 2>&1; then
  PY=python2.7
else
  echo "ERROR: No Python interpreter found in this container."
  echo "Install Python first, then rerun this script."
  exit 1
fi

echo "Using streaming jar: $STREAMING_JAR"
echo "Using Python: $PY"

# ---- Job 1: Total Bookings per Event ----
hdfs dfs -rm -r -f $OUT/job1_bookings_per_event

hadoop jar "$STREAMING_JAR" \
  -files /app/job1_bookings_per_event/mapper.py,/app/job1_bookings_per_event/reducer.py \
  -mapper "$PY mapper.py" \
  -reducer "$PY reducer.py" \
  -input $RAW/bookings.csv \
  -output $OUT/job1_bookings_per_event

echo "--- Job 1 output ---"
hdfs dfs -cat $OUT/job1_bookings_per_event/part-* | sort

# ---- Job 2: Total Revenue per Event (join events + bookings) ----
hdfs dfs -rm -r -f $OUT/job2_revenue_per_event

hadoop jar "$STREAMING_JAR" \
  -files /app/job2_revenue_per_event/mapper.py,/app/job2_revenue_per_event/reducer.py \
  -mapper "$PY mapper.py" \
  -reducer "$PY reducer.py" \
  -input $RAW/events.csv \
  -input $RAW/bookings.csv \
  -output $OUT/job2_revenue_per_event

echo "--- Job 2 output ---"
hdfs dfs -cat $OUT/job2_revenue_per_event/part-* | sort
