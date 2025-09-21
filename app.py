from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS # Import CORS
from datetime import timedelta

# Local module imports
from routes.auth_routes import auth_bp
from config import Config
from routes.consent_routes import consent_bp
from routes.trip_routes import trip_bp
from routes.admin_routes import admin_bp
from routes.admin_signup_routes import admin_signup_bp
from routes.profile_routes import profile_bp
from routes.user_routes import user_bp
from init_db import init_db

# --- App Initialization ---
app = Flask(__name__)

# --- Configuration ---
# Load configuration from the Config object (good for production)
# Ensure your Config class pulls sensitive data from environment variables
app.config.from_object(Config) 
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# --- Extensions ---
# Initialize JWT
jwt = JWTManager(app)

# Initialize CORS to allow requests from any origin.
# This is crucial for your React Native app to communicate with the API.
CORS(app)

# --- Database ---
# Initialize database
init_db(app)

# --- Blueprints / Routes ---
# Register all the application routes
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(consent_bp, url_prefix="/user")
app.register_blueprint(trip_bp, url_prefix="/")
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(admin_signup_bp, url_prefix="/")
app.register_blueprint(profile_bp, url_prefix="/")
app.register_blueprint(user_bp, url_prefix="/user")

# The entry point below is for running the app with the Flask development server.
# A production server like Gunicorn will directly use the 'app' object defined above.
if __name__ == "__main__":
  # Note: debug=True is not recommended for production.
  app.run(debug=True)
