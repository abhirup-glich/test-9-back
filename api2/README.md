# Attendance Service

This microservice handles face recognition and attendance marking.

## Setup

1. Install dependencies: `pip install -r requirements.txt`
   - Note: Includes heavy libraries like PyTorch and OpenCV.
2. Set environment variables in `.env`.
3. Run: `python run.py`

## API

- `POST /api/identify`: Identify student from base64 image
- `POST /api/mark-attendance`: Mark attendance from video stream (optional)

## Docker

Build: `docker build -t attendance-service .`
Run: `docker run -p 5002:5002 --env-file .env attendance-service`
