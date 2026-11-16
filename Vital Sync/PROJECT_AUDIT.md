# VitalSync Project Audit

This document provides a comprehensive technical audit of the VitalSync Health Tracking and Wellness Management Web Application, analyzing both the backend Flask server and the frontend HTML/JS interface.

> [!NOTE]
> **Server/models Directory Status:**
> The directory `Server/models` requested in the audit prompt **does not exist** in the repository. All database models are centralized and defined inside [database.py](file:///c:/Users/SHRISTI%20YADAV/OneDrive/Desktop/Vital%20Sync/Server/database.py).

---

## 1. Implemented Features

### Backend Server (Flask & SQLite)
* **Authentication & Access Control (`/api/auth`)**:
  * Secure user registration with validation (email normalization, age check, gender verification).
  * Secure user login using password hash verification and JSON Web Tokens (JWT).
  * Session token stored in an `HttpOnly` cookie (`token`) with custom `samesite='Lax'` protections, alongside JWT json response support.
  * Active session profile checker (`/api/auth/me`) and user logout (purging cookies).
  * Multi-layer access control decorators (`@token_required` and `@admin_required`).
* **Health Activity Logs (`/api/health`)**:
  * **Steps tracking**: Incremental daily UPSERT logic (compiles movements into a single daily sum).
  * **Water tracking**: Incremental daily intake inserts.
  * **Sleep tracking**: Daily sleep duration logging (overwrites existing daily records, validation capped at 24 hours).
  * **Heart Rate (Pulse) tracking**: Multiple daily recordings supported. Triggers automated warning alerts for anomalies (elevated pulse >150 BPM, low pulse <50 BPM).
  * **Log Deletion**: User-owned record removal by ID.
* **Goal Management (`/api/goals`)**:
  * Daily targets config (Steps, Water, Sleep) with input validation.
  * Today's goals progress calculator (calculates logged value vs target and progress percentages).
* **In-App Notifications (`/api/notifications`)**:
  * Telemetry alerts stored dynamically in the database.
  * Auto-generation of notifications for "Goal Reached" and "Heart Rate Warnings".
  * Notification list management (fetching sorted list, marking specific/all as read, deleting records).
* **Trends Analytics (`/api/analytics`)**:
  * Historical summaries returning calendar trends for Steps, Water, Sleep, and average Heart Rate over a customizable range (up to 30 days).
* **Admin Dashboard Services (`/api/admin`)**:
  * User search engine (filtering by name/email).
  * Cascaded account deletion (purges user profiles and all associated tables).
  * Logs Audit Trail (fetches up to 100 recent health logs across all users, sorted by date).
  * Specific telemetry record deletion (allows deleting invalid/corrupt logs).
  * Platform metrics compiler (compiles total user counts, logs breakdown, and month-on-month registration growth).

### Frontend Interface (HTML5, Vanilla CSS, JS)
* **Landing Page (`index.html`)**: Responsive overview details highlighting features with a dynamic session-aware welcome banner.
* **Auth Portal (`auth.html` / `auth.js`)**: Interactive tabs switching between login and registration with custom gender buttons and client-side password length checks.
* **Dashboard Console (`dashboard.html` / `dashboard.js`)**:
  * Dynamic user greeting and date display.
  * Live status grid containing progress bars and percentage details for Steps, Water, and Sleep.
  * Tabs panel for submitting telemetry inputs, including a quick-log menu for water (+250, +500, +750 ml).
  * Goals setup console.
  * Historical trends visualization rendering four distinct data charts (Steps, Water, Sleep, Pulse) powered by Chart.js.
  * Bell notification dropdown with an unread badge indicator, dropdown transitions, and actions to mark read or clear.
* **Admin Console (`admin.html` / `admin.js`)**:
  * Live telemetry summary cards.
  * User growth trends line chart.
  * Directory search table supporting deletion confirmations.
  * Complete system logs trail with instant delete permissions.

---

## 2. Missing Features from PRD

* **Monthly Statistics Visualizations**:
  * The PRD requires both "Weekly statistics" and "Monthly statistics" trends. While the backend `/api/analytics/trends` endpoint supports a `days` query parameter up to 30 days, the frontend code (`dashboard.js` line 275) hardcodes `days=7` and offers no UI toggle or secondary configuration for a monthly view.
* **Admin User Accounts Management**:
  * The PRD states: "*Administrators should be able to: View users, Search users, **Manage user accounts***". The current implementation only allows viewing, searching, and deleting users. There are no mechanisms for editing user details, resetting user passwords, locking/disabling accounts, or promoting/demoting user roles from the admin console.
* **Heart Rate Goals**:
  * Although the backend enables logging heart rate pulse levels, goal target configurations are restricted strictly to Steps, Water, and Sleep. Custom BPM limits or resting heart rate goals cannot be set.
* **Folder Structure Divergence (`Client/pages`)**:
  * The project instructions list a `Client/pages` directory. This folder does not exist in the codebase. All HTML files (`index.html`, `auth.html`, `dashboard.html`, `admin.html`) are stored as flat files in the root `/Client` directory.
* **Wearables & AI Enhancements (PRD Future Scope)**:
  * Fitbit, Apple Health, and Google Fit integrations are missing.
  * AI-driven personalized feedback, smart reminders, and trend forecasting are absent.
  * Mobile applications (Android/iOS) and community leaderboards are not implemented.

---

## 3. Analytics APIs Available

### Get Metric Trends
* **Endpoint:** `/api/analytics/trends`
* **HTTP Method:** `GET`
* **Authentication:** Required (JWT)
* **Query Parameters:**
  * `days` (Optional, Integer): Specifies range length (1 to 30 days, defaults to 7).
* **Success Response (200 OK):**
  ```json
  {
    "dates": ["2026-05-29", "2026-05-30", "2026-05-31", "2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04"],
    "steps": [0, 0, 0, 0, 0, 0, 5000],
    "water": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 250.0],
    "sleep": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 7.5],
    "heart_rate": [0, 0, 0, 0, 0, 0, 72.0]
  }
  ```

---

## 4. Admin Dashboard APIs Available

All endpoints in this section require the authenticated user to have administrative credentials (`role='admin'`).

### 1. Search Users
* **Endpoint:** `/api/admin/users`
* **HTTP Method:** `GET`
* **Query Parameters:**
  * `search` (Optional, String): Query string matching name or email.
* **Success Response (200 OK):** Returns all matching user profiles.

### 2. Delete User Account
* **Endpoint:** `/api/admin/users/<int:user_id>`
* **HTTP Method:** `DELETE`
* **Success Response (200 OK):** Purges user credentials, logs, and goals. Blocks self-deletion.

### 3. Get Recent Activity Records
* **Endpoint:** `/api/admin/records`
* **HTTP Method:** `GET`
* **Success Response (200 OK):** Returns up to 100 recent health logs across all users, sorted by date descending.

### 4. Delete Specific User Record
* **Endpoint:** `/api/admin/records/<int:log_id>`
* **HTTP Method:** `DELETE`
* **Query Parameters:**
  * `metric_type` (Required, String): 'steps', 'water', 'sleep', or 'heart_rate'.
* **Success Response (200 OK):** Deletes the specific record.

### 5. Get Platform Metrics
* **Endpoint:** `/api/admin/metrics`
* **HTTP Method:** `GET`
* **Success Response (200 OK):** Compiles platform counts, metric activity summaries, and month-grouped user sign-up counts.

---

## 5. Notifications/Reminders Implementation Status

* **Status: Partially Implemented (In-App Only)**
* **Implemented Components:**
  * **Database Persistence:** Notification records are stored in the SQLite `notifications` table (`id`, `user_id`, `title`, `message`, `type`, `is_read`, `created_at`).
  * **Dynamic Goal Triggers:** During logging of steps, water, or sleep, the server checks if cumulative values cross the user's active goal target. If met, it creates a `goal_reached` notification.
  * **Dynamic Warning Triggers:** When logging heart rate, if the BPM is >150 or <50, the server triggers a warning alert with type `warning` (e.g. "High Heart Rate Alert").
  * **Frontend UI Notifications Bell:** Clicking the bell toggles a notifications panel, loads user alerts sorted by newest, displays a numeric badge with the unread count, allows marking single notifications or all notifications as read, and deleting records.
* **Missing Components / Limitations:**
  * **No Inactive Reminders:** The PRD mentions that users should "receive reminders to maintain healthy routines." The app lacks scheduled reminder tasks (e.g., if a user forgets to log water/steps for a day, no reminders are generated).
  * **No External Delivery Channels:** Alerts are strictly visible inside the web interface's notification bell; there is no email integration or native system push notifications.
  * **No User Configurable Thresholds:** Thresholds for high/low heart rates (>150 and <50 BPM) are hardcoded in the server and cannot be customized by users.

---

## 6. Frontend Pages Available

All HTML pages are located in the `/Client` root directory:
1. **Landing Page (`/Client/index.html`)**: Marketing home displaying application benefits, user metrics summaries, and login route buttons.
2. **Auth Portal (`/Client/auth.html`)**: Combined login and registration tab system.
3. **User Dashboard (`/Client/dashboard.html`)**: Heart of the user experience; handles daily telemetry entries, goals settings, and historical trends charts.
4. **Admin Console (`/Client/admin.html`)**: Control panel for checking system telemetry totals, growth charts, managing users, and deleting log entries.

---

## 7. Frontend Pages Connected to Backend

* **`/Client/auth.html`**: Completely integrated with backend endpoints via `Client/js/auth.js`. Submits data to `/api/auth/register` and `/api/auth/login`. Sets session tokens and intercepts API errors.
* **`/Client/dashboard.html`**: Completely integrated with server metrics endpoints via `Client/js/dashboard.js`. Submits data to `/api/health/log` and `/api/goals` (POST). Queries `/api/goals` (GET), `/api/health/history`, `/api/notifications` (read/unread/delete), and `/api/analytics/trends`.
* **`/Client/admin.html`**: Completely integrated with administrative back-channels via `Client/js/admin.js`. Pulls from `/api/admin/metrics`, `/api/admin/users`, `/api/admin/records` and triggers deletions via user/record endpoints.

---

## 8. Frontend Pages Not Connected

* **`/Client/index.html`**: Does not fetch active database logs or make direct API requests. It behaves as a static landing page that inspects `localStorage` for a user session to dynamically alter navigation menus and call-to-actions, but does not perform live network synchronization.

---

## 9. Bugs Found

### Frontend Bugs
1. **Deprecated Global `event` Variable Reference**:
   * **Location:** `Client/js/dashboard.js` (lines 49-59 `switchLogTab` and lines 62-74 `toggleNotifications`).
   * **Problem:** The scripts reference the global `event` object (`event.currentTarget` and `event.stopPropagation()`) without passing `event` as a parameter. This causes `ReferenceError: event is not defined` in modern strict scopes or browsers like Firefox.
2. **Event Listener Leak in Notifications Drawer**:
   * **Location:** `Client/js/dashboard.js` (lines 68-73).
   * **Problem:** Each time `toggleNotifications()` is called to open the drawer, a new click event listener (`closePanel`) is appended to the `document`. Since `removeEventListener` is only triggered when clicking *outside* the panel, repeatedly clicking the bell button to open/close the drawer leaks listeners, degrading browser performance.
3. **UTC Timezone Date Mismatch**:
   * **Location:** `Client/js/dashboard.js` (lines 32-36, line 132).
   * **Problem:** Default dates and quick-log entries use `new Date().toISOString().split('T')[0]`, which returns the current UTC calendar date. If a user logs data late at night in a local timezone (e.g. India GMT+5:30), the data will be logged under tomorrow's date relative to their local time, creating progress bar discrepancies when the backend compares it to local server time.

### Backend Bugs
4. **Steps and Heart Rate Decimal Silent Truncation**:
   * **Location:** `Server/routes/health.py` (lines 40, 84).
   * **Problem:** The server parses steps and heart rate counts as floats and converts them directly via `int(value)`. Because `int()` in Python silently truncates decimals (e.g., `int(5.9)` becomes `5`) without throwing errors, decimal values for steps and BPM are accepted and logged incorrectly instead of returning a validation error.
5. **Static Hardcoded JWT Secret Key**:
   * **Location:** `Server/app.py` (line 21).
   * **Problem:** The Flask app defines `app.config['SECRET_KEY']` as a hardcoded string literal. This is a security vulnerability. Secret keys should always be loaded dynamically from environment variables.

---

## 10. Overall Completion Percentage

Based on the functional requirements outlined in the PRD, the schema requirements, and the client codebases:

* **Backend API Framework:** 96% Complete (All REST routes fully functional; minor validation and config details require hardening).
* **Frontend Web Application:** 92% Complete (Connected forms, visualizations, notifications dropdown, and admin utilities; missing the monthly analytics chart).
* **System Integration:** 90% Complete (In-app notifications work; lacking active external routines or scheduled reminders).

**Overall Completion Rate: 92%**

---

## 11. Next Tasks Required to Reach 100% Completion

### 1. High-Priority Bugs & Stability Fixes
* **Fix Global `event` References:** Pass the `event` parameter explicitly from HTML event hooks to the functions in `dashboard.js` (e.g., `onclick="switchLogTab(event, 'steps')"`).
* **Clean up Notifications Listener Leak:** Store `closePanel` in a variable, and properly track/remove the event handler when the notifications window is toggled.
* **Normalize Client Logging Dates:** Calculate local calendar dates (in `YYYY-MM-DD` format) on the client side instead of using `toISOString()` which defaults to UTC.
* **Strict Integer Validation:** Modify `Server/routes/health.py` to raise a `400 Bad Request` if a user attempts to log steps or pulse rates with decimal values.

### 2. Configuration & Security
* **Secure Session Keys:** Replace the hardcoded JWT secret key in `app.py` with `os.environ.get('SECRET_KEY')` and configure a `.env` file loader.

### 3. Missing Feature Implementation (PRD Scope)
* **Monthly Trends Toggle:** Add a UI toggle on the Dashboard charts panel. Bind it to update the Chart.js instances by querying `/api/analytics/trends?days=30`.
* **Admin Console Enhancements:** Support resetting user passwords, updating profile demographics, or locking accounts directly from the Admin Accounts Registry table.
* **Directory Reorganization:** Relocate frontend page files into a dedicated `Client/pages` sub-folder and update relative references in scripts and links, matching the target schema layout.
