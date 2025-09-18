from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from config import Config

db = SQLAlchemy()

def init_db(app: Flask, force: bool = False):
    """
    Initialize the database with Flask app.
    
    Parameters:
    - app: Flask application instance
    - force: If True, drop all tables and recreate (useful for testing)
    """
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        print("Database initialized successfully!")


    # with app.app_context():
    #     db.drop_all()
    #     db.create_all()
    #     print("Database reset successfully!")

