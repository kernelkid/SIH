from flask import Blueprint, jsonify, request
from functools import wraps
from models.user_model import User
from models.trip_model import Trip
from init_db import db

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Decorator to restrict routes to admin users
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # In real app, get user info from JWT
            role = request.args.get("role", "user")  # temporary for testing
            if role != "admin":
                return jsonify({"error": "Admin access required"}), 403
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": "Authorization failed"}), 500
    return decorated_function

# Get all users
@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    try:
        users = User.query.all()
        if not users:
            return jsonify({"message": "No users found", "users": []}), 200
            
        all_users = []
        for user in users:
            all_users.append({
                "id": user.id,
                "user_id": user.user_id,
                "email": user.email,
                # Add other fields as needed
            })
        
        return jsonify({
            "message": f"Found {len(all_users)} users",
            "users": all_users
        }), 200
        
    except Exception as e:
        return jsonify({"error": "Failed to fetch users"}), 500

# Get all trips
@admin_bp.route('/trips', methods=['GET'])
@admin_required
def get_trips():
    try:
        trips = Trip.query.all()
        if not trips:
            return jsonify({"message": "No trips found", "trips": []}), 200
            
        all_trips = []
        for trip in trips:
            all_trips.append(trip.to_dict())
        
        return jsonify({
            "message": f"Found {len(all_trips)} trips",
            "trips": all_trips
        }), 200
        
    except Exception as e:
        return jsonify({"error": "Failed to fetch trips"}), 500

# Get specific user by ID
@admin_bp.route('/users/<user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    try:
        user = User.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        return jsonify({
            "message": "User found",
            "user": user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({"error": "Failed to fetch user"}), 500

# Get specific trip by trip number
@admin_bp.route('/trips/<trip_number>', methods=['GET'])
@admin_required
def get_trip(trip_number):
    try:
        trip = Trip.query.filter_by(trip_number=trip_number).first()
        if not trip:
            return jsonify({"error": "Trip not found"}), 404
            
        return jsonify({
            "message": "Trip found",
            "trip": trip.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({"error": "Failed to fetch trip"}), 500

# Delete user
@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    try:
        user = User.query.filter_by(user_id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
            
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({"message": f"User {user_id} deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete user"}), 500

# Delete trip
@admin_bp.route('/trips/<trip_number>', methods=['DELETE'])
@admin_required
def delete_trip(trip_number):
    try:
        trip = Trip.query.filter_by(trip_number=trip_number).first()
        if not trip:
            return jsonify({"error": "Trip not found"}), 404
            
        db.session.delete(trip)
        db.session.commit()
        
        return jsonify({"message": f"Trip {trip_number} deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete trip"}), 500