# Data Model & Sample Data — Distributed Ticket Reservation System

## Part 1: Data Collection & Storage

This document defines the data schema for the three core entities — **Events**, **Seats**,
and **Users** — and shows how the sample data files match that schema. This structure is
reused by every other part of the project (processing, analysis, presentation), so all
scripts that read from HDFS should assume this format.

---

## 1. Entities

### Events

| Field         | Type     | Key | Description                                      |
|---------------|----------|-----|---------------------------------------------------|
| `event_id`    | string   | PK  | Unique identifier for the event (e.g. `E001`)      |
| `name`        | string   |     | Event title                                       |
| `venue`       | string   |     | Name of the venue                                 |
| `location`    | string   |     | City where the venue is located                   |
| `date_time`   | datetime |     | Date and time of the event (ISO 8601)             |
| `category`    | string   |     | Concert, Sports, Theater, Conference, Comedy, etc. |
| `total_seats` | int      |     | Total seat capacity for the event                 |
| `status`      | string   |     | `upcoming` / `ongoing` / `completed` / `cancelled` |

**Sample file:** `data/events.csv`
**Sample row:**
```
E001,Coldplay World Tour,Cairo International Stadium,Cairo,2026-09-15T20:00:00,Concert,5000,upcoming
```

---

### Seats

| Field         | Type          | Key | Description                                                |
|---------------|---------------|-----|-------------------------------------------------------------|
| `seat_id`     | string        | PK  | Unique identifier for the seat (e.g. `S00001`)              |
| `event_id`    | string        | FK  | References `Events.event_id`                                |
| `section`     | string        |     | Seating section (e.g. `A`, `B`, `C`, `VIP`)                  |
| `row`         | string        |     | Row number within the section                                |
| `seat_number` | string        |     | Seat number within the row                                   |
| `price`       | decimal       |     | Ticket price for this seat                                   |
| `status`      | string        |     | `available` / `booked`                                       |
| `user_id`     | string / null | FK  | References `Users.user_id`; `null` if seat is not booked      |

**Sample file:** `data/seats.json`
**Sample record:**
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

---

### Users

| Field                | Type   | Key | Description                          |
|----------------------|--------|-----|---------------------------------------|
| `user_id`            | string | PK  | Unique identifier for the user (e.g. `U001`) |
| `name`               | string |     | Full name                             |
| `email`              | string |     | Contact email                         |
| `phone`              | string |     | Contact phone number                  |
| `registration_date`  | date   |     | Date the user registered              |

**Sample file:** `data/users.csv`
**Sample row:**
```
U001,Ahmed Farouk,ahmed.farouk@example.com,01012345678,2025-01-12
```

---

## 2. Relationships

```
Events (1) ────< (many) Seats >──── (many) Users (1)
```

- **One Event has many Seats** — each seat belongs to exactly one event, via `Seats.event_id`.
- **One User can book many Seats** — across different events, via `Seats.user_id`.
- There is **no direct relationship** between Events and Users — they are only connected
  through the Seats entity, which acts as both the seat record and the booking record.

**Design note:** Booking information (`status`, `user_id`) is stored directly on each Seat
row rather than in a separate `Bookings` entity. This keeps the model simple for the scope
of this project. A separate Bookings table (with `booking_id`, `booking_time`, `payment_status`)
would be a natural extension if booking history needs to be preserved across rebookings.

---

## 3. Sample Data Summary

| File            | Format | Records | Matches Entity |
|------------------|--------|---------|-----------------|
| `data/events.csv`| CSV    | 10      | Events          |
| `data/users.csv` | CSV    | 15      | Users           |
| `data/seats.json`| JSON   | 60      | Seats           |

- All `event_id` values in `seats.json` correspond to an `event_id` in `events.csv`.
- All non-null `user_id` values in `seats.json` correspond to a `user_id` in `users.csv`.
- Both CSV and JSON formats are represented across the sample data, so upload/read-back
  scripts can be tested against both.

---

## 4. HDFS Storage Structure

Once uploaded, this data is organized in HDFS as follows:

```
/data/events.csv
/data/seats.json
/data/users.csv
```

Each folder holds only its corresponding entity's data, keeping the storage layer aligned
with the schema defined above. This is the structure all downstream parts of the project
(processing, analysis, presentation) should read from.
