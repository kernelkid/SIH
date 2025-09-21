from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user_model import User
from models.auth_model import Auth  # Make sure to import your Auth model
from init_db import db
from datetime import datetime
import re


user_bp = Blueprint('user', __name__)

@user_bp.route("/setup", methods=["POST", "PUT"])
@jwt_required()
def setup_profile():
    """
    Complete or update user profile with all personal details
    POST: For first-time profile completion
    PUT: For updating existing profile
    """
    try:
        data = request.get_json(force=True)
        
        # Get current user
        current_user_id = get_jwt_identity()
        auth = Auth.query.filter_by(user_id=current_user_id).first()
        if not auth:
            return jsonify({"error": "Authentication failed", "message": "Invalid user"}), 401
        
        user = User.query.filter_by(auth_id=auth.id).first()
        if not user:
            return jsonify({"error": "User profile not found"}), 404
        
        # Validation errors collector
        errors = {}
        
        # Validate and process each field
        
        # 1. Name validation
        name = data.get('name', '').strip() if data.get('name') else None
        if name:
            if len(name) < 2:
                errors['name'] = "Name must be at least 2 characters long"
            elif len(name) > 100:
                errors['name'] = "Name cannot exceed 100 characters"
            elif not re.match(r'^[a-zA-Z\s\.]+$', name):
                errors['name'] = "Name can only contain letters, spaces, and dots"
        elif request.method == 'POST':  # Required for first-time completion
            errors['name'] = "Name is required for profile completion"
        
        # 2. Phone number validation
        phone_number = data.get('phone_number', '').strip() if data.get('phone_number') else None
        if phone_number:
            # Remove any non-digits for validation
            phone_digits = re.sub(r'\D', '', phone_number)
            if len(phone_digits) < 10 or len(phone_digits) > 15:
                errors['phone_number'] = "Phone number must be 10-15 digits"
            elif not phone_digits.isdigit():
                errors['phone_number'] = "Phone number must contain only digits"
            else:
                phone_number = phone_digits  # Store cleaned version
        
        # 3. Aadhaar number validation
        aadhaar_number = data.get('aadhaar_number', '').strip() if data.get('aadhaar_number') else None
        if aadhaar_number:
            aadhaar_digits = re.sub(r'\D', '', aadhaar_number)
            if len(aadhaar_digits) != 12:
                errors['aadhaar_number'] = "Aadhaar number must be exactly 12 digits"
            elif not aadhaar_digits.isdigit():
                errors['aadhaar_number'] = "Aadhaar number must contain only digits"
            else:
                # Check for duplicate Aadhaar (excluding current user)
                existing_aadhaar = User.query.filter(
                    User.aadhaar_number == aadhaar_digits,
                    User.id != user.id
                ).first()
                if existing_aadhaar:
                    errors['aadhaar_number'] = "This Aadhaar number is already registered"
                aadhaar_number = aadhaar_digits
        
        # 4. Date of birth validation
        date_of_birth = data.get('date_of_birth')
        parsed_dob = None
        if date_of_birth:
            try:
                parsed_dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                # Check if date is not in future
                if parsed_dob > datetime.now().date():
                    errors['date_of_birth'] = "Date of birth cannot be in the future"
                # Check reasonable age limits (e.g., not older than 120 years)
                age_years = (datetime.now().date() - parsed_dob).days // 365
                if age_years > 120:
                    errors['date_of_birth'] = "Invalid date of birth (too old)"
                elif age_years < 0:
                    errors['date_of_birth'] = "Invalid date of birth"
            except ValueError:
                errors['date_of_birth'] = "Date of birth must be in YYYY-MM-DD format"
        
        # 5. Gender validation
        gender = data.get('gender')
        if gender:
            valid_genders = ['Male', 'Female', 'Other']
            if gender not in valid_genders:
                errors['gender'] = f"Gender must be one of: {', '.join(valid_genders)}"
        
        # 6. Age validation
        age = data.get('age')
        if age is not None:
            try:
                age = int(age)
                if age < 0 or age > 150:
                    errors['age'] = "Age must be between 0 and 150"
                # Cross-validate with date of birth if both provided
                if parsed_dob:
                    calculated_age = (datetime.now().date() - parsed_dob).days // 365
                    if abs(calculated_age - age) > 1:  # Allow 1 year difference
                        errors['age'] = f"Age ({age}) doesn't match date of birth (calculated age: {calculated_age})"
            except (ValueError, TypeError):
                errors['age'] = "Age must be a valid number"
        elif parsed_dob:
            # Auto-calculate age from DOB if age not provided
            age = (datetime.now().date() - parsed_dob).days // 365
        
        # Return validation errors if any
        if errors:
            return jsonify({
                "error": "Validation failed",
                "validation_errors": errors,
                "message": "Please fix the validation errors and try again"
            }), 400
        
        # Track what fields are being updated
        updated_fields = []
        
        # Update user fields
        if name and user.name != name:
            user.name = name
            updated_fields.append('name')
        
        if phone_number and user.phone_number != phone_number:
            user.phone_number = phone_number
            updated_fields.append('phone_number')
        
        if aadhaar_number and user.aadhaar_number != aadhaar_number:
            user.aadhaar_number = aadhaar_number
            updated_fields.append('aadhaar_number')
        
        if parsed_dob and user.date_of_birth != parsed_dob:
            user.date_of_birth = parsed_dob
            updated_fields.append('date_of_birth')
        
        if gender and user.gender != gender:
            user.gender = gender
            updated_fields.append('gender')
        
        if age is not None and user.age != age:
            user.age = age
            updated_fields.append('age')
        
        # If no fields to update
        if not updated_fields:
            return jsonify({
                "message": "No changes detected",
                "user": user.to_dict(include_sensitive=True)
            }), 200
        
        # Save changes to database
        db.session.commit()
        
        # Check profile completion status
        profile_complete = all([
            user.name,
            user.phone_number,
            user.date_of_birth,
            user.gender
        ])
        
        return jsonify({
            "message": "Profile updated successfully",
            "updated_fields": updated_fields,
            "profile_complete": profile_complete,
            "user": user.to_dict(include_sensitive=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to update profile",
            "message": "An unexpected error occurred",
            "details": str(e)
        }), 500


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