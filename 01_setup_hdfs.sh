#!/usr/bin/env bash
# Run this INSIDE the namenode container (it has the hadoop CLI and, via the
# added volume mount, can also see our local files at /app):
#
#   docker exec -it namenode bash /app/01_setup_hdfs.sh
#
set -euo pipefail

# --- HDFS directory design ---
# /data/raw/<file>.csv               -> immutable source data, uploaded once
# /data/jobs/<member>/<job>/         -> mapper.py / reducer.py staged for each job
# /data/output/<member>/<job>/       -> job results; Part 4 (downstream) reads from here
RAW=/data/raw
JOBS=/data/jobs/member1
OUT=/data/output/member1

hdfs dfs -mkdir -p $RAW
hdfs dfs -mkdir -p $JOBS/job1_bookings_per_event
hdfs dfs -mkdir -p $JOBS/job2_revenue_per_event
hdfs dfs -mkdir -p $OUT

# Upload raw datasets (idempotent: -f overwrites on re-run)
hdfs dfs -put -f /app/bookings.csv $RAW/bookings.csv
hdfs dfs -put -f /app/events.csv   $RAW/events.csv
hdfs dfs -put -f /app/users.csv    $RAW/users.csv

echo "HDFS layout ready:"
hdfs dfs -ls -R /data
