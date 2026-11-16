# Vital Sync API Routes

All endpoints (except `/api/ping`, `/api/auth/register`, and `/api/auth/login`) require authentication via a JSON Web Token (JWT). You can authenticate by either:
1. Setting an `Authorization: Bearer <token>` header.
2. Setting a `token` cookie.

---

## General Endpoints

### Ping API
* **Endpoint:** `/api/ping`
* **HTTP Method:** `GET`
* **Request Body:** None
* **Response:**
  * **200 OK:**
    ```json
    {
      "message": "VitalSync API Server is Active"
    }
    ```
* **Example Usage:**
  ```bash
  curl http://127.0.0.1:5000/api/ping
  ```

---

## Authentication Endpoints (`/api/auth`)

### User Registration
* **Endpoint:** `/api/auth/register`
* **HTTP Method:** `POST`
* **Request Body:**
  ```json
  {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "password": "Password123",
    "age": 28,
    "gender": "female",
    "role": "user"
  }
  ```
  *Note: `gender` must be 'male', 'female', or 'other'. `role` defaults to 'user' if not specified or invalid.*
* **Response:**
  * **201 Created:**
    ```json
    {
      "message": "Registration successful",
      "user_id": 2
    }
    ```
  * **400 Bad Request (Missing fields):**
    ```json
    {
      "message": "All registration fields are required"
    }
    ```
  * **400 Bad Request (Invalid Age):**
    ```json
    {
      "message": "Age must be a valid positive integer"
    }
    ```
  * **400 Bad Request (Invalid Gender):**
    ```json
    {
      "message": "Gender must be male, female, or other"
    }
    ```
  * **409 Conflict (Email exists):**
    ```json
    {
      "message": "Email address is already registered"
    }
    ```
* **Example Usage:**
  ```bash
  curl -X POST -H "Content-Type: application/json" \
    -d '{"name": "Jane Doe", "email": "jane@example.com", "password": "Password123", "age": 28, "gender": "female"}' \
    http://127.0.0.1:5000/api/auth/register
  ```

### User Login
* **Endpoint:** `/api/auth/login`
* **HTTP Method:** `POST`
* **Request Body:**
  ```json
  {
    "email": "jane@example.com",
    "password": "Password123"
  }
  ```
* **Response:**
  * **200 OK:** Sets an `HttpOnly` cookie named `token` and returns:
    ```json
    {
      "message": "Login successful",
      "token": "JWT_TOKEN_STRING",
      "user": {
        "id": 2,
        "name": "Jane Doe",
        "email": "jane@example.com",
        "role": "user"
      }
    }
    ```
  * **400 Bad Request:**
    ```json
    {
      "message": "Email and password are required"
    }
    ```
  * **401 Unauthorized:**
    ```json
    {
      "message": "Invalid email credentials or password"
    }
    ```
* **Example Usage:**
  ```bash
  curl -X POST -H "Content-Type: application/json" \
    -d '{"email": "jane@example.com", "password": "Password123"}' \
    http://127.0.0.1:5000/api/auth/login
  ```

### User Logout
* **Endpoint:** `/api/auth/logout`
* **HTTP Method:** `POST`
* **Request Body:** None
* **Response:**
  * **200 OK:** Deletes the `token` cookie.
    ```json
    {
      "message": "Logged out successfully"
    }
    ```
* **Example Usage:**
  ```bash
  curl -X POST http://127.0.0.1:5000/api/auth/logout
  ```

### Get Profile Information
* **Endpoint:** `/api/auth/me`
* **HTTP Method:** `GET`
* **Request Body:** None
* **Response:**
  * **200 OK:**
    ```json
    {
      "id": 2,
      "name": "Jane Doe",
      "email": "jane@example.com",
      "age": 28,
      "gender": "female",
      "role": "user",
      "created_at": "2026-06-04 23:42:00"
    }
    ```
  * **401 Unauthorized:**
    ```json
    {
      "message": "Authentication token is missing"
    }
    ```
* **Example Usage:**
  ```bash
  curl -H "Authorization: Bearer <token>" http://127.0.0.1:5000/api/auth/me
  ```

---

## Health Log Endpoints (`/api/health`)

### Log Health Metric
* **Endpoint:** `/api/health/log`
* **HTTP Method:** `POST`
* **Request Body:**
  ```json
  {
    "metric_type": "steps",
    "value": 5000,
    "date": "2026-06-04"
  }
  ```
  *Note: `metric_type` must be one of 'steps', 'water', 'sleep', or 'heart_rate'. `date` is optional (defaults to today's date in YYYY-MM-DD format).*
* **Response:**
  * **200 OK (Steps - Incremental UPSERT):**
    ```json
    {
      "message": "Steps logged successfully",
      "log": {
        "id": 1,
        "user_id": 2,
        "count": 5000,
        "log_date": "2026-06-04",
        "logged_at": "2026-06-04 23:43:00"
      }
    }
    ```
  * **200 OK (Water - Incremental Insert):**
    ```json
    {
      "message": "Water intake logged successfully",
      "log": {
        "id": 1,
        "user_id": 2,
        "amount_ml": 250.0,
        "log_date": "2026-06-04",
        "logged_at": "2026-06-04 23:43:00"
      }
    }
    ```
  * **200 OK (Sleep - Overwrites Daily Record):**
    ```json
    {
      "message": "Sleep record logged successfully",
      "log": {
        "id": 1,
        "user_id": 2,
        "duration_hours": 7.5,
        "log_date": "2026-06-04",
        "logged_at": "2026-06-04 23:43:00"
      }
    }
    ```
  * **200 OK (Heart Rate - New Log, potentially triggers warning alerts if >150 bpm or <50 bpm):**
    ```json
    {
      "message": "Heart rate logged successfully",
      "log": {
        "id": 1,
        "user_id": 2,
        "bpm": 72,
        "log_date": "2026-06-04",
        "logged_at": "2026-06-04 23:43:00"
      }
    }
    ```
  * **400 Bad Request:** For missing fields, negative values, invalid date format, or invalid numbers.
* **Example Usage:**
  ```bash
  curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
    -d '{"metric_type": "steps", "value": 5000, "date": "2026-06-04"}' \
    http://127.0.0.1:5000/api/health/log
  ```

### Get Metric History
* **Endpoint:** `/api/health/history`
* **HTTP Method:** `GET`
* **Query Parameters:**
  * `metric_type` (Required): 'steps', 'water', 'sleep', or 'heart_rate'
  * `start_date` (Optional): YYYY-MM-DD
  * `end_date` (Optional): YYYY-MM-DD
* **Response:**
  * **200 OK:**
    ```json
    {
      "logs": [
        {
          "id": 1,
          "user_id": 2,
          "count": 5000,
          "log_date": "2026-06-04",
          "logged_at": "2026-06-04 23:43:00"
        }
      ]
    }
    ```
  * **400 Bad Request:** If `metric_type` is missing or invalid.
* **Example Usage:**
  ```bash
  curl -H "Authorization: Bearer <token>" \
    "http://127.0.0.1:5000/api/health/history?metric_type=steps&start_date=2026-06-01&end_date=2026-06-05"
  ```

### Delete Metric Log
* **Endpoint:** `/api/health/log/<int:log_id>`
* **HTTP Method:** `DELETE`
* **Query Parameters:**
  * `metric_type` (Required): 'steps', 'water', 'sleep', or 'heart_rate'
* **Response:**
  * **200 OK:**
    ```json
    {
      "message": "Health record deleted successfully"
    }
    ```
  * **400 Bad Request:** If `metric_type` is missing or invalid.
  * **404 Not Found:** If the record does not exist or does not belong to the user.
* **Example Usage:**
  ```bash
  curl -X DELETE -H "Authorization: Bearer <token>" \
    "http://127.0.0.1:5000/api/health/log/1?metric_type=steps"
  ```

---

## Goal Endpoints (`/api/goals`)

### Configure Goal
* **Endpoint:** `/api/goals`
* **HTTP Method:** `POST`
* **Request Body:**
  ```json
  {
    "metric_type": "steps",
    "target_value": 8000
  }
  ```
  *Note: `metric_type` must be one of 'steps', 'water', or 'sleep'. `target_value` must be a positive number.*
* **Response:**
  * **200 OK:**
    ```json
    {
      "message": "Goal configured successfully",
      "goal": {
        "id": 1,
        "user_id": 2,
        "metric_type": "steps",
        "target_value": 8000.0,
        "created_at": "2026-06-04 23:44:00",
        "updated_at": "2026-06-04 23:44:00"
      }
    }
    ```
  * **400 Bad Request:** For missing fields, invalid target values, or unsupported metric types.
* **Example Usage:**
  ```bash
  curl -X POST -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
    -d '{"metric_type": "steps", "target_value": 8000}' \
    http://127.0.0.1:5000/api/goals
  ```

### Get Goals and Progress
* **Endpoint:** `/api/goals`
* **HTTP Method:** `GET`
* **Request Body:** None
* **Response:**
  * **200 OK:** Returns active goals and current day progress metrics.
    ```json
    {
      "goals": {
        "steps": 8000.0,
        "water": 0,
        "sleep": 0
      },
      "progress": {
        "steps": {
          "logged": 5000,
          "percentage": 62.5
        },
        "water": {
          "logged": 0,
          "percentage": 0.0
        },
        "sleep": {
          "logged": 0,
          "percentage": 0.0
        }
      }
    }
    ```
* **Example Usage:**
  ```bash
  curl -H "Authorization: Bearer <token>" http://127.0.0.1:5000/api/goals
  ```

---

## Analytics Endpoints (`/api/analytics`)

### Get Metric Trends
* **Endpoint:** `/api/analytics/trends`
* **HTTP Method:** `GET`
* **Query Parameters:**
  * `days` (Optional): Number of days to include (1 to 30, defaults to 7).
* **Response:**
  * **200 OK:**
    ```json
    {
      "dates": ["2026-05-29", "2026-05-30", "2026-05-31", "2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04"],
      "steps": [0, 0, 0, 0, 0, 0, 5000],
      "water": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 250.0],
      "sleep": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 7.5],
      "heart_rate": [0, 0, 0, 0, 0, 0, 72.0]
    }
    ```
* **Example Usage:**
  ```bash
  curl -H "Authorization: Bearer <token>" "http://127.0.0.1:5000/api/analytics/trends?days=7"
  ```

---

## Notification Endpoints (`/api/notifications`)

### Get Notifications
* **Endpoint:** `/api/notifications`
* **HTTP Method:** `GET`
* **Request Body:** None
* **Response:**
  * **200 OK:** Returns a list of notifications for the user, ordered by creation time descending.
    ```json
    {
      "notifications": [
        {
          "id": 1,
          "user_id": 2,
          "title": "High Heart Rate Alert",
          "message": "Your heart rate measurement of 160 bpm is elevated. Take a rest.",
          "type": "warning",
          "is_read": false,
          "created_at": "2026-06-04 23:43:00"
        }
      ]
    }
    ```
* **Example Usage:**
  ```bash
  curl -H "Authorization: Bearer <token>" http://127.0.0.1:5000/api/notifications
  ```

### Mark All Notifications as Read
* **Endpoint:** `/api/notifications/read`
* **HTTP Method:** `POST`
* **Request Body:** None
* **Response:**
  * **200 OK:**
    ```json
    {
      "message": "All notifications marked as read"
    }
    ```
* **Example Usage:**
  ```bash
  curl -X POST -H "Authorization: Bearer <token>" http://127.0.0.1:5000/api/notifications/read
  ```

### Mark Specific Notification as Read
* **Endpoint:** `/api/notifications/read/<int:notif_id>`
* **HTTP Method:** `POST`
* **Request Body:** None
* **Response:**
  * **200 OK:**
    ```json
    {
      "message": "Notification marked as read"
    }
    ```
  * **404 Not Found:** If the notification does not exist or does not belong to the user.
* **Example Usage:**
  ```bash
  curl -X POST -H "Authorization: Bearer <token>" http://127.0.0.1:5000/api/notifications/read/1
  ```

### Delete Notification
* **Endpoint:** `/api/notifications/<int:notif_id>`
* **HTTP Method:** `DELETE`
* **Request Body:** None
* **Response:**
  * **200 OK:**
    ```json
    {
      "message": "Notification deleted successfully"
    }
    ```
  * **404 Not Found:** If the notification does not exist or does not belong to the user.
* **Example Usage:**
  ```bash
  curl -X DELETE -H "Authorization: Bearer <token>" http://127.0.0.1:5000/api/notifications/1
  ```

---

## Administration Endpoints (`/api/admin`)
*All administration endpoints require the user to have the administrative role (`role='admin'`).*

### Search Users
* **Endpoint:** `/api/admin/users`
* **HTTP Method:** `GET`
* **Query Parameters:**
  * `search` (Optional): Query string to search users by name or email.
* **Response:**
  * **200 OK:**
    ```json
    {
      "users": [
        {
          "id": 2,
          "name": "Jane Doe",
          "email": "jane@example.com",
          "age": 28,
          "gender": "female",
          "role": "user",
          "created_at": "2026-06-04 23:42:00"
        }
      ]
    }
    ```
  * **403 Forbidden:** If the current user is not an administrator.
* **Example Usage:**
  ```bash
  curl -H "Authorization: Bearer <admin_token>" "http://127.0.0.1:5000/api/admin/users?search=Jane"
  ```

### Delete User Account
* **Endpoint:** `/api/admin/users/<int:user_id>`
* **HTTP Method:** `DELETE`
* **Request Body:** None
* **Response:**
  * **200 OK:**
    ```json
    {
      "message": "User and all associated data deleted successfully"
    }
    ```
  * **400 Bad Request:** If the administrator attempts to delete their own account.
  * **404 Not Found:** If the user is not found.
* **Example Usage:**
  ```bash
  curl -X DELETE -H "Authorization: Bearer <admin_token>" http://127.0.0.1:5000/api/admin/users/2
  ```

### Get Recent Activity Records
* **Endpoint:** `/api/admin/records`
* **HTTP Method:** `GET`
* **Request Body:** None
* **Response:**
  * **200 OK:** Returns up to 100 recent health logs across all users, sorted by log date descending.
    ```json
    {
      "records": [
        {
          "id": 1,
          "user_name": "Jane Doe",
          "user_email": "jane@example.com",
          "metric_type": "steps",
          "value": 5000,
          "log_date": "2026-06-04",
          "logged_at": "2026-06-04 23:43:00"
        }
      ]
    }
    ```
* **Example Usage:**
  ```bash
  curl -H "Authorization: Bearer <admin_token>" http://127.0.0.1:5000/api/admin/records
  ```

### Delete Specific User Record
* **Endpoint:** `/api/admin/records/<int:log_id>`
* **HTTP Method:** `DELETE`
* **Query Parameters:**
  * `metric_type` (Required): 'steps', 'water', 'sleep', or 'heart_rate'
* **Response:**
  * **200 OK:**
    ```json
    {
      "message": "Record successfully deleted by administrator"
    }
    ```
  * **400 Bad Request:** If `metric_type` is missing or invalid.
  * **404 Not Found:** If the record is not found.
* **Example Usage:**
  ```bash
  curl -X DELETE -H "Authorization: Bearer <admin_token>" \
    "http://127.0.0.1:5000/api/admin/records/1?metric_type=steps"
  ```

### Get Platform Metrics
* **Endpoint:** `/api/admin/metrics`
* **HTTP Method:** `GET`
* **Request Body:** None
* **Response:**
  * **200 OK:**
    ```json
    {
      "total_users": 2,
      "total_logs": 4,
      "activity": {
        "steps": 1,
        "water": 1,
        "sleep": 1,
        "heart_rate": 1
      },
      "growth": {
        "months": ["2026-06"],
        "counts": [2]
      }
    }
    ```
* **Example Usage:**
  ```bash
  curl -H "Authorization: Bearer <admin_token>" http://127.0.0.1:5000/api/admin/metrics
  ```
