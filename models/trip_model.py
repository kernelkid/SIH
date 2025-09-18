# models/trip_model.py

import random

# Temporary fake DB
trips = [
    {
        "trip_number": 1,
        "origin": "Greater Noida",
        "destination": "Delhi",
        "start_time": "2025-09-20 08:00",
        "end_time": "2025-09-20 10:00",
        "mode_of_travel": "Car",
        "vehicle_type": "Sedan",
        "accompanying_travellers": ["user1", "user2"]
    },
    {
        "trip_number": 2,
        "origin": "Delhi",
        "destination": "Jaipur",
        "start_time": "2025-09-25 06:00",
        "end_time": "2025-09-25 12:00",
        "mode_of_travel": "Train",
        "vehicle_type": "Shatabdi Express",
        "accompanying_travellers": ["user3"]
    },
    {
        "trip_number": 3,
        "origin": "Mumbai",
        "destination": "Pune",
        "start_time": "2025-10-01 09:30",
        "end_time": "2025-10-01 12:00",
        "mode_of_travel": "Bus",
        "vehicle_type": "Volvo AC",
        "accompanying_travellers": []
    }
]


class Trip:
    def __init__(self, origin, destination, start_time, end_time,
                 mode_of_travel, vehicle_type=None, fuel_type=None,
                 accompanying_travellers=None, trip_number=None):
        # Auto-generate if not given
        self.trip_number = trip_number or f"TRIP-{random.randint(1000, 9999)}"
        self.origin = origin
        self.destination = destination
        self.start_time = start_time
        self.end_time = end_time
        self.mode_of_travel = mode_of_travel
        self.vehicle_type = vehicle_type
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
            "accompanying_travellers": self.accompanying_travellers
        }
