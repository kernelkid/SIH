from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.trip_model import Trip
from models.auth_model import Auth
from models.user_model import User
from init_db import db
from datetime import datetime

trip_bp = Blueprint("trip", __name__)

# --- Add Trip ---
@trip_bp.route('/add_trip', methods=['POST'])
@jwt_required() 
def add_trip():
    try:
        data = request.get_json(force=True)
        current_user_id = get_jwt_identity()
        
        # Find auth record by user_id (from JWT)
        auth = Auth.query.filter_by(user_id=current_user_id).first()
        if not auth:
            return jsonify({"error": "User not found"}), 404

        # Required fields validation
        required_fields = ["origin", "destination", "start_time", "end_time", "mode_of_travel"]
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

        # Validate datetime format
        try:
            start_time = datetime.fromisoformat(data["start_time"].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(data["end_time"].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({"error": "start_time and end_time must be ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400

        # Check if end_time is after start_time
        if end_time <= start_time:
            return jsonify({"error": "end_time must be after start_time"}), 400

        # Create Trip object with user_id from auth table
        trip = Trip(
            origin=data["origin"],
            destination=data["destination"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            mode_of_travel=data["mode_of_travel"],
            vehicle_type=data.get("vehicle_type"),
            accompanying_travellers=data.get("accompanying_travellers", []),
            trip_purpose=data.get("trip_purpose"),
            additional_info=data.get("additional_info"),
            user_id=auth.user_id  # Use the user_id from auth table
        )

        db.session.add(trip)
        db.session.commit()

        return jsonify({
            "message": "Trip added successfully", 
            "trip": trip.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Something went wrong", "details": str(e)}), 500


# Get all trips of the logged-in user
@trip_bp.route("/my-trips", methods=["GET"])
@jwt_required()
def get_my_trips():
    try:
        # Get current user's user_id from JWT
        current_user_id = get_jwt_identity()
        
        # Find auth record by user_id
        auth = Auth.query.filter_by(user_id=current_user_id).first()
        if not auth:
            return jsonify({"error": "User not found"}), 404
        
        # Get all trips of this user using the user_id from auth
        trips = Trip.query.filter_by(user_id=auth.user_id).all()
        
        # Convert trips to dict
        trips_list = [trip.to_dict() for trip in trips]
        
        return jsonify({
            "user_id": auth.user_id,
            "email": auth.email,
            "total_trips": len(trips_list),
            "trips": trips_list
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Get specific trip by trip_number
@trip_bp.route("/trip/<trip_number>", methods=["GET"])
@jwt_required()
def get_trip(trip_number):
    try:
        # Get current user's user_id from JWT
        current_user_id = get_jwt_identity()
        
        # Find auth record by user_id
        auth = Auth.query.filter_by(user_id=current_user_id).first()
        if not auth:
            return jsonify({"error": "User not found"}), 404
        
        # Get the specific trip (ensure it belongs to current user)
        trip = Trip.query.filter_by(trip_number=trip_number, user_id=auth.user_id).first()
        
        if not trip:
            return jsonify({"error": "Trip not found"}), 404
        
        return jsonify({
            "message": "Trip retrieved successfully",
            "trip": trip.to_dict()
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Update specific trip
@trip_bp.route("/trip/<trip_number>", methods=["PUT"])
@jwt_required()
def update_trip(trip_number):
    try:
        data = request.get_json(force=True)
        current_user_id = get_jwt_identity()
        
        # Find auth record by user_id
        auth = Auth.query.filter_by(user_id=current_user_id).first()
        if not auth:
            return jsonify({"error": "User not found"}), 404
        
        # Get the specific trip (ensure it belongs to current user)
        trip = Trip.query.filter_by(trip_number=trip_number, user_id=auth.user_id).first()
        
        if not trip:
            return jsonify({"error": "Trip not found"}), 404

        # Fields that can be updated
        updatable_fields = [
            'origin', 'destination', 'start_time', 'end_time', 
            'mode_of_travel', 'vehicle_type', 'accompanying_travellers',
            'trip_purpose', 'additional_info'
        ]
        
        updated_fields = []
        
        for field in updatable_fields:
            if field in data:
                new_value = data[field]
                
                # Special validation for datetime fields
                if field in ['start_time', 'end_time']:
                    try:
                        datetime.fromisoformat(new_value.replace('Z', '+00:00'))
                    except ValueError:
                        return jsonify({"error": f"{field} must be ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400
                
                # Update if different
                if getattr(trip, field) != new_value:
                    setattr(trip, field, new_value)
                    updated_fields.append(field)
        
        if not updated_fields:
            return jsonify({"message": "No changes detected"}), 200
        
        # Additional validation: check if end_time is after start_time
        if hasattr(trip, 'start_time') and hasattr(trip, 'end_time'):
            try:
                start = datetime.fromisoformat(trip.start_time.replace('Z', '+00:00'))
                end = datetime.fromisoformat(trip.end_time.replace('Z', '+00:00'))
                if end <= start:
                    return jsonify({"error": "end_time must be after start_time"}), 400
            except:
                pass  # If datetime parsing fails, skip this validation
        
        db.session.commit()
        
        return jsonify({
            "message": "Trip updated successfully",
            "updated_fields": updated_fields,
            "trip": trip.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update trip", "details": str(e)}), 500


# Delete specific trip
@trip_bp.route("/trip/<trip_number>", methods=["DELETE"])
@jwt_required()
def delete_trip(trip_number):
    try:
        current_user_id = get_jwt_identity()
        
        # Find auth record by user_id
        auth = Auth.query.filter_by(user_id=current_user_id).first()
        if not auth:
            return jsonify({"error": "User not found"}), 404
        
        # Get the specific trip (ensure it belongs to current user)
        trip = Trip.query.filter_by(trip_number=trip_number, user_id=auth.user_id).first()
        
        if not trip:
            return jsonify({"error": "Trip not found"}), 404
        
        db.session.delete(trip)
        db.session.commit()
        
        return jsonify({"message": "Trip deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete trip", "details": str(e)}), 500