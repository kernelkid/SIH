from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from init_db import db
from models.user_model import User
from models.consent_model import Consent
from datetime import datetime

consent_bp = Blueprint("consent", __name__)

# GET consent
@consent_bp.route("/consent", methods=["GET"])
@jwt_required()
def get_consent():
    try:
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()

        if not user:
            return jsonify({"error": "User not found"}), 404

        consent = Consent.query.filter_by(user_id=user.id).first()

        if not consent:
            return jsonify({"consent": {}}), 200  # no record yet

        return jsonify({"consent": consent.to_dict()}), 200

    except Exception as e:
        return jsonify({"error": "Failed to fetch consent", "details": str(e)}), 500


# POST consent update
@consent_bp.route("/consent", methods=["POST"])
@jwt_required()
def update_consent():
    try:
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()

        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json(force=True) or {}

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

        return jsonify({"message": "Consent updated", "consent": consent.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to update consent", "details": str(e)}), 500
