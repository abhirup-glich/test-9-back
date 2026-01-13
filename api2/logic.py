import cv2
import numpy as np
import torch
import time
import threading
import sys
import base64
from datetime import datetime
import psycopg2
import psycopg2.extras
from facenet_pytorch import MTCNN, InceptionResnetV1
# import dlib
# from imutils import face_utils
from tabulate import tabulate
import argparse
import os
import json
import logging

logger = logging.getLogger(__name__)

# ===================== CONFIG =====================

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "face_recognition_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "RaunakSaha0."),
    "port": os.getenv("DB_PORT", "5432"),
}

MATCH_THRESHOLD = 0.65
BLINK_THRESHOLD = 0.20
REQUIRED_BLINKS = 2
HEAD_FRAMES = 8
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

exit_attendance = False

# ===================== MODELS =====================

mtcnn = MTCNN(keep_all=False, device=DEVICE)
facenet = InceptionResnetV1(pretrained="vggface2").eval().to(DEVICE)
# predictor = dlib.shape_predictor(os.path.join(os.path.dirname(__file__), "shape_predictor_68_face_landmarks.dat"))

# ===================== DATABASE =====================

def connect_db():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    return conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

def setup_db(cur):
    # Create tables only if they don't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            roll TEXT PRIMARY KEY,
            name TEXT,
            course TEXT,
            emb_left FLOAT8[],
            emb_center FLOAT8[],
            emb_right FLOAT8[],
            face_embeddings JSONB -- Kept for backward compatibility but deprecated
        );
        
        CREATE TABLE IF NOT EXISTS attendance (
            id SERIAL PRIMARY KEY,
            roll TEXT,
            name TEXT,
            course TEXT,
            time TIMESTAMP,
            confidence FLOAT8
        );
        
        CREATE TABLE IF NOT EXISTS classes (
            id SERIAL PRIMARY KEY,
            course TEXT,
            start_time TIMESTAMP DEFAULT NOW(),
            notes TEXT
        );
        
        -- Add comments to document the schema (only if they don't exist)
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_description 
                WHERE objoid = 'students'::regclass AND objsubid = 0
            ) THEN
                COMMENT ON TABLE students IS 'Stores student information and face embeddings';
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM pg_description 
                WHERE objoid = 'attendance'::regclass AND objsubid = 0
            ) THEN
                COMMENT ON TABLE attendance IS 'Stores attendance records';
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM pg_description 
                WHERE objoid = 'classes'::regclass AND objsubid = 0
            ) THEN
                COMMENT ON TABLE classes IS 'Logs each class session start';
            END IF;
        END $$;
    """)

# ===================== UTILS =====================

def normalize(v):
    v = np.asarray(v, dtype=np.float32).flatten()
    n = np.linalg.norm(v)
    return v if n == 0 else v / n

def cosine_sim(a, b):
    a, b = normalize(a), normalize(b)
    if a.shape != b.shape:
        return -1.0
    return float(np.dot(a, b))

def get_embedding(face):
    face = cv2.resize(face, (160,160))
    face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
    t = torch.tensor(face).permute(2,0,1).float().unsqueeze(0)/255.0
    t = t.to(DEVICE)
    with torch.no_grad():
        emb = facenet(t).cpu().numpy()[0]
    return normalize(emb)

def load_students(cur):
    # Updated to read from new columns
    cur.execute("SELECT roll, name, course, emb_left, emb_center, emb_right, face_embeddings FROM students")
    rows = cur.fetchall()
    students = []
    for r in rows:
        embs = []
        
        # Prefer new columns
        if r['emb_center']:
            if r['emb_left']: embs.append(np.array(r['emb_left']))
            if r['emb_center']: embs.append(np.array(r['emb_center']))
            if r['emb_right']: embs.append(np.array(r['emb_right']))
        
        # Fallback to JSONB if new columns are empty
        elif r['face_embeddings']:
            embeddings_json = r['face_embeddings']
            if isinstance(embeddings_json, list):
                embs = [np.array(e) for e in embeddings_json]
            elif isinstance(embeddings_json, dict):
                for key in ['center', 'left', 'right']:
                    if key in embeddings_json and embeddings_json[key]:
                        embs.append(np.array(embeddings_json[key]))
                        
        students.append((r, embs))
    return students

# ===================== REGISTRATION =====================

def process_web_image(base64_str):
    try:
        # Decode base64
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]
        img_data = base64.b64decode(base64_str)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return None

        # Detect face
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        box, _ = mtcnn.detect(rgb)
        
        if box is None:
            return None
            
        # Get largest face if multiple
        x1,y1,x2,y2 = map(int, box[0])
        h, w = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        face = frame[y1:y2, x1:x2]
        if face.size == 0:
            return None
            
        return get_embedding(face)
    except Exception as e:
        logger.error(f"Error processing web image: {e}", exc_info=True)
        return None

def register_student_web(cur, roll, name, course, images):
    # images is dict with keys: center, left, right
    
    # Allow single image registration by using center for all if others missing
    if 'center' in images and ('left' not in images or not images['left']):
        images['left'] = images['center']
    if 'center' in images and ('right' not in images or not images['right']):
        images['right'] = images['center']

    emb_center = process_web_image(images['center'])
    if emb_center is None:
        return {'status': 'error', 'message': 'Face not detected in Center photo'}
        
    emb_left = process_web_image(images['left'])
    if emb_left is None:
        return {'status': 'error', 'message': 'Face not detected in Left photo'}
        
    emb_right = process_web_image(images['right'])
    if emb_right is None:
        return {'status': 'error', 'message': 'Face not detected in Right photo'}
        
    try:
        # Insert into new columns
        cur.execute("""
            INSERT INTO students (roll, name, course, emb_left, emb_center, emb_right) 
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (roll) DO UPDATE SET
            name = EXCLUDED.name,
            course = EXCLUDED.course,
            emb_left = EXCLUDED.emb_left,
            emb_center = EXCLUDED.emb_center,
            emb_right = EXCLUDED.emb_right
        """,(roll, name, course,
             emb_left.tolist(), emb_center.tolist(), emb_right.tolist()))
             
        logger.info(f"Student {name} registered successfully via web")
        return {'status': 'success', 'message': f'Student {name} registered successfully'}
    except Exception as e:
        logger.error(f"DB Error during registration: {e}", exc_info=True)
        return {'status': 'error', 'message': str(e)}

def delete_last_attendance(cur):
    try:
        cur.execute("""
            DELETE FROM attendance 
            WHERE id = (SELECT id FROM attendance ORDER BY time DESC LIMIT 1)
            RETURNING name, time
        """)
        row = cur.fetchone()
        if row:
            return {'name': row['name'], 'time': row['time'].isoformat()}
        return None
    except Exception as e:
        logger.error(f"Error deleting last attendance: {e}", exc_info=True)
        raise

def identify_student_web(cur, image_data):
    try:
        emb = process_web_image(image_data)
        if emb is None:
            return {'status': 'error', 'message': 'No face detected'}
            
        students = load_students(cur)
        best_score, best_student = -1, None

        for s, embs in students:
            for db_emb in embs:
                score = cosine_sim(emb, db_emb)
                if score > best_score:
                    best_score, best_student = score, s

        if best_score > 0.6:
            timestamp = datetime.now()
            # Mark attendance if identified
            cur.execute("""
                INSERT INTO attendance (roll, name, course, time, confidence)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, time
            """, (best_student["roll"], best_student["name"], 
                  best_student["course"], timestamp, float(best_score)))
            
            attendance_record = cur.fetchone()
            
            return {
                'status': 'success',
                'message': f"Welcome {best_student['name']}",
                'data': {
                    'name': best_student['name'],
                    'roll': best_student['roll'],
                    'confidence': float(best_score),
                    'time': attendance_record['time'].isoformat()
                }
            }
        else:
            return {'status': 'error', 'message': 'Student not recognized', 'confidence': float(best_score)}
            
    except Exception as e:
        logger.error(f"Error identifying student: {e}", exc_info=True)
        return {'status': 'error', 'message': str(e)}
