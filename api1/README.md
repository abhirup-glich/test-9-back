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

## Error System (2026-01-11)

A robust error logging and tracking system has been implemented to assign unique error codes to every error occurrence.

### Features
- **Unique Error Codes**: Every error gets a unique, incrementing code based on its type.
  - Example: A 500 error might generate code `500`, the next one `501`, then `502`.
  - Example: A 404 error might generate code `404`, then `405`.
- **Persistence**: Error counters are saved to `error_counters.json` to ensure code continuity across server restarts.
- **Detailed Logging**: Logs include the unique code, timestamp, message, stack trace, and request context.

### Console Output Format
```
[ERROR LOG START]
Code: 501
Time: 2026-01-11T01:00:00.123456Z
Message: Internal Server Error
Context: {'url': 'http://localhost/api/students', 'method': 'GET', 'remote_addr': '127.0.0.1'}
Stack Trace:
Traceback (most recent call last):
  ...
[ERROR LOG END]
```

### Troubleshooting
- **Resetting Counters**: To reset the error codes, delete the `error_counters.json` file.
- **Concurrency**: The system is thread-safe and handles concurrent error logging without code collisions.

## Troubleshooting & Fixes (Previous)

### ImportError Resolution
... (same as before)

### Security Updates
... (same as before)

### Testing
Run tests with:
```bash
python test_routes.py
python test_error_system.py
```
