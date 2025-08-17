## Shuttrly Developer API and Components

This document provides a comprehensive reference for public HTTP endpoints, views, forms, models, template tags, middleware, authentication backend, and key utility functions in this project. It also includes usage examples and guidance for integration and development.

### Table of contents

- Endpoints and Views
  - Project-level routes
  - Users app
  - Admin Panel app
  - Logs app
- Models
- Forms
- Template tags and filters
- Middleware
- Authentication backend
- Utilities (helpers)

---

### Endpoints and Views

#### Project-level routes (`shuttrly/urls.py`)

- `GET /home/` → `shuttrly.views.home_view`
  - Renders `home.html`. If `Hx-Request` header present (htmx), renders `partials/home_partial.html`.
- `/<users app routes>` → included from `users.urls`
- `/admin-panel/<adminpanel routes>` → included from `adminpanel.urls` with namespace `adminpanel`
- `/logs/<logs routes>` → included from `logs.urls`
- `/admin/` → Django admin

#### Users app (`users/urls.py` → `users/views.py`)

- `GET|POST /register/` → `register_view`

  - 6-step registration flow, dispatching to step handlers based on `step` query or form field.
  - Steps: 1) Email, 2) Email code verification, 3) Personal info, 4) Username, 5) Password, 6) Summary & create.
  - Example:

    ```http
    # Step 1 (email + username)
    POST /register/
    Content-Type: application/x-www-form-urlencoded

    step=1&email=alice@example.com&username=alice
    ```

- `POST /check-username/` → `check_username_availability`

  - Returns JSON: `{ available: boolean, message: string }`.
  - Example:
    ```bash
    curl -X POST -d "username=alice" http://localhost:8000/check-username/
    ```

- `POST /resend-verification-code/` → `resend_verification_code_view`

  - Resends registration code (rate-limited/bounded by model logic). Returns HTTP redirect back to step 2.

- `GET|POST /login/` → `login_view`

  - 3-step login with 2FA:
    1. Credentials validation (`LoginForm`)
    2. 2FA method selection (`Choose2FAMethodForm`) if both enabled
    3. 2FA verification (`Email2FAForm` or `TOTP2FAForm`)
  - Example (credentials step):

    ```http
    POST /login/
    Content-Type: application/x-www-form-urlencoded

    step=login&email=alice@example.com&password=secret&remember_device=on
    ```

- `POST /resend-2fa-code/` → `resend_2fa_code_view`

  - AJAX endpoint to resend 2FA code for active login session. JSON responses and 4xx on errors/rate limit.
  - Example:
    ```bash
    curl -X POST http://localhost:8000/resend-2fa-code/
    ```

- `GET|POST /profile/` → `profile_view` (authenticated)

  - View and update profile data using `CustomUserUpdateForm`. Logs changes.

- `GET /logout/` → `logout_view`

  - Logs logout action and redirects to `login`.

- `GET|POST /account/delete/` → `delete_account_view` (authenticated)

  - Confirms then deletes the currently authenticated account on valid password.
  - Example:

    ```http
    POST /account/delete/
    Content-Type: application/x-www-form-urlencoded

    password=your-current-password
    ```

- `GET|POST /2fa/` → `twofa_settings_view` (authenticated)
  - Manage 2FA settings, trusted devices, and method enable/disable. Optional `?step=<name>` to navigate UI states.

Notes:

- Several views log user actions through `logs.utils.log_user_action_json` and re-use helpers from `users.utils`.

#### Admin Panel app (`adminpanel/urls.py` → `adminpanel/views.py`)

All routes are staff-only unless otherwise indicated.

- `GET /admin-panel/` → `admin_dashboard_view`

  - Lists users ordered by `date_joined`.

- `GET|POST /admin-panel/edit-user/<int:user_id>/` → `edit_user_view`

  - Edits a target user via `CustomUserAdminForm`; logs the changes diff (`get_changes_dict`).

- `POST /admin-panel/delete-user/<int:user_id>/` → `delete_user_view`

  - Deletes a non-superuser. Logs action.

- `GET /admin-panel/group/<int:group_id>/` → `group_dashboard_view`

  - Lists users in the Django `Group`.

- `GET /admin-panel/logs/` → `user_logs_view`

  - Renders logs from `logs/user_logs.json` sorted by timestamp.

- `POST /admin-panel/logs/restore/` → `restore_log_action_view`

  - Restores a previous change from the logs by `log_index`.
  - Example:

    ```http
    POST /admin-panel/logs/restore/
    Content-Type: application/x-www-form-urlencoded

    log_index=12
    ```

#### Logs app (`logs/urls.py` → `logs/views.py`)

- `GET /logs/logs/json/` → `logs_json_view` (staff-only)
  - Renders `json_logs.html` with `logs` and `logs_data_json` context from `logs/user_logs.json`.
  - Note: current implementation prints debug data to console; handle with care in production.

---

### Models (`users/models.py`)

Constants used across flows (`users/constants.py`)

- `EMAIL_CODE_RESEND_DELAY_SECONDS`, `EMAIL_CODE_EXPIRY_SECONDS`
- `TOTP_WINDOW_SIZE`, `TOTP_STEP_SECONDS`
- `SESSION_TIMEOUT_SECONDS`, `TRUSTED_DEVICE_EXPIRY_DAYS`
- `MAX_LOGIN_ATTEMPTS`, `MAX_2FA_ATTEMPTS`, `LOGIN_COOLDOWN_SECONDS`
- `EMAIL_VERIFICATION_EXPIRY_HOURS`

#### `CustomUser(AbstractBaseUser, PermissionsMixin)`

- Identity fields: `email` (unique, nullable), `username` (unique), `first_name`, `last_name`, `date_of_birth`
- Profile: `bio`, `is_private`, `profile_picture`
- IP tracking: `ip_address`, `last_login_ip`
- Status: `is_active`, `is_staff`, `date_joined`, `last_login_date`, `is_online`
- Email verification: `is_email_verified`, `email_verification_code`, `verification_code_sent_at`
- 2FA (email): `email_2fa_enabled`, `email_2fa_code`, `email_2fa_sent_at`
- 2FA (TOTP): `totp_enabled`, `twofa_totp_secret`
- GDPR: `is_anonymized`
- Manager: `CustomUserManager` with `create_user`/`create_superuser`
- Notable methods:
  - `save(...)` resizes images and schedules previous profile picture deletion
  - `delete()` removes image files on hard delete
  - `anonymize()` scrubs PII and deactivates account
  - Email verification helpers: `generate_verification_code()`, `can_send_verification_code()`, `is_verification_code_valid(code)`, `verify_email(code)`, `send_verification_email()`

#### `PendingFileDeletion(models.Model)`

- Fields: `file_path`, `trash_path`, `scheduled_deletion`, `created_at`, `reason`
- Methods: `move_to_trash()` moves file under `MEDIA_ROOT/trash/...`

#### `TrustedDevice(models.Model)`

- FK to `AUTH_USER_MODEL`, `device_token`, `user_agent`, `ip_address`, `location`, timestamps, expiry
- Derived metadata: `device_type`, `device_family`, `browser_family`, `browser_version`, `os_family`, `os_version`

---

### Forms (`users/forms.py`, `adminpanel/forms.py`)

#### Registration

- `RegisterStep1Form`: `email`, `username`
- `RegisterStep2Form`: `first_name`, `last_name`, `date_of_birth`
- `RegisterStep3Form`: `bio?`, `is_private?`, `profile_picture?`, `password1`, `password2`
- `RegisterStep4Form`: `username`
- `RegisterStep5Form`: `password1`, `password2` with match validation
- Additional variants for step 1–3 exist with localized labels/placeholders

#### Login & 2FA

- `LoginForm`: `email` (email or username), `password`, `remember_device?`
- `Choose2FAMethodForm`: `twofa_method` in `{email, totp}`
- `Email2FAForm`: `twofa_code` (6 digits)
- `TOTP2FAForm`: `twofa_code` (6 digits)

#### Profile

- `CustomUserUpdateForm(ModelForm)` for `CustomUser` covering primary identity/profile fields

#### Admin Panel

- `CustomUserAdminForm(ModelForm)` for `CustomUser` with `groups` as `ModelMultipleChoiceField`

---

### Template tags and filters

App: `users`

- `message_tags.display_messages_with_auto_clear`
  - Usage:
    ```django
    {% load message_tags %}
    {% display_messages_with_auto_clear %}
    ```
- `message_tags.clear_messages`
  - Usage:
    ```django
    {% load message_tags %}
    {% clear_messages %}
    ```
- `users_filters.format_location`
  - Input: dict-like `{"city": ..., "region": ..., "country": ...}` → string
  - Usage: `{{ user_location|format_location }}`
- `math_filters.mul`
  - Usage: `{{ price|mul:quantity }}`
- `datetime_tags.local_datetime(dt, css_class="user-datetime")`
  - Renders span with ISO datetime for client-side localization
  - Usage:
    ```django
    {% load datetime_tags %}
    {% local_datetime user.last_login_date "muted" %}
    ```

App: `adminpanel`

- `string_filters.is_image_url(value)` → bool
  - Usage: `{% if url|is_image_url %}...{% endif %}`
- `datetime_filters.format_iso_datetime(value)`
  - Parses ISO 8601 string and formats `dd/mm/YYYY HH:MM:SS`
  - Usage: `{{ iso_string|format_iso_datetime }}`

---

### Middleware

- `users.middleware.OnlineStatusMiddleware`
  - Sets `request.user.is_online = True` on authenticated requests.
  - Add to `MIDDLEWARE` after authentication middleware:
    ```python
    MIDDLEWARE = [
        # ...
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "users.middleware.OnlineStatusMiddleware",
        # ...
    ]
    ```

---

### Authentication backend

- `users.backend.SuperuserUsernameBackend`
  - Allows superusers to authenticate with their username; regular users login via email.
  - Configure in settings:
    ```python
    AUTHENTICATION_BACKENDS = [
        "users.backend.SuperuserUsernameBackend",
        "django.contrib.auth.backends.ModelBackend",
    ]
    ```

---

### Utilities (helpers) — `users/utils.py`

Key categories and selected functions. Functions prefixed with `_` are considered internal.

Complete utilities function index:

- `get_client_ip(request)`
- `schedule_profile_picture_deletion(file_path, seconds=None)`
- `is_file_still_in_use(file_path)`
- `get_changes_dict(old_obj, new_obj, changed_fields)`
- `get_user_agent(request)`
- `generate_email_code()`
- `send_2FA_email(user, code)`
- `is_email_code_valid(user, input_code)`
- `generate_totp_secret()`
- `get_totp_uri(user, secret)`
- `generate_qr_code_base64(uri)`
- `verify_totp(secret, code)`
- `hash_token(token)`
- `is_trusted_device(request, user)`
- `get_location_from_ip(ip_address)`
- `analyze_user_agent(ua_string)`
- `calculate_age(birth_date)`
- `can_resend_code(session_data)`
- `send_verification_email(email, code)`
- `get_device_name(request)`
- `is_safe_url(url, allowed_hosts, require_https=False)`
- `login_success(...)`
- `_get_device_info_from_user_agent(user_agent)`
- `get_user_from_session(request)`
- `initialize_2fa_session_data(request, user, code)`
- `initialize_login_session_data(request, user, code=None)`
- `handle_login_step_1_credentials(request)`
- `handle_login_step_2_2fa_choice(request)`
- `handle_login_step_3_2fa_verification_logic(request)`
- `_handle_email_2fa_verification(request, session_data, user)`
- `_handle_totp_2fa_verification(request, user)`
- `handle_login_resend_code(request, user)`
- `get_login_step_progress(step)`
- `cleanup_login_session(request)`
- `handle_resend_code_request(request, session_data, user, email_field="email")`
- `_calculate_time_until_resend(session_data)`
- `add_form_error_with_message(form, field, message)`
- `get_2fa_resend_status(user)`
- `get_current_device_token(request, user)`
- `enhance_trusted_device_info(device, current_device_token)`
- `handle_2fa_cancel_operation(user, step)`
- `handle_enable_email_2fa(user, password)`
- `handle_verify_email_2fa(user, code)`
- `handle_resend_email_2fa_code(user)`
- `handle_enable_totp_2fa(user, password)`
- `handle_verify_totp_2fa(user, code)`
- `handle_disable_2fa_method(user, password, method)`
- `handle_remove_trusted_device(user, device_id, current_device_token)`
- `get_2fa_settings_context(user, trusted_devices, step)`

- IP and request info

  - `get_client_ip(request)` → best-effort client IP
  - `get_user_agent(request)` → raw UA string
  - `get_device_name(request)` → human-friendly device label
  - `get_current_device_token(request, user)` → token used to identify current device

- Profile picture lifecycle

  - `schedule_profile_picture_deletion(file_path, seconds=None)` → queue deletion
  - `is_file_still_in_use(file_path)` → check if any user uses the file

- Change tracking

  - `get_changes_dict(old_obj, new_obj, changed_fields)` → dict of `[old, new]` per field; resolves file URLs

- Email-based 2FA

  - `generate_email_code()`
  - `send_2FA_email(user, code)`
  - `is_email_code_valid(user, input_code)`
  - `handle_resend_email_2fa_code(user)`

- TOTP-based 2FA

  - `generate_totp_secret()` → secret key
  - `get_totp_uri(user, secret)` → otpauth URI
  - `generate_qr_code_base64(uri)` → Base64 PNG for QR
  - `verify_totp(secret, code)`

- Trusted devices

  - `is_trusted_device(request, user)`
  - `enhance_trusted_device_info(device, current_device_token)`
  - `handle_remove_trusted_device(user, device_id, current_device_token)`

- Login flow helpers (used by views)

  - `initialize_login_session_data(request, user, code=None)`
  - `handle_login_step_1_credentials(request)`
  - `handle_login_step_2_2fa_choice(request)`
  - `handle_login_step_3_2fa_verification_logic(request)`
  - `get_login_step_progress(step)`, `cleanup_login_session(request)`
  - `handle_resend_code_request(request, session_data, user, email_field="email")`
  - `login_success(request, user, ip, user_agent, location, twofa_method, remember_device)`

- Misc
  - `get_location_from_ip(ip_address)` → dict with geo info (best-effort)
  - `analyze_user_agent(ua_string)` → parsed UA details
  - `calculate_age(birth_date)`
  - `can_resend_code(session_data)` → rate-limit helper
  - `is_safe_url(url, allowed_hosts, require_https=False)`
  - `add_form_error_with_message(form, field, message)`
  - `get_2fa_resend_status(user)`, `handle_2fa_cancel_operation(user, step)`
  - `handle_enable_email_2fa(user, password)`, `handle_verify_email_2fa(user, code)`
  - `handle_enable_totp_2fa(user, password)`, `handle_verify_totp_2fa(user, code)`
  - `handle_disable_2fa_method(user, password, method)`

Example: send a 2FA email code and verify it

```python
from users.utils import generate_email_code, send_2FA_email, is_email_code_valid

code = generate_email_code()
sent = send_2FA_email(request.user, code)
if sent and is_email_code_valid(request.user, code):
    # proceed
    pass
```

Example: generate TOTP secret and QR data URI

```python
from users.utils import generate_totp_secret, get_totp_uri, generate_qr_code_base64

secret = generate_totp_secret()
otpauth_uri = get_totp_uri(request.user, secret)
qr_png_b64 = generate_qr_code_base64(otpauth_uri)
```

---

### Logs utilities (`logs/utils.py`)

- `log_user_action_json(user, action, request=None, ip_address=None, user_agent=None, location=None, extra_info=None, restored=False)`

  - Appends a structured entry to `logs/user_logs.json`. Auto-fills IP, UA and location when `request` is provided.
  - Example:
    ```python
    from logs.utils import log_user_action_json
    log_user_action_json(
        user=request.user,
        action="update_profile",
        request=request,
        extra_info={"impacted_user_id": request.user.id, "changes": {"bio": ["old", "new"]}},
    )
    ```

- `get_location_from_ip(ip_address)`
  - Queries `ipinfo.io` with small timeout and returns `{city, region, country}` dict or `{}` on failure.

---

### Validators (`users/validators.py`)

- `CustomPasswordValidator`
  - Configurable rules for min length, uppercase/lowercase, digits, symbol.
  - Add to `AUTH_PASSWORD_VALIDATORS` in settings:
    ```python
    AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "users.validators.CustomPasswordValidator",
            "OPTIONS": {
                "min_length": 12,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_digits": True,
                "require_symbol": True,
            },
        },
    ]
    ```

---

### Signals (`users/signals.py`)

- `user_logged_in` receiver updates `last_login_ip` and marks user online.
  - Ensure the module is imported on app ready (e.g., from `apps.py` or project `ready()`), if not already.

---

### Development tips

- Many views require authentication or staff privileges. Use the Django admin to grant permissions and assign groups.
- File and image operations rely on `MEDIA_ROOT` and `default_storage`. Ensure these are configured for your environment.
- Logs are stored in `logs/user_logs.json`. Guard access to logs endpoints in production.
