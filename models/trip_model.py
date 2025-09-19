# trip_model.py
from init_db import db
import random

class Trip(db.Model):
    __tablename__ = "trips"
    
    id = db.Column(db.Integer, primary_key=True)
    trip_number = db.Column(db.String(20), unique=True, nullable=False)
    origin = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.String(50), nullable=False)
    end_time = db.Column(db.String(50), nullable=False)
    mode_of_travel = db.Column(db.String(50), nullable=False)
    vehicle_type = db.Column(db.String(50))
    accompanying_travellers = db.Column(db.JSON)
    trip_purpose = db.Column(db.String(200))
    additional_info = db.Column(db.String(500))

    # Foreign key references users.id (the primary key)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    # Define relationship back to user
    user = db.relationship("User", backref="trips")

    def __init__(self, origin, destination, start_time, end_time,
                 mode_of_travel, vehicle_type=None, fuel_type=None,
                 accompanying_travellers=None, trip_purpose=None, 
                 additional_info=None, trip_number=None, user_id=None):
        self.trip_number = trip_number or f"TRIP-{random.randint(1000, 9999)}"
        self.origin = origin
        self.destination = destination
        self.start_time = start_time
        self.end_time = end_time
        self.mode_of_travel = mode_of_travel
        self.vehicle_type = vehicle_type
        self.accompanying_travellers = accompanying_travellers or []
        self.trip_purpose = trip_purpose
        self.additional_info = additional_info
        self.user_id = user_id

    def to_dict(self):
        """Convert object to dictionary (for JSON response / DB storage)"""
        return {
            "id": self.id,
            "trip_number": self.trip_number,
            "origin": self.origin,
            "destination": self.destination,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "mode_of_travel": self.mode_of_travel,
            "vehicle_type": self.vehicle_type,
            "accompanying_travellers": self.accompanying_travellers,
            "trip_purpose": self.trip_purpose,
            "additional_info": self.additional_info,
            "user_id": self.user_id
        }

    def __repr__(self):
        return f"<Trip {self.trip_number}: {self.origin} -> {self.destination}>"