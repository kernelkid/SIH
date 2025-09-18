from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user_model import users

consent_bp = Blueprint("consent", __name__)

# ✅ Get user consent
@consent_bp.route("/consent", methods=["GET"])
@jwt_required()
def get_consent():
    current_user_email = get_jwt_identity()
    user = next((u for u in users if u.email == current_user_email), None)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.consent)

# ✅ Update user consent
@consent_bp.route("/consent", methods=["POST"])
@jwt_required()
def update_consent():
    current_user_email = get_jwt_identity()
    user = next((u for u in users if u.email == current_user_email), None)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.json
    gps = data.get("gps")
    notifications = data.get("notifications")
    motion_activity = data.get("motion_activity")

    # Update consent only if provided
    if gps is not None:
        user.consent["gps"] = bool(gps)
    if notifications is not None:
        user.consent["notifications"] = bool(notifications)
    if motion_activity is not None:
        user.consent["motion_activity"] = bool(motion_activity)

    return jsonify({"message": "Consent updated successfully", "consent": user.consent})
