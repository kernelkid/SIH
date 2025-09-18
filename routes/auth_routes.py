from flask import Blueprint, request, jsonify, redirect
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.user_model import User
from config import Config
import requests
import google.auth.transport.requests
from google_auth_oauthlib.flow import Flow
import google.oauth2.id_token
from init_db import db

auth_bp = Blueprint("auth", __name__)

# ✅ Signup route
@auth_bp.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json(force=True)
        email = data.get("email")
        password = data.get("password")

        # Basic validation
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return jsonify({"error": "User already exists"}), 400

        # Create new user
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "User created successfully", "user": new_user.to_dict()}), 201

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
            access_token = create_access_token(identity=user.user_id)
            return jsonify({"access_token": access_token, "user": user.to_dict()}), 200

        return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        return jsonify({"error": "Something went wrong", "details": str(e)}), 500