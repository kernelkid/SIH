from flask import Blueprint, jsonify, request
from functools import wraps
from models.user_model import users  # import your existing users list or model
from routes.trip_routes import trips   # import existing trips list

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Decorator to restrict routes to admin users
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # In real app, get user info from JWT
        role = request.args.get("role", "user")  # temporary for testing
        if role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function

# Get all users
@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    # Read directly from your existing users model
    all_users = []
    for user in users:  # users is your User model list
        all_users.append({
            "id": user.get("id"),
            "username": user.get("username"),
            "email": user.get("email"),
            "role": user.get("role"),
            "consent": user.get("consent")
        })
    return jsonify({"users": all_users}), 200

# Get all trips
@admin_bp.route('/trips', methods=['GET'])
@admin_required
def get_trips():
    return jsonify({"trips": trips}), 200
