from flask import Blueprint, request, jsonify
from models.trip_model import trips, Trip

trip_bp = Blueprint("trip", __name__)

@trip_bp.route('/add_trip', methods=['POST'])
def add_trip():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    # Create Trip object
    trip = Trip(
        origin=data.get("origin"),
        destination=data.get("destination"),
        start_time=data.get("start_time"),
        end_time=data.get("end_time"),
        mode_of_travel=data.get("mode_of_travel"),
        vehicle_type=data.get("vehicle_type"),
        accompanying_travellers=data.get("accompanying_travellers", [])
    )

    # Save to fake DB
    trips.append(trip.to_dict())

    return jsonify({"message": "Trip added successfully", "trip": trip.to_dict()}), 201


@trip_bp.route('/all_trips', methods=['GET'])
def get_all_trips():
    """Fetch all trips (for testing)"""
    return jsonify({"trips": trips}), 200
