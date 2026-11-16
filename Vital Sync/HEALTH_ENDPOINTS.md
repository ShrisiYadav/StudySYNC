# Health API Endpoints Specification

All endpoints in this section require authentication. You must provide a valid JWT token either through the `Authorization` header as a Bearer token or inside the cookie `token`.

---

## 1. Log Health Metric

Logs a new health metric for the authenticated user.
* **Steps logs** are incremental and upserted (accumulated daily).
* **Sleep logs** overwrite any existing entry for that date.
* **Water logs** are stored as individual incremental logs.
* **Heart Rate logs** are stored individually and will trigger warnings/notifications if the heart rate is high (>150 bpm) or low (<50 bpm).

### Endpoint Details
* **URL:** `/api/health/log`
* **Method:** `POST`
* **Authentication Requirement:** Required (JWT)
* **Request Body:**
  ```json
  {
    "metric_type": "steps",
    "value": 6000,
    "date": "2026-06-05"
  }
  ```
  * `metric_type` (String, Required): Must be one of `steps`, `water`, `sleep`, or `heart_rate`.
  * `value` (Number, Required): Must be non-negative. For `steps` and `heart_rate`, must be an integer. For `sleep`, must be <= 24.
  * `date` (String, Optional): Date in `YYYY-MM-DD` format (defaults to the current date if omitted).

### Example PowerShell Command
```powershell
$headers = @{
    Authorization = "Bearer <YOUR_JWT_TOKEN>"
}
$body = @{
    metric_type = "steps"
    value = 8500
    date = "2026-06-05"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/health/log" `
                              -Method Post `
                              -Headers $headers `
                              -ContentType "application/json" `
                              -Body $body
$response | ConvertTo-Json -Depth 4
```

---

## 2. Get Metric History

Retrieves historical logs of a specific metric type for the authenticated user, optionally filtered by a date range.

### Endpoint Details
* **URL:** `/api/health/history`
* **Method:** `GET`
* **Authentication Requirement:** Required (JWT)
* **Request Query Parameters:**
  * `metric_type` (String, Required): Must be one of `steps`, `water`, `sleep`, or `heart_rate`.
  * `start_date` (String, Optional): Filter records starting on or after this date (`YYYY-MM-DD`).
  * `end_date` (String, Optional): Filter records logged on or before this date (`YYYY-MM-DD`).

### Example PowerShell Command
```powershell
$headers = @{
    Authorization = "Bearer <YOUR_JWT_TOKEN>"
}

$response = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/health/history?metric_type=steps&start_date=2026-06-01" `
                              -Method Get `
                              -Headers $headers
$response.logs | Out-GridView  # Or just display: $response | ConvertTo-Json -Depth 4
```

---

## 3. Delete Metric Log

Removes a specific health metric log record owned by the authenticated user.

### Endpoint Details
* **URL:** `/api/health/log/<log_id>`
* **Method:** `DELETE`
* **Authentication Requirement:** Required (JWT)
* **Request Query Parameters:**
  * `metric_type` (String, Required): Must be one of `steps`, `water`, `sleep`, or `heart_rate`.

### Example PowerShell Command
```powershell
$headers = @{
    Authorization = "Bearer <YOUR_JWT_TOKEN>"
}

$logId = 12
$metricType = "steps"

$response = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/health/log/$logId?metric_type=$metricType" `
                              -Method Delete `
                              -Headers $headers
$response | ConvertTo-Json
```
