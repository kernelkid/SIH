from init_db import db
from werkzeug.security import generate_password_hash, check_password_hash
import random

class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(400), nullable=False)

    def __init__(self, email, password, admin_id=None):
        self.admin_id = admin_id or f"ADMIN-{random.randint(1000, 9999)}"
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        """Hash the password and store it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Return a JSON-serializable dictionary of admin info."""
        return {
            "admin_id": self.admin_id,
            "email": self.email
        }

    # Optional __repr__ without username
    def __repr__(self):
        return f"<Admin {self.email}>"
