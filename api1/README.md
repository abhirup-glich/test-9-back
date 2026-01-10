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
