from models.user_model import User
from models.trip_model import Trip
from models.consent_model import Consent
from models.location_model import LocationData, MotionData
from init_db import db
import logging

logger = logging.getLogger(__name__)

class AdminService:
    @staticmethod
    def delete_user_cascade_by_id(user_database_id):
        """Delete user by integer database ID and all associated data"""
        try:
            user = User.query.get(user_database_id)  # Use integer ID
            if not user:
               return None

            
            # Get counts before deletion for confirmation
            trips_count = Trip.query.filter_by(user_id=user_database_id).count()
            locations_count = LocationData.query.filter_by(user_id=user_database_id).count()
            motions_count = MotionData.query.filter_by(user_id=user_database_id).count()
            consents_count = Consent.query.filter_by(user_id=user_database_id).count()
            
             # Delete cascade (same as before)
            MotionData.query.filter_by(user_id=user_database_id).delete()
            LocationData.query.filter_by(user_id=user_database_id).delete()
            Trip.query.filter_by(user_id=user_database_id).delete()
            Consent.query.filter_by(user_id=user_database_id).delete()
        
            user_email = user.email
            db.session.delete(user)
            db.session.commit()
            
            return {
            "user_email": user_email,
            "deleted_stats": {
                "trips": trips_count,
                "locations": locations_count,
                "motions": motions_count,
                "consents": consents_count
            }
        }
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete user ID {user_database_id}: {e}")
            raise

    @staticmethod
    def bulk_delete_users(user_ids):
        """Delete multiple users and all their associated data"""
        try:
            deleted_users = []
            failed_users = []
            total_stats = {
                "trips": 0,
                "locations": 0,
                "motions": 0,
                "consents": 0
            }
            
            for user_id in user_ids:
                try:
                    user = User.query.filter_by(user_id=user_id).first()
                    if not user:
                        failed_users.append({"user_id": user_id, "reason": "User not found"})
                        continue
                    
                    # Get counts before deletion
                    trips_count = Trip.query.filter_by(user_id=user.id).count()
                    locations_count = LocationData.query.filter_by(user_id=user.id).count()
                    motions_count = MotionData.query.filter_by(user_id=user.id).count()
                    consents_count = Consent.query.filter_by(user_id=user.id).count()
                    
                    # Delete associated data
                    MotionData.query.filter_by(user_id=user.id).delete()
                    LocationData.query.filter_by(user_id=user.id).delete()
                    Trip.query.filter_by(user_id=user.id).delete()
                    Consent.query.filter_by(user_id=user.id).delete()
                    
                    # Store user email before deletion
                    user_email = user.email
                    
                    # Delete the user
                    db.session.delete(user)
                    
                    deleted_users.append({
                        "user_id": user_id,
                        "email": user_email,
                        "deleted_data": {
                            "trips": trips_count,
                            "locations": locations_count,
                            "motions": motions_count,
                            "consents": consents_count
                        }
                    })
                    
                    # Update totals
                    total_stats["trips"] += trips_count
                    total_stats["locations"] += locations_count
                    total_stats["motions"] += motions_count
                    total_stats["consents"] += consents_count
                    
                except Exception as e:
                    failed_users.append({"user_id": user_id, "reason": str(e)})
            
            # Commit all changes at once
            db.session.commit()
            
            return {
                "deleted_count": len(deleted_users),
                "failed_count": len(failed_users),
                "deleted_users": deleted_users,
                "failed_users": failed_users,
                "total_deleted_data": total_stats
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Bulk delete failed: {e}")
            raise

    @staticmethod  
    def get_database_statistics():
        """Get comprehensive database statistics"""
        try:
            # Basic counts
            total_users = User.query.count()
            total_trips = Trip.query.count()
            total_locations = LocationData.query.count()
            total_motions = MotionData.query.count()
            total_consents = Consent.query.count()
            
            # Users with data
            users_with_trips = db.session.query(User.id).join(Trip).distinct().count()
            users_with_consent = db.session.query(User.id).join(Consent).distinct().count()
            users_with_locations = db.session.query(User.id).join(LocationData).distinct().count()
            
            # Trip mode breakdown
            trip_modes_query = db.session.query(
                Trip.mode_of_travel,
                db.func.count(Trip.id).label('count')
            ).group_by(Trip.mode_of_travel).all()
            
            trip_modes = {}
            for mode, count in trip_modes_query:
                trip_modes[mode] = count
            
            # Location data quality
            resolved_addresses = LocationData.query.filter_by(address_resolved=True).count()
            failed_geocoding = LocationData.query.filter_by(geocoding_failed=True).count()
            
            # Consent statistics
            gps_enabled = Consent.query.filter_by(gps=True).count()
            motion_enabled = Consent.query.filter_by(motion_activity=True).count()
            notifications_enabled = Consent.query.filter_by(notifications=True).count()
            
            # Activity type breakdown (from motion data)
            activity_types_query = db.session.query(
                MotionData.activity_type,
                db.func.count(MotionData.id).label('count')
            ).filter(
                MotionData.activity_type.isnot(None)
            ).group_by(MotionData.activity_type).all()
            
            activity_breakdown = {}
            for activity, count in activity_types_query:
                activity_breakdown[activity] = count
            
            # Calculate percentages
            geocoding_success_rate = 0
            if total_locations > 0:
                geocoding_success_rate = round((resolved_addresses / total_locations) * 100, 2)
            
            consent_rates = {
                "gps_rate": round((gps_enabled / total_consents) * 100, 2) if total_consents > 0 else 0,
                "motion_rate": round((motion_enabled / total_consents) * 100, 2) if total_consents > 0 else 0,
                "notification_rate": round((notifications_enabled / total_consents) * 100, 2) if total_consents > 0 else 0
            }
            
            return {
                "users": {
                    "total": total_users,
                    "with_trips": users_with_trips,
                    "with_consent": users_with_consent,
                    "with_location_data": users_with_locations
                },
                "trips": {
                    "total": total_trips,
                    "by_mode": trip_modes,
                    "average_per_user": round(total_trips / total_users, 2) if total_users > 0 else 0
                },
                "tracking_data": {
                    "total_locations": total_locations,
                    "total_motions": total_motions,
                    "resolved_addresses": resolved_addresses,
                    "failed_geocoding": failed_geocoding,
                    "geocoding_success_rate": geocoding_success_rate,
                    "activity_breakdown": activity_breakdown
                },
                "consent": {
                    "total_records": total_consents,
                    "gps_enabled": gps_enabled,
                    "motion_enabled": motion_enabled,
                    "notifications_enabled": notifications_enabled,
                    "consent_rates": consent_rates
                },
                "data_quality": {
                    "users_without_trips": total_users - users_with_trips,
                    "users_without_consent": total_users - users_with_consent,
                    "locations_without_address": total_locations - resolved_addresses - failed_geocoding,
                    "geocoding_pending": total_locations - resolved_addresses - failed_geocoding
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get database statistics: {e}")
            raise