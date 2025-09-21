# services/activity_classifier.py
import math

class ActivityClassifier:
    @staticmethod
    def classify_activity(motion_data, location_data=None):
        """
        Classify user activity based on motion and location data
        Returns: (activity_type, confidence)
        """
        if not motion_data:
            return "unknown", 0.0
        
        # Calculate total acceleration magnitude
        acc_x = motion_data.get('acceleration', {}).get('x', 0) or 0
        acc_y = motion_data.get('acceleration', {}).get('y', 0) or 0
        acc_z = motion_data.get('acceleration', {}).get('z', 0) or 0
        
        total_acc = math.sqrt(acc_x**2 + acc_y**2 + acc_z**2)
        
        # Get speed from location data if available
        speed = 0
        if location_data and location_data.get('speed'):
            speed = location_data['speed'] * 3.6  # Convert m/s to km/h
        
        # Classification logic
        if total_acc < 0.5:
            return "stationary", 0.8
        elif speed > 50:
            return "driving", 0.9
        elif speed > 15:
            return "cycling", 0.7
        elif total_acc > 3.0:
            return "running", 0.8
        elif total_acc > 1.0:
            return "walking", 0.7
        else:
            return "stationary", 0.6