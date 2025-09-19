"""
Authentication and authorization decorators for Flask routes
"""

from functools import wraps
from flask import session, jsonify, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from models.user_model import User  # Adjust import path based on your structure


def login_required(f):
    """
    Decorator to require user login for routes (Session-based).
    Checks for user_id in session and loads user into g.current_user
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if 'user_id' not in session:
            return jsonify({
                "error": "Authentication required", 
                "message": "Please log in to access this resource"
            }), 401
        
        # Load current user and store in g for easy access
        user = User.query.filter_by(user_id=session['user_id']).first()
        if not user:
            # User exists in session but not in database (deleted account, etc.)
            session.clear()
            return jsonify({
                "error": "Invalid session", 
                "message": "Please log in again"
            }), 401
        
        # Store user in Flask's g object for access in route functions
        g.current_user = user
        
        return f(*args, **kwargs)
    return decorated_function


def jwt_auth_required(f):
    """
    Custom JWT decorator that loads user into g.current_user
    Alternative to using @jwt_required() directly
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Verify JWT token
            verify_jwt_in_request()
            
            # Get user ID from JWT token
            current_user_id = get_jwt_identity()
            
            # Load current user
            user = User.query.filter_by(user_id=current_user_id).first()
            if not user:
                return jsonify({
                    "error": "User not found", 
                    "message": "Invalid token or user deleted"
                }), 404
            
            # Store user in Flask's g object for access in route functions
            g.current_user = user
            
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({
                "error": "Authentication failed",
                "message": str(e)
            }), 401
            
    return decorated_function


def admin_required(f):
    """
    Decorator to require admin privileges.
    Must be used after @login_required or @jwt_auth_required
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'current_user'):
            return jsonify({"error": "Authentication required"}), 401
        
        # Assuming you have an is_admin field or role system
        if not getattr(g.current_user, 'is_admin', False):
            return jsonify({
                "error": "Admin access required",
                "message": "You don't have permission to access this resource"
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function


def token_required(f):
    """
    Alternative decorator for API token-based authentication (Custom tokens)
    Looks for Authorization header with Bearer token
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        
        # Check for Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({"error": "Invalid token format"}), 401
        
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        
        try:
            # Here you would decode/validate your token
            # This is a simplified example - implement based on your token system
            # For JWT: jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            
            # For now, assuming token contains user_id
            # Replace this with your actual token validation logic
            user = User.query.filter_by(user_id=token).first()  # Simplified example
            if not user:
                return jsonify({"error": "Invalid token"}), 401
            
            g.current_user = user
            
        except Exception as e:
            return jsonify({"error": "Invalid token", "details": str(e)}), 401
        
        return f(*args, **kwargs)
    return decorated_function


def optional_auth(f):
    """
    Decorator that loads user if authenticated but doesn't require authentication.
    Supports both session and JWT authentication.
    Useful for routes that behave differently for logged-in vs anonymous users.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.current_user = None
        
        # Try JWT first
        try:
            verify_jwt_in_request(optional=True)
            current_user_id = get_jwt_identity()
            if current_user_id:
                user = User.query.filter_by(user_id=current_user_id).first()
                if user:
                    g.current_user = user
                    return f(*args, **kwargs)
        except:
            pass  # JWT failed, try session
        
        # Fallback to session-based auth
        if 'user_id' in session:
            user = User.query.filter_by(user_id=session['user_id']).first()
            if user:
                g.current_user = user
        
        return f(*args, **kwargs)
    return decorated_function


def rate_limit(max_requests=100, window=3600):
    """
    Basic rate limiting decorator (per user session)
    max_requests: maximum number of requests
    window: time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # This is a simplified rate limiter
            # In production, use Redis or similar for distributed rate limiting
            
            # For now, just continue - implement based on your needs
            # You could use Flask-Limiter for more robust rate limiting
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator