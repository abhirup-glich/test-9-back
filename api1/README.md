# Auth Service

This microservice handles user authentication, registration, and session management.

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables in `.env` (copy from root .env but only keep what's needed).
3. Run: `python run.py`

## API

- `POST /auth/register`: Register new user
- `POST /auth/login`: Login user
- `POST /auth/admin-login-init`: Send OTP for admin
- `POST /auth/admin-login-verify`: Verify OTP and login admin
- `POST /auth/change-password`: Change password

## Docker

Build: `docker build -t auth-service .`
Run: `docker run -p 5001:5001 --env-file .env auth-service`

## Troubleshooting & Fixes (2026-01-11)

### ImportError Resolution
An `ImportError: attempted relative import with no known parent package` was occurring when running with Gunicorn or direct script execution. This was resolved by implementing a hybrid import strategy in `routes.py`:
```python
try:
    from .schemas import ...
except ImportError:
    from schemas import ...
```
This supports both package-mode and script-mode execution.

### Security Updates
- **Password Hashing**: Fixed `register_student` to hash passwords using `werkzeug.security.generate_password_hash` before storing in Supabase, matching the behavior of `update_student`.

### Testing
Unit tests have been added in `test_routes.py` covering:
- Successful student retrieval.
- Unauthorized access attempts.
- Student registration (success).
- Validation errors (missing fields).

Run tests with:
```bash
python test_routes.py
```

### Logging
Detailed logging is enabled via `setup_logging` in `main.py` and used throughout `services.py` and `routes.py`. Logs include timestamp, log level, module, and message.
