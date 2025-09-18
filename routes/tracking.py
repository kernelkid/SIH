# routes/tracking.py - Clean API Routes Only
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user_model import User
from models.consent_model import Consent
from services.tracking_service import TrackingService
from services.activity_classifier import ActivityClassifier

tracking_bp = Blueprint("tracking", __name__)

@tracking_bp.route("/location", methods=["POST"])
@jwt_required()
def save_location():
    """Save user location data"""
    try:
        # Get authenticated user
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Check GPS consent
        if not TrackingService.check_gps_consent(user.id):
            return jsonify({"error": "GPS consent not granted"}), 403
        
        # Validate request data
        data = request.get_json()
        if not data or not data.get('latitude') or not data.get('longitude'):
            return jsonify({"error": "Invalid location data"}), 400
        
        # Save location using service
        location = TrackingService.save_location_data(user.id, data)
        
        return jsonify({
            "message": "Location saved",
            "location": location.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({"error": "Failed to save location", "details": str(e)}), 500

@tracking_bp.route("/motion", methods=["POST"])
@jwt_required()
def save_motion():
    """Save user motion data with activity classification"""
    try:
        # Get authenticated user
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Check motion consent
        if not TrackingService.check_motion_consent(user.id):
            return jsonify({"error": "Motion consent not granted"}), 403
        
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No motion data provided"}), 400
        
        # Classify activity
        activity_type, confidence = ActivityClassifier.classify_activity(data)
        
        # Save motion data using service
        motion = TrackingService.save_motion_data(user.id, data, activity_type, confidence)
        
        return jsonify({
            "message": "Motion data saved",
            "motion": motion.to_dict(),
            "detected_activity": {
                "type": activity_type,
                "confidence": confidence
            }
        }), 201
        
    except Exception as e:
        return jsonify({"error": "Failed to save motion data", "details": str(e)}), 500

@tracking_bp.route("/batch", methods=["POST"])
@jwt_required()
def save_batch_data():
    """Save both location and motion data in a single request"""
    try:
        # Get authenticated user
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Process batch data using service
        result = TrackingService.process_batch_data(user.id, data)
        
        return jsonify({
            "message": "Batch data processed",
            "result": result
        }), 201
        
    except Exception as e:
        return jsonify({"error": "Failed to process batch data", "details": str(e)}), 500

@tracking_bp.route("/history", methods=["GET"])
@jwt_required()
def get_tracking_history():
    """Get user's tracking history"""
    try:
        # Get authenticated user
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get query parameters
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 100, type=int)
        
        # Get history using service
        history = TrackingService.get_user_history(user.id, hours, limit)
        
        return jsonify(history), 200
        
    except Exception as e:
        return jsonify({"error": "Failed to fetch history", "details": str(e)}), 500

@tracking_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_tracking_stats():
    """Get user's tracking statistics"""
    try:
        # Get authenticated user
        current_user_email = get_jwt_identity()
        user = User.query.filter_by(email=current_user_email).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Get stats using service
        stats = TrackingService.get_user_stats(user.id)
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({"error": "Failed to fetch stats", "details": str(e)}), 500