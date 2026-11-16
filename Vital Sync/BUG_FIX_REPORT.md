# VitalSync Bug Fix Report

This document outlines the bugs resolved in the VitalSync platform codebase, detailing the problem descriptions, the corresponding code fixes, and the verification methods.

---

## 1. Resolved Bugs

### Bug 1: Deprecated Global `event` References
* **Affected Files:**
  * [dashboard.html](file:///c:/Users/SHRISTI%20YADAV/OneDrive/Desktop/Vital%20Sync/Client/dashboard.html) (Lines 45, 142–145)
  * [dashboard.js](file:///c:/Users/SHRISTI%20YADAV/OneDrive/Desktop/Vital%20Sync/Client/js/dashboard.js) (Lines 47, 61)
* **Problem Description:** The frontend code relied on `window.event` globally in `switchLogTab` and `toggleNotifications` (calling `event.currentTarget` and `event.stopPropagation()`). Global `event` is deprecated and causes `ReferenceError: event is not defined` in modular/strict environments, or under standard configurations in modern browsers like Firefox.
* **Code Fix:**
  * Modified HTML button templates to pass `event` explicitly into handlers:
    * `onclick="toggleNotifications(event)"`
    * `onclick="switchLogTab(event, 'steps')"`
  * Updated JavaScript methods in `dashboard.js` to capture the parameter as a local variable `e` and replaced `event` calls with `e`.
* **Verification:** Verified by checking frontend behavior when logging metrics and toggling drawers.

---

### Bug 2: Event Listener Leak in Notifications Drawer
* **Affected Files:**
  * [dashboard.js](file:///c:/Users/SHRISTI%20YADAV/OneDrive/Desktop/Vital%20Sync/Client/js/dashboard.js) (Lines 4, 61–85)
* **Problem Description:** Every time `toggleNotifications()` was executed, a new click event handler (`closePanel`) was appended to the global `document` to auto-close the drawer when clicking outside. Because `removeEventListener` was only called if clicking *outside*, repeatedly clicking the bell button to open/close the drawer leaked anonymous event listeners onto the `document` context.
* **Code Fix:**
  * Created a persistent global handle `closePanelListener` inside `dashboard.js`.
  * Rewrote `toggleNotifications(e)` to clean up any active click listener when closing the dropdown, or prior to attaching a new one when opening.
* **Verification:** Verified listener disposal locally to confirm memory leaks are avoided during repeated Bell icon clicks.

---

### Bug 3: UTC Date Timezone Offset Discrepancies
* **Affected Files:**
  * [dashboard.js](file:///c:/Users/SHRISTI%20YADAV/OneDrive/Desktop/Vital%20Sync/Client/js/dashboard.js) (Lines 6–12, 42, 156)
* **Problem Description:** Default input dates and Quick Water logging stamps used `new Date().toISOString().split('T')[0]`. Since `.toISOString()` translates date-times directly into UTC, international users logging telemetry after midnight UTC (late night in local timezones) had entries recorded under the wrong local calendar date, causing dashboard progress calculation mismatches.
* **Code Fix:**
  * Developed a `getLocalDateString()` JavaScript helper that builds `YYYY-MM-DD` strings locally via client-side calendar methods (`getFullYear()`, `getMonth() + 1`, and `getDate()`).
  * Updated both the form date initializers and the quick hydration logs to fetch from `getLocalDateString()`.
* **Verification:** Dates default to local timezones rather than UTC.

---

### Bug 4: Silent Truncation of Float Values (Steps & BPM)
* **Affected Files:**
  * [health.py](file:///c:/Users/SHRISTI%20YADAV/OneDrive/Desktop/Vital%20Sync/Server/routes/health.py) (Lines 39, 82)
  * [test_endpoints.py](file:///c:/Users/SHRISTI%20YADAV/OneDrive/Desktop/Vital%20Sync/Server/tests/test_endpoints.py) (Lines 87–109)
* **Problem Description:** Python's integer casting `int(float)` silently truncates decimal parts rather than raising exceptions (e.g. `int(5.9)` registers as `5` steps). Consequently, users submitting float inputs for Steps or Heart Rate (BPM) were logged incorrectly without validation failures.
* **Code Fix:**
  * Added type validation checks `if not value.is_integer():` to return a `400 Bad Request` if fractional values are passed for Steps or Heart Rate BPM.
  * Added unit test assertions inside `test_endpoints.py` to verify that decimal step entries (e.g. `5000.5`) and decimal BPM entries (e.g. `72.8`) are rejected with a `400` status.
* **Verification:** Ran pytest/unittest discover suites to verify assertions passed successfully.

---

### Bug 5: Exposed JWT Secret Key
* **Affected Files:**
  * [app.py](file:///c:/Users/SHRISTI%20YADAV/OneDrive/Desktop/Vital%20Sync/Server/app.py) (Lines 14–44)
  * [.env](file:///c:/Users/SHRISTI%20YADAV/OneDrive/Desktop/Vital%20Sync/.env)
* **Problem Description:** The Flask server initialized the Flask application context using a hardcoded `SECRET_KEY` string literal inside the codebase, posing a severe security risk.
* **Code Fix:**
  * Created a custom `.env` loader utility (`load_env()`) in `app.py` to search for environment parameters at the project workspace root and load them into memory.
  * Created a secure [.env](file:///c:/Users/SHRISTI%20YADAV/OneDrive/Desktop/Vital%20Sync/.env) configuration template.
  * Refactored `app.config['SECRET_KEY']` to retrieve the key dynamically via `os.environ.get('SECRET_KEY')` with a default safe fallback.
* **Verification:** Confirmed that the application starts up, imports the key, and successfully logs in test profiles.

---

## 2. Testing & Verification Summary

All endpoint behaviors were validated in isolation and integration, and the Python test suite was run locally:

```powershell
python -m unittest discover -s Server/tests
```

**Results:**
* **Total Tests Run:** 4
* **Errors/Failures:** 0
* **Status:** **OK (Passed)**
