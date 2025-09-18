from werkzeug.security import generate_password_hash, check_password_hash
import hashlib

# Fake DB
users = [
    {
        "id": 1,
        "username": "tanishka",
        "email": "admin@example.com",
        "password": hashlib.sha256("adminpassword123".encode()).hexdigest(),
        "role": "admin",
        "consent": True
    },
    {
        "id": 2,
        "username": "user1",
        "email": "user1@example.com",
        "password": hashlib.sha256("userpassword123".encode()).hexdigest(),
        "role": "user",
        "consent": False
    },
    {
        "id": 3,
        "username": "user2",
        "email": "user2@example.com",
        "password": hashlib.sha256("userpassword456".encode()).hexdigest(),
        "role": "user",
        "consent": True
    }
]

class User:
    def __init__(self, email, password=None, google_id=None):
        self.email = email
        self.password_hash = generate_password_hash(password) if password else None
        self.google_id = google_id
        self.consent = {  # default: not given
            "gps": False,
            "notifications": False,
            "motion_activity": False
        }

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
