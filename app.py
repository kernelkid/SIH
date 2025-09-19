from flask import Flask
from flask_jwt_extended import JWTManager
from routes.auth_routes import auth_bp
from config import Config
from routes.consent_routes import consent_bp
from routes.trip_routes import trip_bp
from routes.admin_routes import admin_bp
from routes.admin_signup_routes import admin_signup_bp
from routes.profile_routes import profile_bp
from routes.tracking import tracking_bp
from flask import Flask, render_template
from init_db import init_db
from datetime import timedelta

app = Flask(__name__)
app.config.from_object(Config)  # load configs
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)
jwt = JWTManager(app)

# Initialize database
init_db(app)

# Register routes
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(consent_bp, url_prefix="/user")
app.register_blueprint(trip_bp, url_prefix="/")
app.register_blueprint(admin_bp, url_prefix="/admin")
app.register_blueprint(admin_signup_bp, url_prefix="/")
app.register_blueprint(profile_bp, url_prefix="/")

if __name__ == "__main__":
    app.run(debug=True)