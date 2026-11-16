# SQLite Database Schema Specification - VitalSync

This document outlines the database schema design for the VitalSync health and wellness platform. The target database is **SQLite**, which uses a dynamic type system with five storage affinities: `NULL`, `INTEGER`, `REAL`, `TEXT`, and `BLOB`. 

To support efficient indexing, range queries, and datetime functions, dates and timestamps are stored as **TEXT** conforming to the ISO-8601 standard (`YYYY-MM-DD` for calendar days and `YYYY-MM-DD HH:MM:SS` for timestamp logs).

---

## Entity Relationship Diagram

The database is structured around the `users` table as the central entity, with foreign key relationships linking health logs, user goals, and notification records.

```mermaid
erDiagram
    users ||--o{ steps : "tracks steps"
    users ||--o{ water_intake : "tracks hydration"
    users ||--o{ sleep_records : "tracks sleep"
    users ||--o{ heart_rate : "tracks pulse"
    users ||--o{ goals : "defines goals"
    users ||--o{ notifications : "receives"

    users {
        INTEGER id PK
        TEXT name
        TEXT email UNIQUE
        TEXT password_hash
        INTEGER age
        TEXT gender
        TEXT role
        TEXT created_at
    }

    steps {
        INTEGER id PK
        INTEGER user_id FK
        INTEGER count
        TEXT log_date UNIQUE
        TEXT logged_at
    }

    water_intake {
        INTEGER id PK
        INTEGER user_id FK
        REAL amount_ml
        TEXT log_date
        TEXT logged_at
    }

    sleep_records {
        INTEGER id PK
        INTEGER user_id FK
        REAL duration_hours
        TEXT log_date UNIQUE
        TEXT logged_at
    }

    heart_rate {
        INTEGER id PK
        INTEGER user_id FK
        INTEGER bpm
        TEXT log_date
        TEXT logged_at
    }

    goals {
        INTEGER id PK
        INTEGER user_id FK
        TEXT metric_type UNIQUE
        REAL target_value
        TEXT created_at
        TEXT updated_at
    }

    notifications {
        INTEGER id PK
        INTEGER user_id FK
        TEXT title
        TEXT message
        TEXT type
        INTEGER is_read
        TEXT created_at
    }
```

---

## Table Specification Details

### 1. `users` Table
Stores authentication details, demographic statistics, and role permissions.

| Column | Affinity Type | Keys & Indexes | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | PK | `AUTOINCREMENT` | Unique user identifier |
| `name` | `TEXT` | - | `NOT NULL` | User's full name |
| `email` | `TEXT` | Unique Index | `NOT NULL`, `UNIQUE` | Unique email for authentication |
| `password_hash`| `TEXT` | - | `NOT NULL` | Argon2/pbkdf2 security hash |
| `age` | `INTEGER` | - | `NOT NULL`, `CHECK(age > 0)` | User age in years |
| `gender` | `TEXT` | - | `NOT NULL`, `CHECK(gender IN ('male', 'female', 'other'))` | Self-reported gender identity |
| `role` | `TEXT` | - | `NOT NULL`, `DEFAULT 'user'`, `CHECK(role IN ('user', 'admin'))` | Access level ('user' or 'admin') |
| `created_at` | `TEXT` | - | `NOT NULL`, `DEFAULT (datetime('now', 'localtime'))` | Session creation timestamp |

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    age INTEGER NOT NULL CHECK(age > 0),
    gender TEXT NOT NULL CHECK(gender IN ('male', 'female', 'other')),
    role TEXT NOT NULL DEFAULT 'user' CHECK(role IN ('user', 'admin')),
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE UNIQUE INDEX idx_users_email ON users(email);
```

---

### 2. `steps` Table
Logs user steps. Uses a composite unique constraint `(user_id, log_date)` to represent a single consolidated step count per user per calendar day.

| Column | Affinity Type | Keys & Indexes | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | PK | `AUTOINCREMENT` | Log identifier |
| `user_id` | `INTEGER` | FK -> `users(id)` | `NOT NULL` | Link to user |
| `count` | `INTEGER` | - | `NOT NULL`, `CHECK(count >= 0)` | Step count |
| `log_date` | `TEXT` | Unique Index | `NOT NULL` | Target day (`YYYY-MM-DD`) |
| `logged_at` | `TEXT` | - | `NOT NULL`, `DEFAULT (datetime('now', 'localtime'))` | Actual tracking timestamp |

```sql
CREATE TABLE steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    count INTEGER NOT NULL CHECK(count >= 0),
    log_date TEXT NOT NULL,
    logged_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, log_date)
);

CREATE INDEX idx_steps_user_date ON steps(user_id, log_date);
```

---

### 3. `water_intake` Table
Logs water intake. Users log water intake incrementally throughout the day (e.g., adding +250ml or +500ml), so multiple records can exist per user for the same calendar date.

| Column | Affinity Type | Keys & Indexes | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | PK | `AUTOINCREMENT` | Log identifier |
| `user_id` | `INTEGER` | FK -> `users(id)` | `NOT NULL` | Link to user |
| `amount_ml` | `REAL` | - | `NOT NULL`, `CHECK(amount_ml > 0)` | Hydration in milliliters |
| `log_date` | `TEXT` | Index | `NOT NULL` | Target day (`YYYY-MM-DD`) |
| `logged_at` | `TEXT` | - | `NOT NULL`, `DEFAULT (datetime('now', 'localtime'))` | Actual tracking timestamp |

```sql
CREATE TABLE water_intake (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount_ml REAL NOT NULL CHECK(amount_ml > 0),
    log_date TEXT NOT NULL,
    logged_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_water_user_date ON water_intake(user_id, log_date);
```

---

### 4. `sleep_records` Table
Logs sleep duration. Enforces a composite uniqueness constraint on `(user_id, log_date)` to ensure exactly one sleep duration entry exists per user per day.

| Column | Affinity Type | Keys & Indexes | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | PK | `AUTOINCREMENT` | Log identifier |
| `user_id` | `INTEGER` | FK -> `users(id)` | `NOT NULL` | Link to user |
| `duration_hours` | `REAL` | - | `NOT NULL`, `CHECK(duration_hours >= 0.0 AND duration_hours <= 24.0)` | Sleep time in decimal hours |
| `log_date` | `TEXT` | Unique Index | `NOT NULL` | Target day (`YYYY-MM-DD`) |
| `logged_at` | `TEXT` | - | `NOT NULL`, `DEFAULT (datetime('now', 'localtime'))` | Actual tracking timestamp |

```sql
CREATE TABLE sleep_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    duration_hours REAL NOT NULL CHECK(duration_hours >= 0.0 AND duration_hours <= 24.0),
    log_date TEXT NOT NULL,
    logged_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, log_date)
);

CREATE INDEX idx_sleep_user_date ON sleep_records(user_id, log_date);
```

---

### 5. `heart_rate` Table
Logs raw heart rate readings. Because heart rate varies and users can measure it multiple times per day (e.g. resting vs active), multiple entries per user per day are permitted.

| Column | Affinity Type | Keys & Indexes | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | PK | `AUTOINCREMENT` | Log identifier |
| `user_id` | `INTEGER` | FK -> `users(id)` | `NOT NULL` | Link to user |
| `bpm` | `INTEGER` | - | `NOT NULL`, `CHECK(bpm >= 30 AND bpm <= 250)` | Heart beats per minute |
| `log_date` | `TEXT` | Index | `NOT NULL` | Target day (`YYYY-MM-DD`) |
| `logged_at` | `TEXT` | Index | `NOT NULL`, `DEFAULT (datetime('now', 'localtime'))` | Timestamp of measurement |

```sql
CREATE TABLE heart_rate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    bpm INTEGER NOT NULL CHECK(bpm >= 30 AND bpm <= 250),
    log_date TEXT NOT NULL,
    logged_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_heart_user_date ON heart_rate(user_id, log_date);
CREATE INDEX idx_heart_user_time ON heart_rate(user_id, logged_at);
```

---

### 6. `goals` Table
Defines active goals for a user. The composite constraint `UNIQUE(user_id, metric_type)` limits each user to one active goal per monitored category.

| Column | Affinity Type | Keys & Indexes | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | PK | `AUTOINCREMENT` | Goal identifier |
| `user_id` | `INTEGER` | FK -> `users(id)` | `NOT NULL` | Link to user |
| `metric_type` | `TEXT` | Unique Index | `NOT NULL`, `CHECK(metric_type IN ('steps', 'water', 'sleep'))` | Metric target type |
| `target_value` | `REAL` | - | `NOT NULL`, `CHECK(target_value > 0)` | Target numerical value |
| `created_at` | `TEXT` | - | `NOT NULL`, `DEFAULT (datetime('now', 'localtime'))` | Creation timestamp |
| `updated_at` | `TEXT` | - | `NOT NULL`, `DEFAULT (datetime('now', 'localtime'))` | Last modification timestamp |

```sql
CREATE TABLE goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    metric_type TEXT NOT NULL CHECK(metric_type IN ('steps', 'water', 'sleep')),
    target_value REAL NOT NULL CHECK(target_value > 0),
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, metric_type)
);

CREATE INDEX idx_goals_user ON goals(user_id);
```

---

### 7. `notifications` Table
Manages user notifications. Supports status tracking (`is_read`) using SQLite's numeric representation for booleans (`0` for False, `1` for True).

| Column | Affinity Type | Keys & Indexes | Constraints / Defaults | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | PK | `AUTOINCREMENT` | Notification identifier |
| `user_id` | `INTEGER` | FK -> `users(id)` | `NOT NULL` | Link to recipient |
| `title` | `TEXT` | - | `NOT NULL` | Brief alert header |
| `message` | `TEXT` | - | `NOT NULL` | Notification message text |
| `type` | `TEXT` | - | `NOT NULL`, `DEFAULT 'info'`, `CHECK(type IN ('info', 'goal_reached', 'warning'))` | Alert classification |
| `is_read` | `INTEGER` | Index | `NOT NULL`, `DEFAULT 0`, `CHECK(is_read IN (0, 1))` | Read status flag (Boolean) |
| `created_at` | `TEXT` | - | `NOT NULL`, `DEFAULT (datetime('now', 'localtime'))` | Issue timestamp |

```sql
CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'info' CHECK(type IN ('info', 'goal_reached', 'warning')),
    is_read INTEGER NOT NULL DEFAULT 0 CHECK(is_read IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_notifications_user_read ON notifications(user_id, is_read);
```

---

## Core SQL Aggregations for Backend Endpoints

### 1. Dashboard Goals Progress (Steps, Water, Sleep)
Fetches configured target values alongside actual computed daily totals.
```sql
SELECT 
    g.metric_type,
    g.target_value,
    COALESCE(
        CASE 
            WHEN g.metric_type = 'steps' THEN (SELECT SUM(count) FROM steps WHERE user_id = g.user_id AND log_date = date('now', 'localtime'))
            WHEN g.metric_type = 'water' THEN (SELECT SUM(amount_ml) FROM water_intake WHERE user_id = g.user_id AND log_date = date('now', 'localtime'))
            WHEN g.metric_type = 'sleep' THEN (SELECT SUM(duration_hours) FROM sleep_records WHERE user_id = g.user_id AND log_date = date('now', 'localtime'))
        END, 
        0
    ) AS logged_value
FROM goals g
WHERE g.user_id = ?;
```

### 2. Steps UPSERT Pattern
Ensures dynamic tracking where incremental step entries compile safely under a unique daily total.
```sql
INSERT INTO steps (user_id, count, log_date)
VALUES (?, ?, ?)
ON CONFLICT(user_id, log_date) 
DO UPDATE SET 
    count = count + excluded.count,
    logged_at = datetime('now', 'localtime');
```

### 3. Weekly Analytics (Last 7 Days)
Fetches user data aggregates grouped by day to render visual graphs on the dashboard.
```sql
SELECT 
    d.day AS log_date,
    COALESCE(SUM(s.count), 0) AS total_steps,
    COALESCE(SUM(w.amount_ml), 0) AS total_water_ml,
    COALESCE(AVG(sl.duration_hours), 0.0) AS avg_sleep_hours,
    COALESCE(AVG(h.bpm), 0.0) AS avg_heart_bpm
FROM (
    -- Generates calendar dates for the past 7 days
    SELECT date('now', 'localtime', '-' || n || ' days') AS day 
    FROM (SELECT 0 AS n UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6)
) d
LEFT JOIN steps s ON s.user_id = ? AND s.log_date = d.day
LEFT JOIN water_intake w ON w.user_id = ? AND w.log_date = d.day
LEFT JOIN sleep_records sl ON sl.user_id = ? AND sl.log_date = d.day
LEFT JOIN heart_rate h ON h.user_id = ? AND h.log_date = d.day
GROUP BY d.day
ORDER BY d.day ASC;
```
