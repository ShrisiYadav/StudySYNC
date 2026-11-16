# Implementation Plan - VitalSync Health & Wellness Platform

VitalSync is a web-based health and wellness tracking platform designed to help users monitor, manage, and improve their daily health habits. This document provides a detailed implementation roadmap for the codebase structure, database models, backend API specifications, frontend styling system, user tracking modules, dynamic notifications, and the administrative console.

---

## Technical Stack & Architecture

### Backend
- **Framework:** Python Flask (lightweight, modular routing)
- **Database:** SQLite (local database file `database.db`)
- **Authentication:** Token-based security using JSON Web Tokens (JWT) stored in HTTPOnly cookies to prevent XSS-based theft
- **Security Utilities:** `Werkzeug` for password hashing and verification

### Frontend
- **Structure:** Semantic HTML5
- **Style System:** Vanilla CSS3 utilizing a modern Glassmorphism theme, dark mode defaults, fluid grids, and CSS custom properties for cohesive HSL color schemes
- **Logic:** Native modern JavaScript (ES6+), using fetch APIs for async server interactions
- **Visuals & Charts:** Chart.js loaded via secure CDN for responsive data visualizations

---

## Folder Structure Mapping

The project files will be structured inside the [Client](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Client) and [Server](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Server) directories:

```
VitalSync/
│
├── PRD.md
├── Technical_Design.md
├── API_Specification.md
├── IMPLEMENTATION_PLAN.md
│
├── Server/
│   ├── app.py                  # Main entrypoint & App configuration
│   ├── database.py             # SQLite helper and DB connection management
│   ├── schema.sql              # Database table definition scripts
│   ├── requirements.txt        # Python dependency manifest
│   └── routes/                 # Flask modular Blueprints
│       ├── auth.py             # User authentication routes
│       ├── health.py           # Health metrics logging/management
│       ├── goals.py            # Personal goals creation/tracking
│       ├── analytics.py        # Trend summaries and aggregation
│       └── admin.py            # User management and platform metrics
│
└── Client/
    ├── index.html              # Marketing/Landing page
    ├── auth.html               # Combined Login & Signup page
    ├── dashboard.html          # Main User Dashboard & tracking page
    ├── admin.html              # Administrator Management console
    ├── css/
    │   ├── main.css            # Global CSS variables, reset, layout, and glassmorphic designs
    │   ├── auth.css            # Styling for the authentication views
    │   ├── dashboard.css       # Core styling for data grids, tracking widgets, and charts
    │   └── admin.css           # Table layouts, analytic metrics cards, and logs management
    └── js/
        ├── api.js              # Centralized fetch wrapper & routing config
        ├── auth.js             # Client session checking, registration, & login scripts
        ├── dashboard.js        # Form tracking submissions, goal gauges, and Chart.js integration
        └── admin.js            # User searching, invalid log deletion, and platform charts
```

---

## Database Schema Design

SQLite tables will structure the storage model. Relationships are illustrated below:

```mermaid
erDiagram
    users ||--o{ health_logs : "tracks"
    users ||--o{ goals : "defines"
    
    users {
        integer id PK
        string name
        string email UNIQUE
        string password_hash
        integer age
        string gender
        string role
        timestamp created_at
    }

    health_logs {
        integer id PK
        integer user_id FK
        string metric_type
        real value
        string log_date
        timestamp timestamp
    }

    goals {
        integer id PK
        integer user_id FK
        string metric_type
        real target_value
        timestamp updated_at
    }
```

### Table Definitions

#### 1. `users`
Tracks both standard users and platform administrators.
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    role TEXT DEFAULT 'user', -- 'user' or 'admin'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. `health_logs`
A unified table capturing all dynamic activities (steps, water, sleep, and heart rate).
```sql
CREATE TABLE health_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    metric_type TEXT CHECK(metric_type IN ('steps', 'water', 'sleep', 'heart_rate')) NOT NULL,
    value REAL NOT NULL,
    log_date TEXT NOT NULL, -- YYYY-MM-DD format for aggregation
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX idx_logs_user_date ON health_logs(user_id, log_date);
```

#### 3. `goals`
Maintains goals configured by users for steps, water, and sleep.
```sql
CREATE TABLE goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    metric_type TEXT CHECK(metric_type IN ('steps', 'water', 'sleep')) NOT NULL,
    target_value REAL NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, metric_type)
);
```

---

## REST API Specification

### Authentication Module

*   **POST** `/api/auth/register`
    *   **Body:** `{"name": "Rahul", "email": "rahul@email.com", "password": "SecurePassword123", "age": 20, "gender": "male"}`
    *   **Response (201):** `{"message": "Registration successful", "user_id": 1}`
*   **POST** `/api/auth/login`
    *   **Body:** `{"email": "rahul@email.com", "password": "SecurePassword123"}`
    *   **Response (200):** `{"message": "Login successful", "user": {"name": "Rahul", "email": "rahul@email.com", "role": "user"}}` (sets HttpOnly token cookie)
*   **POST** `/api/auth/logout`
    *   **Response (200):** `{"message": "Logged out successfully"}`
*   **GET** `/api/auth/me`
    *   **Response (200):** `{"id": 1, "name": "Rahul", "email": "rahul@email.com", "age": 20, "gender": "male", "role": "user"}`

### Health Tracking Module

*   **POST** `/api/health/log`
    *   **Body:** `{"metric_type": "steps", "value": 8500, "date": "2026-06-04"}` (defaults to today if date is omitted)
    *   **Response (201):** `{"message": "Activity log saved successfully", "log_id": 42}`
*   **GET** `/api/health/history`
    *   **Parameters:** `metric_type` (optional), `start_date` (optional), `end_date` (optional)
    *   **Response (200):** `{"logs": [{"id": 42, "metric_type": "steps", "value": 8500, "log_date": "2026-06-04", "timestamp": "2026-06-04 18:30:00"}]}`
*   **DELETE** `/api/health/log/<id>`
    *   **Response (200):** `{"message": "Health record deleted successfully"}`

### Goal Management Module

*   **POST** `/api/goals`
    *   **Body:** `{"metric_type": "steps", "target_value": 10000}`
    *   **Response (200):** `{"message": "Goal updated successfully"}`
*   **GET** `/api/goals`
    *   **Response (200):** `{"goals": {"steps": 10000, "water": 2500, "sleep": 8}, "progress": {"steps": {"logged": 8500, "percentage": 85.0}, "water": {"logged": 1500, "percentage": 60.0}, "sleep": {"logged": 7.5, "percentage": 93.75}}}`

### Analytics Module

*   **GET** `/api/analytics/trends`
    *   **Parameters:** `days` (default 7, supports 30)
    *   **Response (200):** Aggregated metrics grouped by date for rendering line and bar charts.
    *   **Structure:** `{"dates": ["2026-05-29", ...], "steps": [8000, ...], "water": [2000, ...], "sleep": [7.0, ...], "heart_rate": [72, ...]}`

### Admin Dashboard Module

*   **GET** `/api/admin/users`
    *   **Parameters:** `search` (optional)
    *   **Response (200):** `{"users": [{"id": 2, "name": "Priya", "email": "priya@email.com", "role": "user", "created_at": "2026-05-15"}]}`
*   **DELETE** `/api/admin/users/<id>`
    *   **Response (200):** `{"message": "User account and all linked records removed"}`
*   **GET** `/api/admin/records`
    *   **Response (200):** A system-wide list of health logs.
    *   **Structure:** `{"records": [{"id": 105, "user_name": "Rahul", "metric_type": "heart_rate", "value": 180, "log_date": "2026-06-04"}]}`
*   **DELETE** `/api/admin/records/<id>` (allows admins to remove erroneous or invalid data)
    *   **Response (200):** `{"message": "Record deleted"}`
*   **GET** `/api/admin/metrics`
    *   **Response (200):** System performance and enrollment statistics.
    *   **Structure:** `{"total_users": 15, "total_logs": 348, "active_today": 8, "growth": {"dates": ["2026-05", "2026-06"], "users": [10, 15]}}`

---

## Detailed Implementation Roadmap

### Phase 1: Project Setup & Workspace Initialization
1.  **Backend Structure Initialization:**
    *   Create [requirements.txt](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Server/requirements.txt) with dependencies: `Flask`, `Flask-CORS`, `PyJWT`, `cryptography`.
    *   Implement [database.py](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Server/database.py) to manage SQLite connection pools and handle SQL scripts.
    *   Write a SQL schema file [schema.sql](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Server/schema.sql) defining the `users`, `health_logs`, and `goals` tables.
    *   Create [app.py](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Server/app.py) with registration configurations for routing Blueprints.
2.  **Frontend Design Tokens Setup:**
    *   Create [main.css](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Client/css/main.css) defining modern design properties:
        *   **Typography:** Google Font `Inter` and `Outfit` for smooth weights.
        *   **Color Palette (HSL):** Theme colors (indigo background, emerald steps, sky water, coral heart rate).
        *   **Glassmorphic styling classes:**
            ```css
            .glass-panel {
                background: rgba(255, 255, 255, 0.04);
                backdrop-filter: blur(16px);
                border: 1px solid rgba(255, 255, 255, 0.08);
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
                border-radius: 16px;
            }
            ```
        *   **Animations:** Glow keyframes and hover scale micro-animations (`transform: scale(1.02); transition: all 0.3s ease;`).
3.  **Core Frontend Shell & API Client:**
    *   Write [index.html](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Client/index.html) as the application portal.
    *   Write [api.js](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Client/js/api.js) handling server fetch headers, parsing errors, and automatically including cookie credentials.

### Phase 2: Secure User Authentication
1.  **Backend Auth Blueprints ([auth.py](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Server/routes/auth.py)):**
    *   Define validation metrics (valid email structure, password constraints, positive age ranges).
    *   Build secure signup using password hashing via `generate_password_hash`.
    *   Implement token authentication: sign JWT tokens, write standard token checking middleware, and set JWT tokens in HttpOnly cookies upon successful login.
2.  **Frontend Auth UI ([auth.html](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Client/auth.html) & [auth.js](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Client/js/auth.js)):**
    *   Design a unified glassmorphic card allowing switching between "Login" and "Create Account" panels.
    *   Implement interactive front-end validations (e.g., matching passwords, password strength bar).
    *   Store session states dynamically and handle routing redirects.

### Phase 3: Core Health Tracking Modules
1.  **Backend Logic ([health.py](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Server/routes/health.py)):**
    *   Implement user verification checks.
    *   Build `POST /api/health/log` to record steps, water (ml), sleep (hours), or heart rate (bpm) and parse dates.
    *   Build deletion and list endpoints.
2.  **Frontend Interactive Controls:**
    *   In [dashboard.html](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Client/dashboard.html), create visual logging controls:
        *   **Steps tracker:** Input field with a step counter selector.
        *   **Hydration tracker:** Quick add buttons (+250ml, +500ml) with an animation showing a water-fill level.
        *   **Sleep tracker:** Simple sliding slider for duration.
        *   **Heart rate tracker:** Numerical field with category descriptors (Resting, Active, Peak).
    *   Handle async submission updates in [dashboard.js](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Client/js/dashboard.js) without page reloads.

### Phase 4: Goal Management Module
1.  **Goal DB & Endpoints ([goals.py](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Server/routes/goals.py)):**
    *   Build endpoints to configure goals for Steps, Water, and Sleep.
    *   Implement a progress calculation query: aggregate daily health log sums and compare with target goals.
2.  **Frontend Progress Gauges:**
    *   Show tracking progress using circular SVG rings on the dashboard.
    *   Animate the gauge progress as values update to reward users visually upon hitting 100%.

### Phase 5: Dashboard & Analytics Engine
1.  **Historical Trends Route ([analytics.py](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Server/routes/analytics.py)):**
    *   Aggregate metrics by daily calendar date (summing steps and water, averaging sleep hours and heart rate readings).
2.  **Dashboard Visual Chart Engine:**
    *   Embed Chart.js into [dashboard.html](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Client/dashboard.html).
    *   Initialize multiple chart configurations inside [dashboard.js](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Client/js/dashboard.js):
        *   *Steps vs Goals:* Combined bar/line chart.
        *   *Hydration Trends:* Area chart showing weekly hydration patterns.
        *   *Sleep Patterns:* Bar chart displaying sleep duration.
        *   *Heart Rate:* Line chart mapping heart rate changes.

### Phase 6: Dynamic In-App Notifications & Alerts
1.  **Frontend Notification Banner:**
    *   Implement a subtle floating alert banner (toast notifications) in [dashboard.html](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Client/dashboard.html).
2.  **Trigger Notifications:**
    *   Implement Javascript triggers checking user statistics:
        *   *Hydration reminder:* If water consumption is under 50% of the daily goal by 3 PM local time.
        *   *Activity congratulator:* A custom confetti alert when step goals are reached.
        *   *Heart rate warning:* Alerts if a logged heart rate is abnormally high (>150 bpm) or low (<50 bpm).

### Phase 7: Administrative Dashboard
1.  **Security Enforcements ([admin.py](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Server/routes/admin.py)):**
    *   Restrict endpoints to users where `role = 'admin'` based on the JWT token.
2.  **Admin UI & Features ([admin.html](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Client/admin.html) & [admin.js](file:///c:/Users/SHRISTI YADAV/OneDrive/Desktop/Vital Sync/Client/js/admin.js)):**
    *   **User Registry Panel:** Clean search grid displaying active accounts, profile parameters, and account age.
    *   **Records Table:** Live log listing from all users with an action button allowing administrators to purge corrupt data logs.
    *   **Platform Insights:** Visual graphs tracking registration metrics, platform engagement indices, and average user health records.

---

## Verification & Testing Plan

### Automated Verification
To ensure functional compliance across modules, the following verification checks will be run:

```bash
# 1. Start backend server
python Server/app.py

# 2. Execute verification script
python Server/tests/test_endpoints.py
```

*   **Endpoint Unit Tests:** Script covering `/api/auth/*`, `/api/health/*`, and `/api/goals/*` APIs using mocked database connections.
*   **Security Access Control:** Verification that admin endpoints return a `403 Forbidden` status code for regular user tokens.

### Manual Verification
1.  **Mobile Layout Check:** Emulate responsive configurations in Chrome/Edge DevTools (iPhone, iPad, Desktop). Validate navigation bar responsiveness and verify grid adjustments on the analytics panels.
2.  **Dashboard Flow:**
    *   Register a user with an age of 25 and gender of female.
    *   Log in and configure a step goal of 10,000 steps.
    *   Log steps using the dashboard interface and verify real-time chart rendering updates.
    *   Simulate admin login on a separate window, verify user lookup, locate the newly logged record, and verify data removal.
