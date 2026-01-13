import psycopg2
import psycopg2.extras
import os
import json
import numpy as np

# Configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "face_recognition_db"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "abhirup"),
    "port": os.getenv("DB_PORT", "5432"),
}

def connect_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        return conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None, None

def migrate():
    conn, cur = connect_db()
    if not conn:
        return

    print("Connected to database. Starting migration...")

    # 1. Update 'students' table
    print("Checking 'students' table...")
    
    # Check if columns exist
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'students'
    """)
    columns = [row['column_name'] for row in cur.fetchall()]
    
    new_columns = ['emb_left', 'emb_center', 'emb_right']
    
    for col in new_columns:
        if col not in columns:
            print(f"Adding column '{col}' to students table...")
            cur.execute(f"ALTER TABLE students ADD COLUMN {col} FLOAT8[]")
        else:
            print(f"Column '{col}' already exists in students table.")

    # Data Migration: Convert JSONB 'face_embeddings' to new columns if it exists
    if 'face_embeddings' in columns:
        print("Migrating data from 'face_embeddings' to new columns...")
        cur.execute("SELECT roll, face_embeddings FROM students")
        rows = cur.fetchall()
        
        for row in rows:
            roll = row['roll']
            embeddings = row['face_embeddings']
            
            if not embeddings:
                continue
                
            emb_left = None
            emb_center = None
            emb_right = None
            
            if isinstance(embeddings, dict):
                emb_left = embeddings.get('left')
                emb_center = embeddings.get('center')
                emb_right = embeddings.get('right')
            elif isinstance(embeddings, list):
                # Assume list order or just put first in center?
                # Better safe than sorry, maybe just log it. 
                # Assuming list might be [left, center, right] or just one.
                if len(embeddings) > 0:
                    emb_center = embeddings[0]
            
            updates = []
            values = []
            
            if emb_left:
                updates.append("emb_left = %s")
                values.append(emb_left)
            if emb_center:
                updates.append("emb_center = %s")
                values.append(emb_center)
            if emb_right:
                updates.append("emb_right = %s")
                values.append(emb_right)
                
            if updates:
                values.append(roll)
                query = f"UPDATE students SET {', '.join(updates)} WHERE roll = %s"
                cur.execute(query, tuple(values))
                print(f"Migrated embeddings for student {roll}")

    # 2. Update 'attendance' table
    print("Checking 'attendance' table...")
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'attendance'
    """)
    att_columns = [row['column_name'] for row in cur.fetchall()]
    
    if 'confidence' not in att_columns:
        print("Adding column 'confidence' to attendance table...")
        cur.execute("ALTER TABLE attendance ADD COLUMN confidence FLOAT8")
    else:
        print("Column 'confidence' already exists in attendance table.")

    print("Migration completed successfully.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    migrate()
