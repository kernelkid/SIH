from flask import Blueprint, jsonify, request
from models.user_model import User
from models.trip_model import Trip
from models.consent_model import Consent
from models.location_model import LocationData, MotionData
from init_db import db
from utils.auth_utils import admin_required
from services.admin_service import AdminService
from utils.pagination_utils import format_pagination_response
import logging

logger = logging.getLogger(__name__)
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Get all users
@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        users = User.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        if not users.items:
            return jsonify({"message": "No users found", "users": []}), 200
            
        all_users = []
        for user in users.items:
            # Get user stats
            trip_count = Trip.query.filter_by(user_id=user.id).count()
            location_count = LocationData.query.filter_by(user_id=user.id).count()
            
            user_data = user.to_dict()
            user_data.update({
                "id": user.id,  # Include database ID for admin operations
                "trip_count": trip_count,
                "location_count": location_count
            })
            all_users.append(user_data)
        
        response_data = format_pagination_response(users, all_users)
        response_data["message"] = f"Found {users.total} users"
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Failed to fetch users: {e}")
        return jsonify({"error": "Failed to fetch users"}), 500

# Get all trips
@admin_bp.route('/trips', methods=['GET'])
@admin_required
def get_trips():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        user_id = request.args.get('user_id', type=int)
        
        query = Trip.query
        if user_id:
            query = query.filter_by(user_id=user_id)
            
        trips = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        if not trips.items:
            return jsonify({"message": "No trips found", "trips": []}), 200
            
        all_trips = []
        for trip in trips.items:
            trip_data = trip.to_dict()
            trip_data["id"] = trip.id  # Include database ID for admin operations
            
            # Get user email for this trip
            user = User.query.get(trip.user_id)
            trip_data["user_email"] = user.email if user else "Unknown"
            
            all_trips.append(trip_data)
        
        response_data = format_pagination_response(trips, all_trips)
        response_data["message"] = f"Found {trips.total} trips"
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Failed to fetch trips: {e}")
        return jsonify({"error": "Failed to fetch trips"}), 500



# Get specific user by ID
@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    try:
        # user_id is now an integer (database primary key)
        user = User.query.get(user_id)  # Looks up by primary key (id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Store user info before deletion
        user_string_id = user.user_id  # The string ID like "USER-1001"
        user_email = user.email
        
        result = AdminService.delete_user_cascade_by_id(user_id)  # Pass integer ID
        
        if not result:
            return jsonify({"error": "User not found"}), 404
        
        logger.info(f"Successfully deleted user {user_string_id} (ID: {user_id}) and all associated data")
        
        return jsonify({
            "message": f"User {user_string_id} (ID: {user_id}) and all associated data deleted successfully",
            "deleted_data": {
                "user_id": user_string_id,  # String ID for reference
                "database_id": user_id,     # Integer ID used for deletion
                "email": user_email,
                "trips": result["deleted_stats"]["trips"],
                "locations": result["deleted_stats"]["locations"],
                "motions": result["deleted_stats"]["motions"],
                "consents": result["deleted_stats"]["consents"]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to delete user ID {user_id}: {e}")
        return jsonify({"error": "Failed to delete user", "details": str(e)}), 500

# Get specific trip by trip number
@admin_bp.route('/trips/<trip_number>', methods=['GET'])
@admin_required
def get_trip(trip_number):
    try:
        trip = Trip.query.filter_by(trip_number=trip_number).first()
        if not trip:
            return jsonify({"error": "Trip not found"}), 404
        
        trip_data = trip.to_dict()
        trip_data["id"] = trip.id
        
        # Get user information
        user = User.query.get(trip.user_id)
        trip_data["user"] = user.to_dict() if user else None
        
        # Get associated tracking data
        location_count = LocationData.query.filter_by(user_id=trip.user_id).count()
        motion_count = MotionData.query.filter_by(user_id=trip.user_id).count()
        
        trip_data["tracking_data"] = {
            "location_points": location_count,
            "motion_points": motion_count
        }
            
        return jsonify({
            "message": "Trip found",
            "trip": trip_data
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to fetch trip {trip_number}: {e}")
        return jsonify({"error": "Failed to fetch trip"}), 500




# Bulk delete users (using AdminService)
@admin_bp.route('/users/bulk-delete', methods=['POST'])
@admin_required
def bulk_delete_users():
    try:
        data = request.get_json()
        user_ids = data.get('user_ids', [])
        
        if not user_ids or not isinstance(user_ids, list):
            return jsonify({"error": "user_ids array is required"}), 400
        
        result = AdminService.bulk_delete_users(user_ids)
        
        logger.info(f"Bulk delete completed: {len(result['deleted_users'])} users deleted, {len(result['failed_users'])} failed")
        
        return jsonify({
            "message": "Bulk delete completed",
            "results": result
        }), 200
        
    except Exception as e:
        logger.error(f"Bulk delete failed: {e}")
        return jsonify({"error": "Bulk delete failed", "details": str(e)}), 500

# Get database statistics (using AdminService)
@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_database_stats():
    try:
        stats = AdminService.get_database_statistics()
        
        return jsonify({
            "message": "Database statistics retrieved",
            "stats": stats
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return jsonify({"error": "Failed to get database statistics"}), 500
    


# Search users
@admin_bp.route('/users/search', methods=['GET'])
@admin_required
def search_users():
    try:
        query = request.args.get('q', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        if not query:
            return jsonify({"error": "Search query 'q' parameter is required"}), 400
        
        # Search in email and user_id
        users = User.query.filter(
            db.or_(
                User.email.ilike(f'%{query}%'),
                User.user_id.ilike(f'%{query}%')
            )
        ).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        search_results = []
        for user in users.items:
            user_data = user.to_dict()
            user_data["id"] = user.id
            user_data["trip_count"] = Trip.query.filter_by(user_id=user.id).count()
            search_results.append(user_data)
        
        response_data = format_pagination_response(users, search_results)
        response_data.update({
            "message": f"Found {users.total} users matching '{query}'",
            "search_query": query
        })
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"User search failed: {e}")
        return jsonify({"error": "Search failed"}), 500
    


# Add this to your admin_bp routes

@admin_bp.route('/users', methods=['POST'])
@admin_required
def create_user():
    try:
        data = request.get_json()
        
        # Validate required fields
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"error": "User with this email already exists"}), 409
        
        # Optional fields with defaults
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        phone_number = data.get('phone_number', '')
        is_admin = data.get('is_admin', False)  # Admin can create other admins
        
        # Create new user
        new_user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            is_admin=is_admin
        )
        
        # Set password (assuming your User model has a set_password method)
        new_user.set_password(password)
        
        # Save to database
        db.session.add(new_user)
        db.session.commit()
        
        logger.info(f"Admin created new user: {new_user.user_id} ({email})")
        
        # Return user data (excluding password)
        user_data = new_user.to_dict()
        user_data["id"] = new_user.id  # Include database ID for admin operations
        
        return jsonify({
            "message": "User created successfully",
            "user": user_data
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create user: {e}")
        return jsonify({"error": "Failed to create user", "details": str(e)}), 500