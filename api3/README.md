# Admin Service

This microservice handles administrative tasks like managing students and viewing attendance logs.

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables in `.env`.
3. Run: `python run.py`

## API

- `GET /api/students`: List all students (JWT required)
- `GET /api/check_attendance`: View attendance log (JWT required)
- `PUT /api/students/<roll>`: Update student (JWT required)
- `DELETE /api/students/<roll>`: Delete student (JWT required)

## Docker

Build: `docker build -t admin-service .`
Run: `docker run -p 5003:5003 --env-file .env admin-service`
