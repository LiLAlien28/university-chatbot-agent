import sqlite3
import os
from datetime import datetime

# Get database path from environment or default to local directory
DB_PATH = os.getenv("SQLITE_DB_PATH", "app/database/university_chatbot.db")

def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema and populates default data."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('student', 'professor'))
    )
    """)
    
    # 2. Courses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        code TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT
    )
    """)
    
    # 3. Materials table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        file_path TEXT NOT NULL,
        course_code TEXT NOT NULL,
        uploader_id INTEGER NOT NULL,
        material_type TEXT NOT NULL CHECK(material_type IN ('notes', 'paper', 'assignment')),
        popular_score INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(course_code) REFERENCES courses(code),
        FOREIGN KEY(uploader_id) REFERENCES users(id)
    )
    """)
    
    # 4. Study Groups table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS study_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code TEXT NOT NULL,
        group_name TEXT NOT NULL,
        meeting_info TEXT NOT NULL,
        FOREIGN KEY(course_code) REFERENCES courses(code)
    )
    """)
    
    # 5. Deadlines table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deadlines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        due_date TEXT NOT NULL,
        course_code TEXT NOT NULL,
        FOREIGN KEY(course_code) REFERENCES courses(code)
    )
    """)
    
    # 6. Analytics table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT,
        material_id_clicked INTEGER,
        count INTEGER DEFAULT 1,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(material_id_clicked) REFERENCES materials(id)
    )
    """)
    
    # Insert default courses if not exists
    cursor.execute("SELECT COUNT(*) FROM courses")
    if cursor.fetchone()[0] == 0:
        default_courses = [
            ("CS101", "Introduction to Computer Science", "Fundamentals of programming, data structures, and algorithms."),
            ("MATH101", "Calculus I", "Limits, derivatives, integrals, and real-world applications of calculus."),
            ("PHY101", "General Physics I", "Mechanics, kinematics, forces, work, energy, and thermodynamics."),
            ("CS201", "Database Systems", "Relational database concepts, SQL design, indexing, and transactions."),
            ("MATH201", "Linear Algebra", "Systems of linear equations, matrices, vector spaces, and eigenvalues.")
        ]
        cursor.executemany("INSERT INTO courses (code, name, description) VALUES (?, ?, ?)", default_courses)
        
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

# User Operations
def create_user(username, password_hash, role):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, role)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(user) if user else None

# Course Operations
def add_course(code, name, description):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO courses (code, name, description) VALUES (?, ?, ?)",
            (code, name, description)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def list_courses():
    conn = get_db_connection()
    cursor = conn.cursor()
    courses = cursor.execute("SELECT * FROM courses ORDER BY code ASC").fetchall()
    conn.close()
    return [dict(c) for c in courses]

# Material Operations
def add_material(title, file_path, course_code, uploader_id, material_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO materials (title, file_path, course_code, uploader_id, material_type) VALUES (?, ?, ?, ?, ?)",
            (title, file_path, course_code, uploader_id, material_type)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def list_materials(course_code=None, keyword=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT m.*, u.username as uploader, c.name as course_name FROM materials m JOIN users u ON m.uploader_id = u.id JOIN courses c ON m.course_code = c.code WHERE 1=1"
    params = []
    
    if course_code:
        query += " AND m.course_code = ?"
        params.append(course_code)
    if keyword:
        query += " AND (m.title LIKE ? OR m.material_type LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])
        
    query += " ORDER BY m.created_at DESC"
    materials = cursor.execute(query, params).fetchall()
    conn.close()
    return [dict(m) for m in materials]

def get_popular_materials(limit=5):
    conn = get_db_connection()
    cursor = conn.cursor()
    materials = cursor.execute(
        "SELECT m.*, c.name as course_name FROM materials m JOIN courses c ON m.course_code = c.code ORDER BY m.popular_score DESC, m.created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(m) for m in materials]

def increment_material_popularity(material_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE materials SET popular_score = popular_score + 1 WHERE id = ?", (material_id,))
    conn.commit()
    conn.close()

# Deadline Operations
def add_deadline(title, due_date, course_code):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO deadlines (title, due_date, course_code) VALUES (?, ?, ?)",
            (title, due_date, course_code)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def list_deadlines(course_code=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT d.*, c.name as course_name FROM deadlines d JOIN courses c ON d.course_code = c.code WHERE 1=1"
    params = []
    if course_code:
        query += " AND d.course_code = ?"
        params.append(course_code)
    query += " ORDER BY d.due_date ASC"
    deadlines = cursor.execute(query, params).fetchall()
    conn.close()
    return [dict(d) for d in deadlines]

# Study Group Operations
def add_study_group(course_code, group_name, meeting_info):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO study_groups (course_code, group_name, meeting_info) VALUES (?, ?, ?)",
            (course_code, group_name, meeting_info)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def list_study_groups(course_code=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT s.*, c.name as course_name FROM study_groups s JOIN courses c ON s.course_code = c.code WHERE 1=1"
    params = []
    if course_code:
        query += " AND s.course_code = ?"
        params.append(course_code)
    groups = cursor.execute(query, params).fetchall()
    conn.close()
    return [dict(g) for g in groups]

# Analytics & Logs Operations
def log_analytics(query=None, material_id_clicked=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if query:
            # Check if query already exists today to update count
            today = datetime.now().strftime("%Y-%m-%d")
            existing = cursor.execute(
                "SELECT id FROM analytics WHERE query = ? AND date(timestamp) = ?",
                (query, today)
            ).fetchone()
            if existing:
                cursor.execute("UPDATE analytics SET count = count + 1 WHERE id = ?", (existing['id'],))
            else:
                cursor.execute("INSERT INTO analytics (query) VALUES (?)", (query,))
        elif material_id_clicked:
            cursor.execute("INSERT INTO analytics (material_id_clicked) VALUES (?)", (material_id_clicked,))
        conn.commit()
    finally:
        conn.close()

def get_analytics(limit=10):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Most frequent queries
    queries = cursor.execute(
        "SELECT query, SUM(count) as total_count FROM analytics WHERE query IS NOT NULL GROUP BY query ORDER BY total_count DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(q) for q in queries]
