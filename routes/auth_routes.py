from flask import Blueprint, request, jsonify, redirect
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.user_model import users, User
from config import Config
import requests
import google.auth.transport.requests
from google_auth_oauthlib.flow import Flow
import google.oauth2.id_token

auth_bp = Blueprint("auth", __name__)

# ✅ Signup
@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if any(u.email == email for u in users):
        return jsonify({"error": "User already exists"}), 400

    new_user = User(email=email, password=password)
    users.append(new_user)
    return jsonify({"message": "User created successfully"}), 201

# ✅ Login
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    user = next((u for u in users if u.email == email), None)
    if user and user.check_password(password):
        access_token = create_access_token(identity=email)
        return jsonify({"access_token": access_token}), 200
    return jsonify({"error": "Invalid credentials"}), 401

# ✅ Protected Profile
@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    current_user = get_jwt_identity()
    return jsonify({"message": f"Welcome {current_user}!"})

# ✅ Google OAuth
flow = Flow.from_client_config(
    {
        "web": {
            "client_id": Config.GOOGLE_CLIENT_ID,
            "client_secret": Config.GOOGLE_CLIENT_SECRET,
            "redirect_uris": [Config.GOOGLE_REDIRECT_URI],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    },
    scopes=["openid", "https://www.googleapis.com/auth/userinfo.email"],
    redirect_uri=Config.GOOGLE_REDIRECT_URI
)

@auth_bp.route("/google-login")
def google_login():
    auth_url, _ = flow.authorization_url(prompt="consent")
    return redirect(auth_url)

@auth_bp.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    credentials = flow.credentials
    token_request = google.auth.transport.requests.Request()
    id_info = google.oauth2.id_token.verify_oauth2_token(
        credentials._id_token, token_request, Config.GOOGLE_CLIENT_ID
    )

    email = id_info.get("email")
    user = next((u for u in users if u.email == email), None)
    if not user:
        user = User(email=email, google_id=id_info["sub"])
        users.append(user)

    access_token = create_access_token(identity=email)
    return jsonify({"access_token": access_token, "email": email})
