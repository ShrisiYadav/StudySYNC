# Goals API Endpoints Specification

All endpoints in this section require authentication. You must provide a valid JWT token either through the `Authorization` header as a Bearer token or inside the cookie `token`.

---

## 1. Configure Goal

Creates or updates a target goal for the authenticated user for a specific metric type (`steps`, `water`, or `sleep`).

### Endpoint Details
* **Endpoint URL:** `/api/goals`
* **Method:** `POST`
* **Authentication Requirement:** Required (JWT)
* **Request Body:**
  ```json
  {
    "metric_type": "steps",
    "target_value": 8000
  }
  ```
  * `metric_type` (String, Required): Must be one of `steps`, `water`, or `sleep`.
  * `target_value` (Number, Required): Must be a positive number.

### Example PowerShell Command
```powershell
$headers = @{
    Authorization = "Bearer <YOUR_JWT_TOKEN>"
}
$body = @{
    metric_type = "steps"
    target_value = 10000
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/goals" `
                              -Method Post `
                              -Headers $headers `
                              -ContentType "application/json" `
                              -Body $body
$response | ConvertTo-Json -Depth 4
```

### Expected Response

#### 200 OK (Success)
```json
{
  "message": "Goal configured successfully",
  "goal": {
    "id": 1,
    "user_id": 3,
    "metric_type": "steps",
    "target_value": 10000.0,
    "created_at": "2026-06-05 00:36:00",
    "updated_at": "2026-06-05 00:36:00"
  }
}
```

#### 400 Bad Request (Missing parameters)
```json
{
  "message": "metric_type and target_value are required"
}
```

#### 400 Bad Request (Unsupported metric type)
```json
{
  "message": "Goal tracking not supported for: heart_rate"
}
```

#### 400 Bad Request (Non-positive target value)
```json
{
  "message": "Goal target value must be positive"
}
```

---

## 2. Get Goals and Progress

Retrieves the user's active goals along with today's logged progress percentage (capped at `100.0`).

### Endpoint Details
* **Endpoint URL:** `/api/goals`
* **Method:** `GET`
* **Authentication Requirement:** Required (JWT)
* **Request Body:** None

### Example PowerShell Command
```powershell
$headers = @{
    Authorization = "Bearer <YOUR_JWT_TOKEN>"
}

$response = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/goals" `
                              -Method Get `
                              -Headers $headers
$response | ConvertTo-Json -Depth 4
```

### Expected Response

#### 200 OK (Success)
```json
{
  "goals": {
    "steps": 10000.0,
    "water": 2000.0,
    "sleep": 8.0
  },
  "progress": {
    "steps": {
      "logged": 8500,
      "percentage": 85.0
    },
    "water": {
      "logged": 2.5,
      "percentage": 0.13
    },
    "sleep": {
      "logged": 7.5,
      "percentage": 93.75
    }
  }
}
```
*Note: If no goal targets are configured for a metric, the default target will show as `0` and progress percentage will be `0.0`.*
