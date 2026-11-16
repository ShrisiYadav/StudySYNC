# VitalSync Reminder System

This document outlines the design and implementation details of the VitalSync Reminder and Inactivity Notification system, which dynamically alerts users of trailing habits and triggers warnings for inactive profiles.

---

## 1. Feature Specifications

The system tracks user log activity patterns and generates warnings for:

### A. Water Hydration Reminder
* **Trigger:** If the user has not logged water intake in the last 3 hours, or if they have not logged any water intake today.
* **Alert Message:** `"It has been over 3 hours since your last logged water intake. Don't forget to drink water and log it!"` (or `"You haven't logged any water intake today. Keep tracking to meet your hydration targets!"` if no today logs exist).
* **Type/Severity:** `info` (Water color indicator).

### B. Daily Activity Reminder (Step Goal)
* **Trigger:** Checks today's total steps compared to the user's active Steps Goal.
* **Alert Message:** If a steps target is configured, displays the current counts vs the goal target: `"You have logged {steps} steps out of your {target} steps target today. Keep moving!"`. If no steps target is set, displays: `"You have not configured a daily step goal yet. Configure a goal to track your target activity levels!"`.
* **Type/Severity:** `warning` (Yellow status indicator) if below target; `info` if no goal configured.

### C. Sleep Tracker Reminder
* **Trigger:** Checks if sleep duration has been recorded for the current day.
* **Alert Message:** If no logs exist, prompts the user: `"Don't forget to record your sleep hours for last night to track rest patterns on your graphs."`. If a sleep record exists but duration is under 7 hours: `"You logged {duration} hours of sleep today. Recommended guidelines suggest 7–9 hours for optimal recovery."`.
* **Type/Severity:** `warning` (for short sleep cycles) or `info` (for missing logs).

### D. Platform Inactivity Warning (For Inactive Users)
* **Trigger:** Checks the most recent logged activity date across all telemetry tables (`Steps`, `WaterIntake`, `SleepRecord`, `HeartRate`) for the user. If they have never logged telemetry, checks user registration creation time.
* **Action:** If the latest activity is **older than 24 hours**, the server automatically generates a database notification record:
  * **Title:** `"Platform Inactivity Alert"`
  * **Message:** `"Consistency is key to wellness! We noticed you haven't logged any health metrics in the last 24 hours. Let's record some stats!"`
  * **Type:** `warning`
* **Status:** Persists in the user's unread notifications drawer.

---

## 2. Technical Implementation Details

### A. Backend API Additions
* **File:** [notifications.py](file:///c:/Users/SHRISTI%20YADAV/OneDrive/Desktop/Vital%20Sync/Server/routes/notifications.py)
* **New Route:** `GET /api/notifications/reminders` (Requires JWT Authentication)
  * Runs the **Inactivity Check** helper: `check_inactive_user(current_user)`.
  * Queries database records for today's logs and goals.
  * Compiles active reminder objects with types (`water`, `activity`, `sleep`), titles, messages, and severities.
  * Returns:
    ```json
    {
      "reminders": [
        {
          "type": "water",
          "title": "Stay Hydrated",
          "message": "It has been over 3 hours since your last logged water intake...",
          "severity": "info"
        }
      ]
    }
    ```
* **Inactivity Check Hook:** `check_inactive_user(current_user)` evaluates timestamps and appends warnings directly to the `notifications` table dynamically when fetching notifications or reminders.

### B. Frontend Layout & CSS
* **File:** [dashboard.html](file:///c:/Users/SHRISTI%20YADAV/OneDrive/Desktop/Vital%20Sync/Client/dashboard.html)
  * Inserted `#reminders-panel` container div between the welcome header and the overview cards grid.
* **File:** [dashboard.css](file:///c:/Users/SHRISTI%20YADAV/OneDrive/Desktop/Vital%20Sync/Client/css/dashboard.css)
  * Added styling for `.reminders-container`, `.reminder-card`, and severity variations using our premium HSL color variables and glassmorphism.
  * Added slide-down entry animations (`reminderFadeIn`) and smooth opacity transitions.
* **File:** [dashboard.js](file:///c:/Users/SHRISTI%20YADAV/OneDrive/Desktop/Vital%20Sync/Client/js/dashboard.js)
  * Integrated `fetchReminders()` inside the standard dashboard data refresh pipeline (`refreshDashboardData()`).
  * Created `dismissReminder(button)` helper to animate card exits (translates up and fades out) and automatically collapse the reminder header panel when the card stack is empty.
