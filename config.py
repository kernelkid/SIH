import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-secret-key")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
    SECRET_KEY = os.environ.get("SECRET_KEY") or "super-secret-key"
    ADMIN_CREATION_KEY = os.getenv("ADMIN_CREATION_KEY")
    
    # Neon Database Configuration
    SQLALCHEMY_DATABASE_URI = "postgresql://neondb_owner:npg_wWImVFB4l9cG@ep-damp-cloud-a1x41e4u-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    SQLALCHEMY_TRACK_MODIFICATIONS = False