import bcrypt
import re

def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt."""
    if not password:
        raise ValueError("Password cannot be empty")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a hashed password."""
    if not password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def validate_username(username: str) -> bool:
    """Validates if username contains only alphanumeric characters, underscores and is of length 3-20."""
    if not username:
        return False
    return bool(re.match(r"^[a-zA-Z0-9_]{3,20}$", username))

def validate_course_code(code: str) -> bool:
    """Validates university course code syntax (e.g. CS101, MATH201)."""
    if not code:
        return False
    return bool(re.match(r"^[A-Z]{2,4}\d{3}$", code.upper()))

def sanitize_input(text: str) -> str:
    """Sanitizes user input by removing potential HTML/script injections."""
    if not text:
        return ""
    # Strip HTML tags
    clean = re.sub(r'<[^>]*>', '', text)
    return clean.strip()
