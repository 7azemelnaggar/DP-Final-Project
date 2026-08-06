# Data Model and Sample Data - Distributed Ticket Reservation System

## Part 1: Data Collection and Storage

This document defines the data model for the three core entities in the ticket
reservation system: **Events**, **Seats**, and **Users**. The sample data is
loaded into HDFS and reused by later project stages for processing, analysis,
and presentation.

## 1. Architecture

```text
Local sample data
  data/events.csv
  data/users.csv
  data/seats.json
        |
        | upload_to_hdfs.py via WebHDFS
        v
Hadoop HDFS cluster
  namenode: 1 master
  datanode1-datanode10: 10 workers
        |
        | verify_hdfs.py via WebHDFS
        v
Read-back verification and integrity checks
```

## 2. Entities

### Events

| Field | Type | Key | Description |
|---|---|---|---|
| `event_id` | string | PK | Unique identifier for the event, such as `E001`. |
| `name` | string | | Event title. |
| `venue` | string | | Name of the venue. |
| `location` | string | | City where the venue is located. |
| `date_time` | datetime | | Date and time of the event in ISO 8601 format. |
| `category` | string | | Concert, Sports, Theater, Conference, Comedy, etc. |
| `total_seats` | integer | | Total seat capacity for the event. |
| `status` | string | | `upcoming`, `ongoing`, `completed`, or `cancelled`. |

Sample file: `data/events.csv`

Sample row:

```csv
E001,Coldplay World Tour,Cairo International Stadium,Cairo,2026-09-15T20:00:00,Concert,5000,upcoming
```

### Seats

| Field | Type | Key | Description |
|---|---|---|---|
| `seat_id` | string | PK | Unique identifier for the seat, such as `S00001`. |
| `event_id` | string | FK | References `Events.event_id`. |
| `section` | string | | Seating section, such as `A`, `B`, `C`, or `VIP`. |
| `row` | string | | Row number within the section. |
| `seat_number` | string | | Seat number within the row. |
| `price` | decimal | | Ticket price for this seat. |
| `status` | string | | `available` or `booked`. |
| `user_id` | string/null | FK | References `Users.user_id`; `null` if the seat is not booked. |

Sample file: `data/seats.json`

Sample record:

```json
{
  "seat_id": "S00001",
  "event_id": "E001",
  "section": "A",
  "row": "1",
  "seat_number": "24",
  "price": 45.5,
  "status": "booked",
  "user_id": "U012"
}
```

### Users

| Field | Type | Key | Description |
|---|---|---|---|
| `user_id` | string | PK | Unique identifier for the user, such as `U001`. |
| `name` | string | | Full name. |
| `email` | string | | Contact email address. |
| `phone` | string | | Contact phone number. |
| `registration_date` | date | | Date the user registered. |

Sample file: `data/users.csv`

Sample row:

```csv
U001,Ahmed Farouk,ahmed.farouk@example.com,01012345678,2025-01-12
```

## 3. Relationships

```text
Events (1) ----< Seats >---- (1) Users
```

- One event has many seats through `Seats.event_id`.
- One user can book many seats through `Seats.user_id`.
- Events and users are connected through seats. The seat record also stores
  the current booking state for this project stage.

Booking information is stored directly on each seat through `status` and
`user_id`. A separate `Bookings` table could be added later if historical
booking transactions are required.

## 4. Sample Data Summary

| File | Format | Records | Entity |
|---|---:|---:|---|
| `data/events.csv` | CSV | 10 | Events |
| `data/users.csv` | CSV | 15 | Users |
| `data/seats.json` | JSON | 60 | Seats |

Integrity conditions satisfied by the sample data:

- Every `event_id` in `seats.json` exists in `events.csv`.
- Every non-null `user_id` in `seats.json` exists in `users.csv`.
- Every booked seat has a `user_id`.
- Every available seat has a null `user_id`.
- Both CSV and JSON formats are included, as required by the assignment.

## 5. HDFS Storage Structure

After upload, the files are stored in HDFS as:

```text
/data/events.csv
/data/seats.json
/data/users.csv
```

The `/data` directory is the shared HDFS storage location for Part 1. Each path
stores one entity's sample data and is used by downstream parts of the project.

## 6. Verification Performed

The verification script confirms:

- all required HDFS files can be read back;
- HDFS file contents match the local source files using SHA-256 checksums;
- record counts match the expected sample sizes;
- sample records can be printed from each file;
- seat records reference valid event and user IDs;
- seat booking status is consistent with `user_id`.
