# auth_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.auth_model import Auth
from models.user_model import User
from init_db import db
import re

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json(force=True)
        
        # Extract required fields
        email = data.get("email")
        password = data.get("password")

        # Basic validation
        if not email or not password:
            return jsonify({
                "error": "Email and password are required"
            }), 400

        # Email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({"error": "Invalid email format"}), 400
        
        # Password strength validation
        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters long"}), 400

        # Check if user already exists
        existing_auth = Auth.query.filter_by(email=email.lower().strip()).first()
        if existing_auth:
            return jsonify({"error": "User with this email already exists"}), 400
        
        # Create new auth record first
        new_auth = Auth(email=email, password=password)
        db.session.add(new_auth)
        db.session.flush()  # Get the ID
        
        # Create new user record with auth_id
        new_user = User(auth_id=new_auth.id)
        
        db.session.add(new_user)
        db.session.commit()

        return jsonify({
            "message": "User created successfully",
            "user": new_user.to_dict()
        }), 201

    except ValueError as ve:
        db.session.rollback()
        return jsonify({"error": "Validation error", "details": str(ve)}), 400
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Something went wrong", "details": str(e)}), 500

@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json(force=True)
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Fetch auth record from DB
        auth = Auth.query.filter_by(email=email.lower().strip()).first()
        if auth and auth.check_password(password):
            # Create token with user_id as identity
            access_token = create_access_token(identity=auth.user_id)
            return jsonify({
                "message": "Login successful",
                "access_token": access_token, 
                "user": auth.user.to_dict() if auth.user else auth.to_dict()
            }), 200

        return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        return jsonify({"error": "Something went wrong", "details": str(e)}), 500