# user_model.py
from init_db import db
from datetime import datetime
from sqlalchemy import CheckConstraint

class User(db.Model):
    __tablename__ = "users"
    
    # Primary key - this is what other tables should reference
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign key to Auth table
    auth_id = db.Column(db.Integer, db.ForeignKey('auth.id'), unique=True, nullable=False)
    
    # Personal Details - all nullable for initial signup
    name = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(15), nullable=True)
    aadhaar_number = db.Column(db.String(12), unique=True, nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    
    # Add constraints
    __table_args__ = (
        CheckConstraint('aadhaar_number IS NULL OR LENGTH(aadhaar_number) = 12', name='aadhaar_length_check'),
        CheckConstraint("gender IS NULL OR gender IN ('Male', 'Female', 'Other')", name='gender_check'),
        CheckConstraint('age IS NULL OR (age >= 0 AND age <= 150)', name='age_range_check'),
    )

    def __init__(self, auth_id, name=None, phone_number=None, aadhaar_number=None, 
                 date_of_birth=None, gender=None, age=None):
        self.auth_id = auth_id
        
        if name:
            self.name = name.strip()
        if phone_number:
            self.phone_number = phone_number.strip()
        
        # Validate Aadhaar number if provided
        if aadhaar_number:
            if not self._validate_aadhaar(aadhaar_number):
                raise ValueError("Aadhaar number must be exactly 12 digits")
            self.aadhaar_number = aadhaar_number.strip()
        
        # Handle date of birth
        if date_of_birth:
            if isinstance(date_of_birth, str):
                try:
                    self.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                except ValueError:
                    raise ValueError("Date of birth must be in YYYY-MM-DD format")
            else:
                self.date_of_birth = date_of_birth
        
        # Validate gender if provided
        if gender:
            if gender not in ['Male', 'Female', 'Other']:
                raise ValueError("Gender must be 'Male', 'Female', or 'Other'")
            self.gender = gender
        
        # Validate age if provided
        if age is not None:
            if not isinstance(age, int) or age < 0 or age > 150:
                raise ValueError("Age must be a valid integer between 0 and 150")
            self.age = age

    def _validate_aadhaar(self, aadhaar_number):
        """Validate Aadhaar number - must be exactly 12 digits"""
        return (isinstance(aadhaar_number, str) and 
                len(aadhaar_number) == 12 and 
                aadhaar_number.isdigit())
    
    def calculate_age_from_dob(self):
        """Calculate age from date of birth"""
        if not self.date_of_birth:
            return None
        today = datetime.now().date()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    def update_age_from_dob(self):
        """Update age field based on current date and DOB"""
        if self.date_of_birth:
            self.age = self.calculate_age_from_dob()
    
    # Properties to access auth data easily
    @property
    def user_id(self):
        """Get the user_id from auth"""
        return self.auth.user_id if self.auth else None
    
    @property 
    def email(self):
        """Get the email from auth"""
        return self.auth.email if self.auth else None

    def get_trips(self):
        """Get all trips for this user"""
        from models.trip_model import Trip
        return Trip.query.filter_by(user_id=self.id).all()
    
    def to_dict(self, include_sensitive=False):
        """Convert object to dictionary (for JSON response / DB storage)"""
        user_dict = {
            "id": self.id,
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