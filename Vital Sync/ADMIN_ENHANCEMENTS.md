# VitalSync Admin Dashboard Enhancements

This document describes the enhancements implemented in the VitalSync Admin Dashboard, detailing both backend API route configurations and frontend UI enhancements.

---

## 1. Backend API Routes Implemented

Three new administrative endpoints were created in the backend [admin.py](file:///c:/Users/SHRISTI%20YADAV/OneDrive/Desktop/Vital%20Sync/Server/routes/admin.py) route controller. All endpoints verify that the requesting user's role is `'admin'`.

### A. Reset User Password
* **Endpoint:** `POST /api/admin/users/<int:user_id>/reset-password`
* **Request Body:**
  ```json
  {
    "password": "NewSecurePassword123"
  }
  ```
* **Validation:** Enforces that the password must be at least 8 characters. Hashes using standard PBKDF2 cryptography functions before committing.

### B. Disable / Enable User Account
* **Endpoint:** `POST /api/admin/users/<int:user_id>/toggle-status`
* **Logic:**
  * Checks if the admin attempts to toggle their own account status (returns `400 Bad Request` to prevent locking oneself out).
  * Flips the `is_active` parameter between `0` (disabled) and `1` (active).
  * Enforced in `auth.py` (blocks login checks for disabled accounts, returning `403 Forbidden`).
  * Enforced in `middleware.py` (invalidates session requests on standard user endpoints immediately if their account is disabled).

### C. Edit User Profile
* **Endpoint:** `PUT /api/admin/users/<int:user_id>`
* **Request Body:**
  ```json
  {
    "name": "Rahul Sharma",
    "email": "rahul@example.com",
    "age": 21,
    "gender": "male",
    "role": "user"
  }
  ```
* **Validation:** Performs standard registration-level inputs checks (positive age integer, valid gender category, role validation, and checks email uniqueness conflicts against other registered accounts). Prevents the admin from demoting their own role.

---

## 2. Frontend UI Enhancements

The administrative interface inside [admin.html](file:///c:/Users/SHRISTI%20YADAV/OneDrive/Desktop/Vital%20Sync/Client/admin.html) and [admin.js](file:///c:/Users/SHRISTI%20YADAV/OneDrive/Desktop/Vital%20Sync/Client/js/admin.js) was upgraded to support interactive user actions:

### A. Better User Management UI Table
* Upgraded the accounts registry table to contain two additional columns: **Status** and **Actions**.
* Renders active status badges:
  * `<span class="status-badge active">Active</span>`
  * `<span class="status-badge disabled">Disabled</span>`
* Houses a clean horizontal button group inside the Actions column:
  * **✏️ Edit Profile Button:** Opens the custom profile edit modal.
  * **🔑 Reset Password Button:** Opens the password reset modal.
  * **🚫 / ✅ Toggle Status Button:** Renders a block icon if the account is active, or a checkmark if disabled, triggering confirmation popups on click.
  * **🗑️ Delete Account Button:** Confirms and deletes user accounts.

### B. Interactive Popups & Modal Modifiers
* **Overlay Modals:** Developed two premium-styled overlay modals at the bottom of the body:
  * `#edit-user-modal`: Contains form fields for Name, Email, Age, Gender selection dropdown, and Role.
  * `#reset-password-modal`: Displays the target user's name and collects a new secure password.
* **Transitions:** Modals utilize backdrop-blur filters (`backdrop-filter: blur(8px)`) and scaling transformations (`transform: scale(0.9) -> scale(1)`) to animate entry smoothly.
* **Auto-Session Synchronization:** If the active admin updates their own profile details, changes are synced directly into `localStorage` dynamically, updating headers instantly without manual page refreshes.

---

## 3. Database Schema Migration

To support active state indicators, a database schema migration step was added to Flask's initialization inside [app.py](file:///c:/Users/SHRISTI%20YADAV/OneDrive/Desktop/Vital%20Sync/Server/app.py):

* Appended the column `is_active` to the `User` model (`Integer`, `default=1`).
* Inside `app.app_context()`, a test query runs on startup. If the column `is_active` is missing from the existing SQLite database table, it executes:
  ```sql
  ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1
  ```
  This ensures compatibility with pre-existing sqlite files in deployment.

---

## 4. Test Suite Enhancements

Added complete unit test coverage inside [test_endpoints.py](file:///c:/Users/SHRISTI%20YADAV/OneDrive/Desktop/Vital%20Sync/Server/tests/test_endpoints.py#L141-L229):

* **Profile Update Assertion:** Confirms database changes persist after editing.
* **Toggle Status & Login Invalidation Assertion:**
  * Disables a user profile.
  * Asserts login requests return `403 Forbidden` with the warning: `"This account has been disabled"`.
  * Enables the user again, asserting that login succeeds.
* **Password Reset Assertion:**
  * Triggers reset password.
  * Verifies old credentials fail (`401`) while new credentials pass.
* All test scenarios pass successfully.
