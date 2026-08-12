#!/usr/bin/env bash
# Run this INSIDE the namenode container:
#   docker exec -it namenode bash /app/02_run_jobs_python.sh
#
# Runs all Part 2 Hadoop Streaming analytics jobs.
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
  echo "Install Python, or use a Hadoop image that includes Python, then rerun."
  exit 1
fi

echo "Using streaming jar: $STREAMING_JAR"
echo "Using Python: $PY"

run_streaming_job() {
  job_name="$1"
  input_args="$2"

  echo ""
  echo "===== Running $job_name ====="
  hdfs dfs -rm -r -f "$OUT/$job_name"

  # shellcheck disable=SC2086
  hadoop jar "$STREAMING_JAR" \
    -D mapreduce.job.reduces=1 \
    -files "/app/jobs/$job_name/mapper.py,/app/jobs/$job_name/reducer.py" \
    -mapper "$PY mapper.py" \
    -reducer "$PY reducer.py" \
    $input_args \
    -output "$OUT/$job_name"

  echo "--- $job_name output ---"
  hdfs dfs -cat "$OUT/$job_name/part-*" | sort
}

run_streaming_job "job1_bookings_per_event" \
  "-input $RAW/bookings.csv"

run_streaming_job "job2_revenue_per_event" \
  "-input $RAW/events.csv -input $RAW/bookings.csv"

run_streaming_job "job3_occupancy_per_event" \
  "-input $RAW/events.csv -input $RAW/bookings.csv"

run_streaming_job "job4_available_seats_per_event" \
  "-input $RAW/events.csv -input $RAW/bookings.csv"

run_streaming_job "job5_top5_events" \
  "-input $RAW/events.csv -input $RAW/bookings.csv"

run_streaming_job "job6_stats_by_category" \
  "-input $RAW/events.csv -input $RAW/bookings.csv"

run_streaming_job "job7_stats_by_date" \
  "-input $RAW/bookings.csv"

run_streaming_job "job8_top5_users" \
  "-input $RAW/users.csv -input $RAW/bookings.csv"

echo ""
echo "All Part 2 outputs are under $OUT"
hdfs dfs -ls "$OUT"
