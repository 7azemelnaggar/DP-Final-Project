# Member 1 — Basic Single & Multi-Dataset Aggregations

## HDFS layout (the "infrastructure" task)

```
/data/raw/                              <- immutable source CSVs, uploaded once
    bookings.csv
    events.csv
    users.csv
/data/jobs/member1/                     <- mapper.py / reducer.py per job (reference copy in HDFS)
    job1_bookings_per_event/
    job2_revenue_per_event/
/data/output/member1/                   <- results; Part 4 (downstream) reads ONLY from here
    job1_bookings_per_event/part-00000
    job2_revenue_per_event/part-00000
```
Keeping raw / jobs / output as siblings under `/data` means Part 4 always
knows results live at `/data/output/<member>/<job_name>/`, regardless of how
the job itself was implemented.

## Steps

### 1. Start the cluster (from your project folder, on the host)
```bash
docker-compose up -d
```
This brings up HDFS (namenode + 10 datanodes) **and** YARN
(resourcemanager + nodemanager + historyserver), which I added to
`docker-compose.yml` — the original file only had HDFS, so no MapReduce
job could actually run. Wait ~30s, then confirm:
- HDFS UI: http://localhost:9870 (should show 10 live datanodes)
- YARN UI: http://localhost:8088 (should show 1 active nodemanager)

### 2. Create the HDFS directories and upload the raw data
```bash
docker exec -it namenode bash /app/01_setup_hdfs.sh
```

### 3. Run both jobs
```bash
docker exec -it namenode bash /app/02_run_jobs.sh
```
This submits both Hadoop Streaming jobs to YARN and prints the results.

### 4. Verify / hand off to Part 4
```bash
docker exec -it namenode hdfs dfs -cat /data/output/member1/job1_bookings_per_event/part-*
docker exec -it namenode hdfs dfs -cat /data/output/member1/job2_revenue_per_event/part-*
```

## Job 1 — Total Bookings per Event
- Input: `bookings.csv`
- Mapper emits `event_id \t 1` per booking row
- Reducer sums per event_id
- Output: `event_id \t total_bookings`

## Job 2 — Total Revenue per Event (multi-dataset join)
- Inputs: `events.csv` + `bookings.csv` (reduce-side join)
- Mapper tags each row `E` (from events.csv, carries event name) or `B`
  (from bookings.csv, carries price), keyed by `event_id`
- Reducer accumulates the event name and sums price/count per key
- Output: `event_id \t event_name \t total_revenue \t total_bookings`

Both were dry-run locally against your actual `bookings.csv`/`events.csv`
and produce consistent numbers (e.g. E001 → 4 bookings / $193.36).

## Files
```
docker-compose.yml              <- updated: added YARN so jobs can run
hadoop.env                      <- updated: added YARN config
01_setup_hdfs.sh                <- creates HDFS dirs, uploads raw data
02_run_jobs.sh                  <- submits both streaming jobs
job1_bookings_per_event/
    mapper.py
    reducer.py
job2_revenue_per_event/
    mapper.py
    reducer.py
```
