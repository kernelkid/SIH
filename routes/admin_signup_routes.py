from flask import Blueprint, request, jsonify
from init_db import db
from models.admin_model import Admin
import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

admin_signup_bp = Blueprint("admin_signup", __name__)

# Secret key loaded from .env
ADMIN_CREATION_KEY = os.getenv("ADMIN_CREATION_KEY")

@admin_signup_bp.route('/create_admin', methods=['POST'])
def create_admin():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        # Secret key validation
        if data.get("secret_key") != ADMIN_CREATION_KEY:
            return jsonify({"error": "Unauthorized. Secret key invalid."}), 403

        email = data.get("email")
        password = data.get("password")

        # Basic field validation
        if not email or not password:
            return jsonify({"error": "username, email, and password are required"}), 400

        # Check if admin already exists
        if Admin.query.filter_by(email=email).first():
            return jsonify({"error": "Admin with this email already exists"}), 400

        # Create new admin
        new_admin = Admin(email=email, password=password)
        db.session.add(new_admin)
        db.session.commit()

        return jsonify({"message": "Admin created successfully", "admin": new_admin.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Something went wrong", "details": str(e)}), 500
