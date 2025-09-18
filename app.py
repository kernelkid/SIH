from flask import Flask
from flask_jwt_extended import JWTManager
from routes.auth_routes import auth_bp
from config import Config
from routes.consent_routes import consent_bp
from routes.trip_routes import trip_bp
from routes.admin_routes import admin_bp
from routes.admin_signup_routes import admin_signup_bp

app = Flask(__name__)
app.config.from_object(Config)  # load configs

jwt = JWTManager(app)

# Register routes
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(consent_bp, url_prefix="/user")
app.register_blueprint(trip_bp, url_prefix="/")
app.register_blueprint(admin_bp, url_prefix="/")
app.register_blueprint(admin_signup_bp, url_prefix="/")


if __name__ == "__main__":
    app.run(debug=True)
