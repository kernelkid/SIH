from init_db import db
import random
from datetime import datetime

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
    fuel_type = db.Column(db.String(50))
    accompanying_travellers = db.Column(db.JSON)  # Store as JSON array

    def __init__(self, origin, destination, start_time, end_time,
                 mode_of_travel, vehicle_type=None, fuel_type=None,
                 accompanying_travellers=None, trip_number=None):
        self.trip_number = trip_number or f"TRIP-{random.randint(1000, 9999)}"
        self.origin = origin
        self.destination = destination
        self.start_time = start_time
        self.end_time = end_time
        self.mode_of_travel = mode_of_travel
        self.vehicle_type = vehicle_type
        self.fuel_type = fuel_type
        self.accompanying_travellers = accompanying_travellers or []

    def to_dict(self):
        """Convert object to dictionary (for JSON response / DB storage)"""
        return {
            "trip_number": self.trip_number,
            "origin": self.origin,
            "destination": self.destination,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "mode_of_travel": self.mode_of_travel,
            "vehicle_type": self.vehicle_type,
            "fuel_type": self.fuel_type,
            "accompanying_travellers": self.accompanying_travellers
        }