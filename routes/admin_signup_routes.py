from flask import Blueprint, request, jsonify
import hashlib
from models.user_model import users  # your existing users list or DB

admin_signup_bp = Blueprint("admin_signup", __name__)

# Secret key only known to existing admins
ADMIN_CREATION_KEY = "super-secret-admin-key-123"

@admin_signup_bp.route('/create_admin', methods=['POST'])
def create_admin():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    secret_key = data.get("secret_key")
    if secret_key != ADMIN_CREATION_KEY:
        return jsonify({"error": "Unauthorized"}), 403

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    # Hash the password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    # Create admin user
    new_admin = {
        "id": len(users) + 1,
        "username": username,
        "email": email,
        "password": hashed_password,
        "role": "admin",
        "consent": True
    }

    users.append(new_admin)

    return jsonify({"message": "Admin created successfully", "admin": new_admin}), 201
