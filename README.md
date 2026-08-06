# Distributed Ticket Reservation System - Part 1

This project implements the Data Collection and Storage stage for a distributed
ticket reservation system using Hadoop HDFS.

## What Is Included

- `docker-compose.yml`: Hadoop HDFS cluster with 1 namenode and 10 datanodes.
- `hadoop.env`: HDFS configuration, including replication factor 3.
- `data/events.csv`: sample event data.
- `data/users.csv`: sample user data.
- `data/seats.json`: sample seat and booking-state data.
- `data/Schema/*.json`: JSON schema definitions for the three entities.
- `data/docs/README.md`: data model, relationships, HDFS paths, and verification notes.
- `upload_to_hdfs.py`: uploads the CSV/JSON files into HDFS.
- `verify_hdfs.py`: reads HDFS data back and verifies exact local-vs-HDFS content,
  record counts, sample records, and referential integrity.
- `requirements.txt`: Python dependency for WebHDFS access.
- `to-run-it.txt`: step-by-step commands for running and verifying the project.
- `evidence/README.md`: checklist for capturing runtime proof before submission.

## Quick Run

```powershell
cd C:\Users\HP\Desktop\DP-Final-Project\DP-Final-Project
python -m pip install -r requirements.txt
docker compose up -d
python upload_to_hdfs.py --namenode http://localhost:9870 --local-dir ./data
python verify_hdfs.py --namenode http://localhost:9870 --local-dir ./data
```

## HDFS Layout

```text
/data/events.csv
/data/users.csv
/data/seats.json
```

## Cluster Layout

```text
namenode   - master node
datanode1  - worker node
datanode2  - worker node
datanode3  - worker node
datanode4  - worker node
datanode5  - worker node
datanode6  - worker node
datanode7  - worker node
datanode8  - worker node
datanode9  - worker node
datanode10 - worker node
```
