from werkzeug.security import generate_password_hash, check_password_hash
from init_db import db
import random
from datetime import datetime
from sqlalchemy import CheckConstraint

class User(db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(400), nullable=False)
    
    # Personal Details
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    aadhaar_number = db.Column(db.String(12), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    
    trips = db.relationship("Trip", backref="user", lazy=True)
    
    # Add constraints
    __table_args__ = (
        CheckConstraint('LENGTH(aadhaar_number) = 12', name='aadhaar_length_check'),
        CheckConstraint("gender IN ('Male', 'Female', 'Other')", name='gender_check'),
        CheckConstraint('age >= 0 AND age <= 150', name='age_range_check'),
    )

    def __init__(self, email, name, phone_number, aadhaar_number, date_of_birth, 
                 gender, age, password=None, password_hash=None, user_id=None):
        self.user_id = user_id or f"USER-{random.randint(1000, 9999)}"
        self.email = email
        self.name = name
        self.phone_number = phone_number
        
        # Validate Aadhaar number
        if not self._validate_aadhaar(aadhaar_number):
            raise ValueError("Aadhaar number must be exactly 12 digits")
        self.aadhaar_number = aadhaar_number
        
        # Handle date of birth
        if isinstance(date_of_birth, str):
            try:
                self.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError("Date of birth must be in YYYY-MM-DD format")
        else:
            self.date_of_birth = date_of_birth
        
        # Validate gender
        if gender not in ['Male', 'Female', 'Other']:
            raise ValueError("Gender must be 'Male', 'Female', or 'Other'")
        self.gender = gender
        
        # Validate age
        if not isinstance(age, int) or age < 0 or age > 150:
            raise ValueError("Age must be a valid integer between 0 and 150")
        self.age = age
        
        # Handle password
        if password_hash:
            self.password_hash = password_hash
        elif password:
            self.password_hash = generate_password_hash(password)
        else:
            raise ValueError("Either password or password_hash must be provided")

    def _validate_aadhaar(self, aadhaar_number):
        """Validate Aadhaar number - must be exactly 12 digits"""
        return (isinstance(aadhaar_number, str) and 
                len(aadhaar_number) == 12 and 
                aadhaar_number.isdigit())

    def set_password(self, password):
        """Hashes the password and stores it."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks a password against the stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def calculate_age_from_dob(self):
        """Calculate age from date of birth"""
        today = datetime.now().date()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    def update_age_from_dob(self):
        """Update age field based on current date and DOB"""
        self.age = self.calculate_age_from_dob()
    
    def to_dict(self, include_sensitive=False):
        """Convert object to dictionary (for JSON response / DB storage)"""
        user_dict = {
            "user_id": self.user_id,
            "email": self.email,
            "name": self.name,
            "phone_number": self.phone_number,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "gender": self.gender,
            "age": self.age,
        }
        
        # Only include sensitive data if explicitly requested
        if include_sensitive:
            user_dict["aadhaar_number"] = self.aadhaar_number
            
        return user_dict

    def __repr__(self):
        return f"<User {self.name} ({self.email})>"