from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from init_db import db
from models.user_model import User
from models.consent_model import Consent
from models.auth_model import Auth  # You'll need to import Auth model
from utils.auth_utils import admin_required
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
consent_bp = Blueprint("consent", __name__)

# GET consent (user's own consent)
@consent_bp.route("/consent", methods=["GET"])
@jwt_required()
def get_consent():
    try:
        current_user_id = get_jwt_identity()
        auth = Auth.query.filter_by(user_id=current_user_id).first()
        if not auth:
            return jsonify({"error": "Auth record not found"}), 404
            
        user = User.query.filter_by(auth_id=auth.id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        consent = Consent.query.filter_by(user_id=user.id).first()

        if not consent:
            # Return default consent structure if no record exists
            default_consent = {
                "gps": False,
                "notifications": False,
                "motion_activity": False,
                "ts": None
            }
            return jsonify({"consent": default_consent}), 200

        return jsonify({"consent": consent.to_dict()}), 200

    except Exception as e:
        return jsonify({"error": "Failed to fetch consent", "details": str(e)}), 500


# POST consent update (user updates their own consent)
@consent_bp.route("/consent", methods=["POST"])
@jwt_required()
def update_consent():
    try:
        current_user_id = get_jwt_identity()
        print(f"DEBUG: JWT contains: '{current_user_id}' (type: {type(current_user_id)})")
        
        # Find auth record by user_id
        auth = Auth.query.filter_by(user_id=current_user_id).first()
        print(f"DEBUG: Found auth record: {auth}")
        
        if not auth:
            return jsonify({"error": "Auth record not found"}), 404
            
        user = User.query.filter_by(auth_id=auth.id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json(force=True) or {}

        # Validate that at least one consent field is provided
        consent_fields = ["gps", "notifications", "motion_activity"]
        if not any(field in data for field in consent_fields):
            return jsonify({"error": "At least one consent field must be provided"}), 400

        # Find existing or create new consent
        consent = Consent.query.filter_by(user_id=user.id).first()
        if not consent:
            consent = Consent(user_id=user.id)
            db.session.add(consent)

        # Update only provided fields
        if "gps" in data:
            consent.gps = bool(data["gps"])
        if "notifications" in data:
            consent.notifications = bool(data["notifications"])
        if "motion_activity" in data:
            consent.motion_activity = bool(data["motion_activity"])

        consent.ts = datetime.utcnow()

        db.session.commit()

        logger.info(f"Consent updated for user {user.user_id}: GPS={consent.gps}, Notifications={consent.notifications}, Motion={consent.motion_activity}")

        return jsonify({
            "message": "Consent updated successfully", 
            "consent": consent.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update consent", "details": str(e)}), 500