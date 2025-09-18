from werkzeug.security import generate_password_hash, check_password_hash
from init_db import db
import random

class User(db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(400), nullable=False)

    def __init__(self, email, password=None, password_hash=None, user_id=None):
        self.user_id = user_id or f"USER-{random.randint(1000, 9999)}"
        self.email = email
        
        if password_hash:
            self.password_hash = password_hash
        elif password:
            self.password_hash = generate_password_hash(password)
        else:
            raise ValueError("Either password or password_hash must be provided")

    def set_password(self, password):
        """Hashes the password and stores it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks a password against the stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert object to dictionary (for JSON response / DB storage)"""
        return {
            "user_id": self.user_id,
            "email": self.email,
        }

    def __repr__(self):
        return f"<User {self.email}>"