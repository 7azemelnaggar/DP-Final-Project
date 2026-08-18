# Distributed Ticket Reservation System

## Overview

This project stores ticket reservation data in Hadoop HDFS and runs batch
analytics jobs using Hadoop Streaming. The system is split into four main parts:

- Part 1: Data collection and storage in HDFS.
- Part 2: Batch processing and analytics using mapper/reducer jobs.
- Part 3: Real-time booking service with concurrency-safe booking/cancel
  operations.
- Part 4: Localhost website for viewing seat availability and calling the
  booking service.

The project uses Docker to start a Hadoop HDFS cluster with one namenode and ten
datanodes. The analytics output is saved back to HDFS so it can be reused by
later project parts, especially Part 4.

## Project Structure

```text
.
|-- docker-compose.yml
|-- hadoop.env
|-- requirements.txt
|-- upload_to_hdfs.py
|-- verify_hdfs_docker.py
|-- 01_setup_hdfs.sh
|-- 02_run_jobs_python.sh
|-- booking_service/
|   |-- __init__.py
|   |-- app.py
|   |-- store.py
|   `-- test_booking_service.py
|-- data/
|   |-- bookings.csv
|   |-- events.csv
|   |-- users.csv
|   |-- seats.json
|   |-- Schema/
|   |   |-- events_schema.json
|   |   |-- seats_schema.json
|   |   `-- users_schema.json
|   `-- docs/
|       `-- README.md
|-- jobs/
|   |-- job1_bookings_per_event/
|   |-- job2_revenue_per_event/
|   |-- job3_occupancy_per_event/
|   |-- job4_available_seats_per_event/
|   |-- job5_top5_events/
|   |-- job6_stats_by_category/
|   |-- job7_stats_by_date/
|   `-- job8_top5_users/
|-- ui/
|   `-- index.html
`-- evidence/
    `-- README.md
```

Each job folder contains:

```text
mapper.py
reducer.py
```

## Data Files

| File | Format | Description |
|---|---|---|
| `data/events.csv` | CSV | Event details such as event ID, name, venue, date, category, and total seats. |
| `data/users.csv` | CSV | User details such as user ID, name, email, phone, and registration date. |
| `data/seats.json` | JSON | Seat details such as seat ID, event ID, section, price, status, and user ID. |
| `data/bookings.csv` | CSV | Booking records used by the analytics jobs. |

## HDFS Layout

After running the setup script, HDFS uses this structure:

```text
/data/raw/
    bookings.csv
    events.csv
    users.csv
    seats.json
    booking_changes.csv

/data/jobs/member1/
    job1_bookings_per_event/
    job2_revenue_per_event/
    job3_occupancy_per_event/
    job4_available_seats_per_event/
    job5_top5_events/
    job6_stats_by_category/
    job7_stats_by_date/
    job8_top5_users/

/data/output/member1/
    job1_bookings_per_event/
    job2_revenue_per_event/
    job3_occupancy_per_event/
    job4_available_seats_per_event/
    job5_top5_events/
    job6_stats_by_category/
    job7_stats_by_date/
    job8_top5_users/
```

The `/data/output/member1/` directory is the handoff location for Part 4.

## Part 3: Real-Time Booking Processing

Part 3 is implemented in `booking_service/`. It exposes API endpoints to book
and cancel seats while using a thread lock to keep seat state consistent when
multiple requests arrive at the same time.

### Run the Booking Service

Install dependencies if needed:

```bash
python -m pip install -r requirements.txt
```

Start the API and UI:

```bash
python booking_service/app.py
```

Or run it with Docker Compose:

```bash
docker compose up booking-service
```

The local website is available at:

```text
http://127.0.0.1:5000
```

### Booking API

Book a seat:

```bash
curl -X POST http://127.0.0.1:5000/api/book \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"U001\",\"event_id\":\"E001\",\"seat_id\":\"S00003\"}"
```

Cancel a booking:

```bash
curl -X POST http://127.0.0.1:5000/api/cancel \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"U001\",\"event_id\":\"E001\",\"seat_id\":\"S00003\"}"
```

View seat availability for an event:

```bash
curl http://127.0.0.1:5000/api/events/E001/seats
```

Successful booking and cancellation changes are written to
`booking_service/runtime/booking_changes.csv`. When HDFS WebHDFS is reachable,
the service also uploads that change log to:

```text
/data/raw/booking_changes.csv
```

Useful HDFS environment variables:

| Variable | Default |
|---|---|
| `BOOKING_HDFS_URL` | `http://localhost:9870` |
| `BOOKING_HDFS_USER` | `root` |
| `BOOKING_HDFS_CHANGE_LOG_PATH` | `/data/raw/booking_changes.csv` |
| `BOOKING_HDFS_ENABLED` | `1` |

### Concurrency Tests

Run:

```bash
python -m unittest booking_service.test_booking_service -v
```

The tests verify that:

- multiple users trying to book the same seat concurrently produce only one
  successful booking;
- multiple users booking different seats concurrently can all succeed;
- cancelling a booking releases the seat again.

## Part 4: Local Host Website

Part 4 is implemented in `ui/index.html` and is served by the Flask app. The UI
loads events, displays current seat availability, lets a user book or cancel a
selected seat, shows the booking result, and refreshes seat status after every
request. It also reads the Part 2 Hadoop job outputs from
`/data/output/member1/` through the `/api/job-outputs` endpoint.

## Part 1: Data Storage

Part 1 starts the Hadoop cluster and uploads the project data into HDFS.

### Start Docker

Run this from the project folder:

```bash
docker compose up -d
```

Check the containers:

```bash
docker compose ps
```

Expected cluster:

- `namenode`
- `datanode1` to `datanode10`
- `hdfs-uploader`

The HDFS web UI is available at:

```text
http://localhost:9870
```

### Upload and Prepare HDFS

Run:

```bash
docker exec -it namenode bash /app/01_setup_hdfs.sh
```

This script:

- creates the HDFS folders;
- uploads `bookings.csv`, `events.csv`, `users.csv`, and `seats.json`;
- uploads each job's `mapper.py` and `reducer.py` into `/data/jobs/member1/`;
- prepares output folders for the analytics jobs.

### Verify HDFS Data

List HDFS data:

```bash
docker exec -it namenode hdfs dfs -ls -R /data
```

Run the verification script:

```bash
python verify_hdfs_docker.py --container namenode
```

The verification checks that files can be read back from HDFS and that seat
records reference valid events and users.

## Part 2: Batch Processing and Analytics

Part 2 runs eight Hadoop Streaming jobs. Each job reads from HDFS and writes its
result back to HDFS.

### Run All Jobs

Run:

```bash
docker exec -it namenode bash /app/02_run_jobs_python.sh
```

The script auto-detects one of these Python commands inside the container:

```text
python3
python
python2.7
```

Then it runs all jobs one by one.

## Analytics Jobs

| Job | Name | Inputs | Output |
|---|---|---|---|
| 1 | Total bookings per event | `bookings.csv` | `event_id`, `total_bookings` |
| 2 | Total revenue per event | `events.csv`, `bookings.csv` | `event_id`, `event_name`, `total_revenue`, `total_bookings` |
| 3 | Seat occupancy percentage per event | `events.csv`, `bookings.csv` | `event_id`, `event_name`, `booked_seats`, `total_seats`, `occupancy_percentage` |
| 4 | Available seats per event | `events.csv`, `bookings.csv` | `event_id`, `event_name`, `total_seats`, `booked_seats`, `available_seats` |
| 5 | Top 5 most-booked events | `events.csv`, `bookings.csv` | `rank`, `event_id`, `event_name`, `total_bookings` |
| 6 | Booking statistics by category | `events.csv`, `bookings.csv` | `category`, `total_bookings`, `total_revenue`, `average_booking_price` |
| 7 | Booking statistics by date | `bookings.csv` | `event_date`, `total_bookings`, `total_revenue`, `average_booking_price` |
| 8 | Top 5 users by bookings | `users.csv`, `bookings.csv` | `rank`, `user_id`, `user_name`, `total_bookings` |

## Requirement Coverage

| Requirement | Status |
|---|---|
| At least 8 batch jobs | Complete |
| Total bookings per event | Complete |
| Seat occupancy percentage per event | Complete |
| Total revenue per event | Complete |
| Number of available seats per event | Complete |
| Top 5 most-booked events | Complete |
| Booking statistics by event category | Complete |
| Booking statistics by date | Complete |
| Top 5 users by number of bookings | Complete |
| At least 4 jobs use two datasets | Complete: jobs 2, 3, 4, 5, 6, and 8 |
| At least 2 ranked/sorted jobs | Complete: jobs 5 and 8 |
| Jobs read from distributed storage | Complete: reads from `/data/raw/` |
| Jobs write to distributed storage | Complete: writes to `/data/output/member1/` |
| Jobs are re-runnable | Complete: old output is deleted before each job |
| Simple trigger command | Complete: `02_run_jobs_python.sh` |
| Clear output structure for Part 4 | Complete: `/data/output/member1/<job_name>/` |

## View Outputs

List all output folders:

```bash
docker exec -it namenode hdfs dfs -ls /data/output/member1
```

Read a specific job output:

```bash
docker exec -it namenode hdfs dfs -cat /data/output/member1/job1_bookings_per_event/part-*
docker exec -it namenode hdfs dfs -cat /data/output/member1/job2_revenue_per_event/part-*
docker exec -it namenode hdfs dfs -cat /data/output/member1/job5_top5_events/part-*
docker exec -it namenode hdfs dfs -cat /data/output/member1/job8_top5_users/part-*
```

## Troubleshooting

### File `/app/jobs/<job>/mapper.py` Does Not Exist

The run script expects jobs inside:

```text
/app/jobs/<job_name>/mapper.py
/app/jobs/<job_name>/reducer.py
```

Make sure the project has this structure:

```text
jobs/job1_bookings_per_event/mapper.py
jobs/job1_bookings_per_event/reducer.py
```

Check inside Docker:

```bash
docker exec -it namenode ls /app/jobs/job1_bookings_per_event
```

If the files are missing, restart Docker from the project folder:

```bash
docker compose down
docker compose up -d
```

### No Python Interpreter Found

If the script says no Python exists inside the container, install Python 2 on
the old Debian 9 Hadoop image:

```bash
docker exec -it namenode bash
sed -i 's/deb.debian.org/archive.debian.org/g' /etc/apt/sources.list
sed -i 's/security.debian.org/archive.debian.org/g' /etc/apt/sources.list
sed -i '/stretch-updates/d' /etc/apt/sources.list
apt-get -o Acquire::Check-Valid-Until=false update
apt-get install -y python-minimal
python --version
exit
```

Then run again:

```bash
docker exec -it namenode bash /app/02_run_jobs_python.sh
```

### Output Folder Already Exists

Hadoop fails if an output directory already exists. The run script handles this
by deleting old output before each job:

```bash
hdfs dfs -rm -r -f "$OUT/$job_name"
```

So the jobs can be re-run safely.

## Evidence for Grading

Recommended evidence screenshots or text files:

- `docker compose ps`
- `docker exec namenode hdfs dfsadmin -report`
- HDFS UI at `http://localhost:9870`
- `docker exec -it namenode hdfs dfs -ls -R /data`
- successful output from `01_setup_hdfs.sh`
- successful output from `02_run_jobs_python.sh`
- output folders under `/data/output/member1`
- sample output from each job

## Important Note About Distributed Execution

This project uses HDFS with one namenode and ten datanodes. The Hadoop Streaming
jobs read input from HDFS and write output back to HDFS.

If the job logs show names like:

```text
job_local...
```

then Hadoop is running the MapReduce job in local mode. If the instructor
requires proof of YARN-based distributed MapReduce execution, the Docker Compose
file should also include YARN services such as a resourcemanager and
nodemanager.
