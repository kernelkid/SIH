from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.trip_model import Trip
from init_db import db
from models.user_model import User 
from datetime import datetime

trip_bp = Blueprint("trip", __name__)

# --- Add Trip ---
@trip_bp.route('/add_trip', methods=['POST'])
def add_trip():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        # Required fields validation
        required_fields = ["origin", "destination", "start_time", "end_time", "mode_of_travel"]
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

        # Validate datetime format
        try:
            datetime.fromisoformat(data["start_time"])
            datetime.fromisoformat(data["end_time"])
        except ValueError:
            return jsonify({"error": "start_time and end_time must be ISO format (YYYY-MM-DDTHH:MM:SS)"}), 400

        # Create Trip object
        trip = Trip(
            origin=data["origin"],
            destination=data["destination"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            mode_of_travel=data["mode_of_travel"],
            vehicle_type=data.get("vehicle_type"),
            fuel_type=data.get("fuel_type"),
            accompanying_travellers=data.get("accompanying_travellers", [])
        )

        db.session.add(trip)
        db.session.commit()

        return jsonify({"message": "Trip added successfully", "trip": trip.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Something went wrong", "details": str(e)}), 500


# Get all trips of the logged-in user
@trip_bp.route("/my-trips", methods=["GET"])
@jwt_required()
def get_my_trips():
    try:
        # Get current user's email (or id) from JWT
        current_user_email = get_jwt_identity()
        
        # Find user in DB
        user = User.query.filter_by(email=current_user_email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get all trips of this user
        trips = Trip.query.filter_by(user_id=user.id).all()
        
        # Convert trips to dict
        trips_list = [trip.to_dict() for trip in trips]
        
        return jsonify({
            "user": user.email,
            "total_trips": len(trips_list),
            "trips": trips_list
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
