from functools import wraps
from flask import jsonify, request

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Your existing admin check logic
            role = request.args.get("role", "user")
            if role != "admin":
                return jsonify({"error": "Admin access required"}), 403
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": "Authorization failed"}), 500
    return decorated_function