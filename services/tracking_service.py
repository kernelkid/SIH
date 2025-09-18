from init_db import db
from datetime import datetime

class LocationData(db.Model):
    __tablename__ = 'location_data'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float)
    altitude = db.Column(db.Float)
    altitude_accuracy = db.Column(db.Float)
    heading = db.Column(db.Float)
    speed = db.Column(db.Float)  # meters per second
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'accuracy': self.accuracy,
            'altitude': self.altitude,
            'altitude_accuracy': self.altitude_accuracy,
            'heading': self.heading,
            'speed': self.speed,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class MotionData(db.Model):
    __tablename__ = 'motion_data'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # DeviceMotionEvent data
    acceleration_x = db.Column(db.Float)
    acceleration_y = db.Column(db.Float)
    acceleration_z = db.Column(db.Float)
    
    acceleration_including_gravity_x = db.Column(db.Float)
    acceleration_including_gravity_y = db.Column(db.Float)
    acceleration_including_gravity_z = db.Column(db.Float)
    
    rotation_rate_alpha = db.Column(db.Float)
    rotation_rate_beta = db.Column(db.Float)
    rotation_rate_gamma = db.Column(db.Float)
    
    # DeviceOrientationEvent data
    orientation_alpha = db.Column(db.Float)  # compass direction
    orientation_beta = db.Column(db.Float)   # front-to-back tilt
    orientation_gamma = db.Column(db.Float)  # left-to-right tilt
    
    # Derived activity type
    activity_type = db.Column(db.String(50))  # walking, running, driving, stationary, etc.
    confidence = db.Column(db.Float)  # confidence level 0-1
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'acceleration': {
                'x': self.acceleration_x,
                'y': self.acceleration_y,
                'z': self.acceleration_z
            },
            'acceleration_including_gravity': {
                'x': self.acceleration_including_gravity_x,
                'y': self.acceleration_including_gravity_y,
                'z': self.acceleration_including_gravity_z
            },
            'rotation_rate': {
                'alpha': self.rotation_rate_alpha,
                'beta': self.rotation_rate_beta,
                'gamma': self.rotation_rate_gamma
            },
            'orientation': {
                'alpha': self.orientation_alpha,
                'beta': self.orientation_beta,
                'gamma': self.orientation_gamma
            },
            'activity_type': self.activity_type,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }