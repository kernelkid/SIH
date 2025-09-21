from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user_model import User
from models.auth_model import Auth  # Make sure to import your Auth model
from init_db import db
from datetime import datetime
import re


user_bp = Blueprint('user', __name__)


@user_bp.route("/status", methods=["GET"])
@jwt_required()
def get_profile_status():
    """
    Get current profile completion status
    """
    try:
        # Get current user
        current_user_id = get_jwt_identity()
        auth = Auth.query.filter_by(user_id=current_user_id).first()
        if not auth:
            return jsonify({"error": "Authentication failed"}), 401
        
        user = User.query.filter_by(auth_id=auth.id).first()
        if not user:
            return jsonify({"error": "User profile not found"}), 404
        
        # Check which fields are missing
        required_fields = {
            'name': user.name,
            'phone_number': user.phone_number,
            'date_of_birth': user.date_of_birth,
            'gender': user.gender
        }
        
        optional_fields = {
            'aadhaar_number': user.aadhaar_number,
            'age': user.age
        }
        
        missing_required = [field for field, value in required_fields.items() if not value]
        missing_optional = [field for field, value in optional_fields.items() if not value]
        
        profile_complete = len(missing_required) == 0
        completion_percentage = ((len(required_fields) - len(missing_required)) / len(required_fields)) * 100
        
        return jsonify({
            "profile_complete": profile_complete,
            "completion_percentage": round(completion_percentage, 2),
            "missing_required_fields": missing_required,
            "missing_optional_fields": missing_optional,
            "user": user.to_dict(include_sensitive=False)
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": "Failed to get profile status",
            "details": str(e)
        }), 500