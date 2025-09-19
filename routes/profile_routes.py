# profile_routes.py
from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.auth_model import Auth
from models.user_model import User
from init_db import db
import re
from datetime import datetime

profile_bp = Blueprint('profile', __name__)

@profile_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """Get current user's profile information"""
    try:
        # Get user_id from JWT token
        current_user_id = get_jwt_identity()
        
        # Find auth record by user_id
        auth = Auth.query.filter_by(user_id=current_user_id).first()
        if not auth or not auth.user:
            return jsonify({"error": "User not found"}), 404
        
        # Return user profile
        return jsonify({
            "message": "Profile retrieved successfully",
            "user": auth.user.to_dict(include_sensitive=True)
        }), 200
        
    except Exception as e:
        return jsonify({"error": "Failed to retrieve profile", "details": str(e)}), 500

@profile_bp.route("/profile", methods=["PUT"])
@jwt_required()
def update_profile():
    """Update current user's profile information"""
    try:
        data = request.get_json(force=True)
        
        # Get user_id from JWT token
        current_user_id = get_jwt_identity()
        
        # Find auth record by user_id
        auth = Auth.query.filter_by(user_id=current_user_id).first()
        if not auth or not auth.user:
            return jsonify({"error": "User not found"}), 404
            
        user = auth.user
        
        # Fields that can be updated
        updatable_fields = {
            'name': str,
            'phone_number': str,
            'aadhaar_number': str,
            'date_of_birth': str,
            'gender': str,
            'age': int
        }
        
        # Track changes for response
        updated_fields = []
        
        # Update each field if provided
        for field, field_type in updatable_fields.items():
            if field in data:
                new_value = data[field]
                
                # Type conversion and validation
                if field_type == int:
                    try:
                        new_value = int(new_value)
                    except (ValueError, TypeError):
                        return jsonify({"error": f"Invalid {field}: must be a number"}), 400
                
                # Field-specific validation
                if field == 'phone_number':
                    if not (isinstance(new_value, str) and new_value.isdigit() and 10 <= len(new_value) <= 15):
                        return jsonify({"error": "Phone number must be 10-15 digits"}), 400
                
                elif field == 'aadhaar_number':
                    if not user._validate_aadhaar(new_value):
                        return jsonify({"error": "Aadhaar number must be exactly 12 digits"}), 400
                    
                    # Check if Aadhaar is already taken by another user
                    existing_user = User.query.filter(
                        User.aadhaar_number == new_value,
                        User.id != user.id
                    ).first()
                    if existing_user:
                        return jsonify({"error": "Aadhaar number already exists"}), 400
                
                elif field == 'date_of_birth':
                    try:
                        # Validate date format
                        datetime.strptime(new_value, '%Y-%m-%d')
                    except ValueError:
                        return jsonify({"error": "Date of birth must be in YYYY-MM-DD format"}), 400
                
                elif field == 'gender':
                    if new_value not in ['Male', 'Female', 'Other']:
                        return jsonify({"error": "Gender must be 'Male', 'Female', or 'Other'"}), 400
                
                elif field == 'age':
                    if not (0 <= new_value <= 150):
                        return jsonify({"error": "Age must be between 0 and 150"}), 400
                
                elif field == 'name':
                    if not new_value or len(new_value.strip()) < 1:
                        return jsonify({"error": "Name cannot be empty"}), 400
                    new_value = new_value.strip()
                
                # Update the field if it's different from current value
                current_value = getattr(user, field)
                if current_value != new_value:
                    setattr(user, field, new_value)
                    updated_fields.append(field)
        
        # Handle email update separately (updates auth table)
        if 'email' in data:
            new_email = data['email'].strip().lower()
            
            # Email format validation
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, new_email):
                return jsonify({"error": "Invalid email format"}), 400
            
            # Check if email is already taken by another user
            existing_auth = Auth.query.filter(
                Auth.email == new_email,
                Auth.id != auth.id
            ).first()
            if existing_auth:
                return jsonify({"error": "Email already exists"}), 400
            
            if auth.email != new_email:
                auth.email = new_email
                updated_fields.append('email')
        
        # If no fields were updated
        if not updated_fields:
            return jsonify({"message": "No changes detected"}), 200
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            "message": "Profile updated successfully",
            "updated_fields": updated_fields,
            "user": user.to_dict(include_sensitive=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update profile", "details": str(e)}), 500


@profile_bp.route("/profile/change-password", methods=["PUT"])
@jwt_required()
def change_password():
    """Change user's password"""
    try:
        data = request.get_json(force=True)
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # Validation
        if not all([current_password, new_password, confirm_password]):
            return jsonify({"error": "Current password, new password, and confirmation are required"}), 400
        
        if new_password != confirm_password:
            return jsonify({"error": "New password and confirmation do not match"}), 400
        
        if len(new_password) < 8:
            return jsonify({"error": "New password must be at least 8 characters long"}), 400
        
        # Get user_id from JWT token
        current_user_id = get_jwt_identity()
        
        # Find auth record by user_id
        auth = Auth.query.filter_by(user_id=current_user_id).first()
        if not auth:
            return jsonify({"error": "User not found"}), 404
        
        # Verify current password
        if not auth.check_password(current_password):
            return jsonify({"error": "Current password is incorrect"}), 400
        
        # Update password
        auth.set_password(new_password)
        db.session.commit()
        
        return jsonify({"message": "Password changed successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to change password", "details": str(e)}), 500


@profile_bp.route("/profile/delete", methods=["DELETE"])
@jwt_required()
def delete_profile():
    """Delete user's account (with password confirmation)"""
    try:
        data = request.get_json(force=True)
        password = data.get('password')
        confirmation = data.get('confirmation')
        
        # Require explicit confirmation
        if confirmation != "DELETE_MY_ACCOUNT":
            return jsonify({"error": "Account deletion requires confirmation: 'DELETE_MY_ACCOUNT'"}), 400
        
        if not password:
            return jsonify({"error": "Password is required to delete account"}), 400
        
        # Get user_id from JWT token
        current_user_id = get_jwt_identity()
        
        # Find auth record by user_id
        auth = Auth.query.filter_by(user_id=current_user_id).first()
        if not auth:
            return jsonify({"error": "User not found"}), 404
            
        user = User.query.filter_by(auth_id=auth.id).first()
        if not user:
            return jsonify({"error": "User profile not found"}), 404
        
        # Verify password
        if not auth.check_password(password):
            return jsonify({"error": "Incorrect password"}), 400
        
        # Delete user and auth (this will cascade delete related trips due to foreign key)
        db.session.delete(user)
        db.session.delete(auth)
        db.session.commit()
        
        return jsonify({"message": "Account deleted successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete account", "details": str(e)}), 500