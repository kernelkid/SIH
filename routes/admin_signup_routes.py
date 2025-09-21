from flask import Blueprint, request, jsonify
from init_db import db
from models.admin_model import Admin
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

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

        # Check if ADMIN_CREATION_KEY is configured
        if not ADMIN_CREATION_KEY:
            logger.error("ADMIN_CREATION_KEY not configured in environment")
            return jsonify({"error": "Admin creation not configured"}), 500

        # Secret key validation
        if data.get("secret_key") != ADMIN_CREATION_KEY:
            logger.warning(f"Invalid admin creation attempt from IP: {request.remote_addr}")
            return jsonify({"error": "Unauthorized. Invalid secret key."}), 403

        email = data.get("email", "").strip()
        password = data.get("password", "")

        # Basic field validation
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Simple email validation
        if "@" not in email or "." not in email:
            return jsonify({"error": "Invalid email format"}), 400

        # Password length check
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        # Check if admin already exists
        if Admin.query.filter_by(email=email).first():
            return jsonify({"error": "Admin with this email already exists"}), 409

        # Create new admin
        new_admin = Admin(email=email, password=password)
        db.session.add(new_admin)
        db.session.commit()

        logger.info(f"New admin created: {email}")

        return jsonify({
            "message": "Admin created successfully", 
            "admin": new_admin.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create admin: {e}")
        return jsonify({"error": "Failed to create admin", "details": str(e)}), 500