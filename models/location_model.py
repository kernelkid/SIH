from init_db import db
from datetime import datetime

class LocationData(db.Model):
    __tablename__ = 'location_data'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    accuracy = db.Column(db.Float)
    altitude = db.Column(db.Float)
    altitude_accuracy = db.Column(db.Float)
    heading = db.Column(db.Float)
    speed = db.Column(db.Float)  # meters per second
    # Address fields (from reverse geocoding)
    full_address = db.Column(db.Text)
    formatted_address = db.Column(db.Text)
    street_number = db.Column(db.String(20))
    street_name = db.Column(db.String(200))
    neighborhood = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100))
    country_code = db.Column(db.String(5))
    
    # Status flags
    address_resolved = db.Column(db.Boolean, default=False)
    geocoding_failed = db.Column(db.Boolean, default=False)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    address_updated_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'coordinates': {
                'latitude': self.latitude,
                'longitude': self.longitude,
                'accuracy': self.accuracy,
                'altitude': self.altitude,
                'altitude_accuracy': self.altitude_accuracy,
                'heading': self.heading,
                'speed': self.speed,
            },
            'address': {
                'full_address': self.full_address,
                'formatted_address': self.formatted_address,
                'street_number': self.street_number,
                'street_name': self.street_name,
                'neighborhood': self.neighborhood,
                'city': self.city,
                'state': self.state,
                'postal_code': self.postal_code,
                'country': self.country,
                'country_code': self.country_code,
                'address_resolved': self.address_resolved
            },
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'address_updated_at': self.address_updated_at.isoformat() if self.address_updated_at else None
        }
    def get_simple_address(self):
        """Get a simple readable address"""
        if not self.address_resolved:
            return f"Near {self.latitude:.4f}, {self.longitude:.4f}"
        
        return self.formatted_address or self.full_address or f"{self.city}, {self.state}"


class MotionData(db.Model):
    __tablename__ = 'motion_data'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
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
    
    # Associated location (optional)
    location_id = db.Column(db.Integer, db.ForeignKey('location_data.id'))
    location = db.relationship('LocationData', backref='motion_events')
    
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
            'activity': {
                'type': self.activity_type,
                'confidence': self.confidence
            },
            'location_id': self.location_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }