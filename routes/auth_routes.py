from flask import Blueprint, request, jsonify, redirect
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.user_model import User
from init_db import db

auth_bp = Blueprint("auth", __name__)

# ✅ Signup route
@auth_bp.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json(force=True)
        
        # Extract all required fields
        email = data.get("email")
        password = data.get("password")
        name = data.get("name")
        phone_number = data.get("phone_number")
        aadhaar_number = data.get("aadhaar_number")
        date_of_birth = data.get("date_of_birth")  # Expected format: "YYYY-MM-DD"
        gender = data.get("gender")
        age = data.get("age")

        # Basic validation - check if all required fields are present
        required_fields = {
            "email": email,
            "password": password,
            "name": name,
            "phone_number": phone_number,
            "aadhaar_number": aadhaar_number,
            "date_of_birth": date_of_birth,
            "gender": gender,
            "age": age
        }
        
        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            return jsonify({
                "error": "Missing required fields",
                "missing_fields": missing_fields
            }), 400

        # Additional validations
        
        # Email format validation (basic)
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({"error": "Invalid email format"}), 400
        
        # Phone number validation (basic - should be digits, 10-15 characters)
        if not phone_number.isdigit() or len(phone_number) < 10 or len(phone_number) > 15:
            return jsonify({"error": "Phone number must be 10-15 digits"}), 400
        
        # Aadhaar validation (handled in User model, but double-check here)
        if not (isinstance(aadhaar_number, str) and len(aadhaar_number) == 12 and aadhaar_number.isdigit()):
            return jsonify({"error": "Aadhaar number must be exactly 12 digits"}), 400
        
        # Date format validation
        from datetime import datetime
        try:
            datetime.strptime(date_of_birth, '%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Date of birth must be in YYYY-MM-DD format"}), 400
        
        # Gender validation
        if gender not in ['Male', 'Female', 'Other']:
            return jsonify({"error": "Gender must be 'Male', 'Female', or 'Other'"}), 400
        
        # Age validation
        try:
            age = int(age)
            if age < 0 or age > 150:
                raise ValueError()
        except (ValueError, TypeError):
            return jsonify({"error": "Age must be a valid integer between 0 and 150"}), 400
        
        # Password strength validation (optional - adjust as needed)
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters long"}), 400

        # Check if user already exists (by email or aadhaar)
        existing_user = User.query.filter(
            (User.email == email) | (User.aadhaar_number == aadhaar_number)
        ).first()
        
        if existing_user:
            if existing_user.email == email:
                return jsonify({"error": "User with this email already exists"}), 400
            else:
                return jsonify({"error": "User with this Aadhaar number already exists"}), 400

        # Create new user
        new_user = User(
            email=email,
            password=password,
            name=name,
            phone_number=phone_number,
            aadhaar_number=aadhaar_number,
            date_of_birth=date_of_birth,
            gender=gender,
            age=age
        )
        
        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            "message": "User created successfully",
            "user": new_user.to_dict()  # This won't include sensitive Aadhaar by default
        }), 201

    except ValueError as ve:
        db.session.rollback()
        return jsonify({"error": "Validation error", "details": str(ve)}), 400
    
    except Exception as e:
        db.session.rollback()  # rollback in case of DB error
        return jsonify({"error": "Something went wrong", "details": str(e)}), 500

# ✅ Login route
@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(force=True)
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Fetch user from DB
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            access_token = create_access_token(identity=user.email)
            return jsonify({"access_token": access_token, "user": user.to_dict()}), 200

        return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        return jsonify({"error": "Something went wrong", "details": str(e)}), 500