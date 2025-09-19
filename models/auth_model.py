from werkzeug.security import generate_password_hash, check_password_hash
from init_db import db
import random

class Auth(db.Model):
    __tablename__ = "auth"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(400), nullable=False)
    
    # Relationship to User model
    user = db.relationship("User", backref="auth", uselist=False, lazy=True)

    def __init__(self, email, password, user_id=None):
        self.user_id = user_id or f"USER-{random.randint(1000, 9999)}"
        self.email = email.lower().strip()
        
        if not password:
            raise ValueError("Password is required")
        self.password_hash = generate_password_hash(password)

    def set_password(self, password):
        """Hashes the password and stores it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks a password against the stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert auth object to dictionary (excludes sensitive data)"""
        return {
            "user_id": self.user_id,
            "email": self.email,
        }

    def __repr__(self):
        return f"<Auth {self.email} ({self.user_id})>"