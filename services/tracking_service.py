# services/tracking_service.py - Updated with geocoding
from models.location_model import LocationData, MotionData
from models.consent_model import Consent
from services.geocoding_service import GeocodingService
from init_db import db
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict, List
import os

logger = logging.getLogger(__name__)

class TrackingService:
    """Service for handling location and motion tracking with address resolution"""
    
    def __init__(self):
        # Initialize geocoding service
        geocoding_provider = os.getenv('GEOCODING_PROVIDER', 'nominatim')  # free by default
        self.geocoder = GeocodingService(geocoding_provider)
        
        # API keys from environment variables
        self.google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        self.mapbox_api_key = os.getenv('MAPBOX_API_KEY')
    
    @staticmethod
    def check_gps_consent(user_id: int) -> bool:
        """Check if user has granted GPS consent"""
        consent = Consent.query.filter_by(user_id=user_id).first()
        return consent and consent.gps
    
    @staticmethod
    def check_motion_consent(user_id: int) -> bool:
        """Check if user has granted motion consent"""
        consent = Consent.query.filter_by(user_id=user_id).first()
        return consent and consent.motion_activity
    
    def save_location_data(self, user_id: int, location_data: dict, resolve_address: bool = True) -> LocationData:
        """
        Save location data to database with optional address resolution
        
        Args:
            user_id: User ID
            location_data: Location data from frontend
            resolve_address: Whether to resolve GPS coordinates to address
        """
        try:
            location = LocationData(
                user_id=user_id,
                latitude=location_data.get('latitude'),
                longitude=location_data.get('longitude'),
                accuracy=location_data.get('accuracy'),
                altitude=location_data.get('altitude'),
                altitude_accuracy=location_data.get('altitudeAccuracy'),
                heading=location_data.get('heading'),
                speed=location_data.get('speed')
            )
            
            db.session.add(location)
            db.session.flush()  # Get the ID without committing
            
            # Resolve address if requested
            if resolve_address:
                self._resolve_location_address(location)
            
            db.session.commit()
            
            logger.info(f"Location saved for user {user_id}: {location.latitude}, {location.longitude}")
            return location
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save location data: {e}")
            raise
    
    def _resolve_location_address(self, location: LocationData) -> None:
        """
        Resolve GPS coordinates to address and update the location record
        """
        try:
            # Get geocoding kwargs based on provider
            kwargs = {}
            if self.geocoder.provider == 'google' and self.google_api_key:
                kwargs['google_api_key'] = self.google_api_key
            elif self.geocoder.provider == 'mapbox' and self.mapbox_api_key:
                kwargs['mapbox_api_key'] = self.mapbox_api_key
            
            # Resolve address
            address_data = self.geocoder.reverse_geocode(
                location.latitude, 
                location.longitude,
                **kwargs
            )
            
            if address_data:
                # Update location with address information
                location.full_address = address_data.get('full_address')
                location.formatted_address = address_data.get('formatted_address')
                location.street_number = address_data.get('street_number')
                location.street_name = address_data.get('street_name')
                location.neighborhood = address_data.get('neighborhood')
                location.city = address_data.get('city')
                location.state = address_data.get('state')
                location.postal_code = address_data.get('postal_code')
                location.country = address_data.get('country')
                location.country_code = address_data.get('country_code')
                location.address_resolved = True
                location.address_updated_at = datetime.utcnow()
                
                logger.info(f"Address resolved: {location.formatted_address}")
            else:
                location.geocoding_failed = True
                logger.warning(f"Failed to resolve address for {location.latitude}, {location.longitude}")
                
        except Exception as e:
            location.geocoding_failed = True
            logger.error(f"Error resolving address: {e}")
    
    def save_motion_data(self, user_id: int, motion_data: dict, activity_type: str, confidence: float, location_id: Optional[int] = None) -> MotionData:
        """
        Save motion data to database
        """
        try:
            motion = MotionData(
                user_id=user_id,
                acceleration_x=motion_data.get('acceleration', {}).get('x'),
                acceleration_y=motion_data.get('acceleration', {}).get('y'),
                acceleration_z=motion_data.get('acceleration', {}).get('z'),
                acceleration_including_gravity_x=motion_data.get('accelerationIncludingGravity', {}).get('x'),
                acceleration_including_gravity_y=motion_data.get('accelerationIncludingGravity', {}).get('y'),
                acceleration_including_gravity_z=motion_data.get('accelerationIncludingGravity', {}).get('z'),
                rotation_rate_alpha=motion_data.get('rotationRate', {}).get('alpha'),
                rotation_rate_beta=motion_data.get('rotationRate', {}).get('beta'),
                rotation_rate_gamma=motion_data.get('rotationRate', {}).get('gamma'),
                orientation_alpha=motion_data.get('orientation', {}).get('alpha'),
                orientation_beta=motion_data.get('orientation', {}).get('beta'),
                orientation_gamma=motion_data.get('orientation', {}).get('gamma'),
                activity_type=activity_type,
                confidence=confidence,
                location_id=location_id
            )
            
            db.session.add(motion)
            db.session.commit()
            
            logger.info(f"Motion data saved for user {user_id}: {activity_type} ({confidence:.2f})")
            return motion
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to save motion data: {e}")
            raise
    
    def process_batch_data(self, user_id: int, batch_data: dict) -> dict:
        """
        Process batch data (location + motion) in a single transaction
        """
        try:
            result = {}
            location_obj = None
            
            # Process location data first
            if batch_data.get('location') and self.check_gps_consent(user_id):
                location_obj = self.save_location_data(user_id, batch_data['location'])
                result['location'] = {
                    'saved': True,
                    'id': location_obj.id,
                    'address': location_obj.get_simple_address()
                }
            
            # Process motion data
            if batch_data.get('motion') and self.check_motion_consent(user_id):
                from services.activity_classifier import ActivityClassifier
                
                motion_data = batch_data['motion']
                activity_type, confidence = ActivityClassifier.classify_activity(
                    motion_data, 
                    batch_data.get('location')
                )
                
                motion_obj = self.save_motion_data(
                    user_id, 
                    motion_data, 
                    activity_type, 
                    confidence,
                    location_obj.id if location_obj else None
                )
                
                result['motion'] = {
                    'saved': True,
                    'id': motion_obj.id,
                    'activity': {
                        'type': activity_type,
                        'confidence': confidence
                    }
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process batch data: {e}")
            raise
    
    def get_user_history(self, user_id: int, hours: int = 24, limit: int = 100) -> dict:
        """
        Get user's tracking history with addresses
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Get recent location data with addresses
            locations = LocationData.query.filter(
                LocationData.user_id == user_id,
                LocationData.timestamp >= cutoff_time
            ).order_by(LocationData.timestamp.desc()).limit(limit).all()
            
            # Get recent motion data
            motions = MotionData.query.filter(
                MotionData.user_id == user_id,
                MotionData.timestamp >= cutoff_time
            ).order_by(MotionData.timestamp.desc()).limit(limit).all()
            
            return {
                'locations': [loc.to_dict() for loc in locations],
                'motions': [motion.to_dict() for motion in motions],
                'summary': {
                    'total_locations': len(locations),
                    'total_motions': len(motions),
                    'locations_with_address': sum(1 for loc in locations if loc.address_resolved),
                    'time_range_hours': hours
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get user history: {e}")
            raise
    
    def get_user_stats(self, user_id: int) -> dict:
        """
        Get user's tracking statistics
        """
        try:
            # Overall stats
            total_locations = LocationData.query.filter_by(user_id=user_id).count()
            total_motions = MotionData.query.filter_by(user_id=user_id).count()
            
            # Today's stats
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_locations = LocationData.query.filter(
                LocationData.user_id == user_id,
                LocationData.timestamp >= today_start
            ).count()
            
            # Activity breakdown (last 7 days)
            week_start = datetime.utcnow() - timedelta(days=7)
            activity_stats = db.session.query(
                MotionData.activity_type,
                db.func.count(MotionData.id).label('count')
            ).filter(
                MotionData.user_id == user_id,
                MotionData.timestamp >= week_start
            ).group_by(MotionData.activity_type).all()
            
            # Address resolution stats
            resolved_addresses = LocationData.query.filter(
                LocationData.user_id == user_id,
                LocationData.address_resolved == True
            ).count()
            
            failed_addresses = LocationData.query.filter(
                LocationData.user_id == user_id,
                LocationData.geocoding_failed == True
            ).count()
            
            # Most recent activity
            latest_location = LocationData.query.filter_by(user_id=user_id).order_by(
                LocationData.timestamp.desc()
            ).first()
            
            latest_motion = MotionData.query.filter_by(user_id=user_id).order_by(
                MotionData.timestamp.desc()
            ).first()
            
            return {
                'overall': {
                    'total_locations': total_locations,
                    'total_motions': total_motions,
                    'locations_today': today_locations
                },
                'geocoding': {
                    'resolved_addresses': resolved_addresses,
                    'failed_addresses': failed_addresses,
                    'resolution_rate': round(resolved_addresses / total_locations * 100, 2) if total_locations > 0 else 0
                },
                'activity_breakdown': {
                    activity: count for activity, count in activity_stats
                },
                'latest_activity': {
                    'last_location': {
                        'timestamp': latest_location.timestamp.isoformat() if latest_location else None,
                        'address': latest_location.get_simple_address() if latest_location else None
                    },
                    'last_motion': {
                        'timestamp': latest_motion.timestamp.isoformat() if latest_motion else None,
                        'activity_type': latest_motion.activity_type if latest_motion else None,
                        'confidence': latest_motion.confidence if latest_motion else None
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get user stats: {e}")
            raise
    
    def cleanup_old_data(self, days: int = 30) -> dict:
        """
        Clean up old tracking data older than specified days
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            
            # Delete old location data
            deleted_locations = LocationData.query.filter(
                LocationData.timestamp < cutoff_time
            ).delete()
            
            # Delete old motion data
            deleted_motions = MotionData.query.filter(
                MotionData.timestamp < cutoff_time
            ).delete()
            
            db.session.commit()
            
            logger.info(f"Cleanup completed: {deleted_locations} locations, {deleted_motions} motions deleted")
            
            return {
                'deleted_locations': deleted_locations,
                'deleted_motions': deleted_motions,
                'cutoff_date': cutoff_time.isoformat()
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to cleanup old data: {e}")
            raise
    
    def get_location_timeline(self, user_id: int, date: datetime = None) -> List[dict]:
        """
        Get timeline of locations for a specific date
        """
        try:
            if not date:
                date = datetime.utcnow()
            
            # Get start and end of the day
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            locations = LocationData.query.filter(
                LocationData.user_id == user_id,
                LocationData.timestamp >= start_of_day,
                LocationData.timestamp < end_of_day
            ).order_by(LocationData.timestamp.asc()).all()
            
            timeline = []
            for loc in locations:
                timeline.append({
                    'timestamp': loc.timestamp.isoformat(),
                    'latitude': loc.latitude,
                    'longitude': loc.longitude,
                    'address': loc.get_simple_address(),
                    'accuracy': loc.accuracy
                })
            
            return timeline
            
        except Exception as e:
            logger.error(f"Failed to get location timeline: {e}")
            raise
    
    def get_distance_traveled(self, user_id: int, date: datetime = None) -> float:
        """
        Calculate total distance traveled for a specific date using Haversine formula
        """
        try:
            timeline = self.get_location_timeline(user_id, date)
            
            if len(timeline) < 2:
                return 0.0
            
            total_distance = 0.0
            
            for i in range(1, len(timeline)):
                prev_loc = timeline[i-1]
                curr_loc = timeline[i]
                
                distance = self._haversine_distance(
                    prev_loc['latitude'], prev_loc['longitude'],
                    curr_loc['latitude'], curr_loc['longitude']
                )
                total_distance += distance
            
            return round(total_distance, 2)
            
        except Exception as e:
            logger.error(f"Failed to calculate distance traveled: {e}")
            raise
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on the earth in kilometers
        """
        import math
        
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r
    
    def get_frequent_locations(self, user_id: int, days: int = 30, min_visits: int = 3) -> List[dict]:
        """
        Get frequently visited locations based on clustering nearby coordinates
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            
            locations = LocationData.query.filter(
                LocationData.user_id == user_id,
                LocationData.timestamp >= cutoff_time,
                LocationData.address_resolved == True
            ).all()
            
            if not locations:
                return []
            
            # Simple clustering by address similarity
            location_clusters = {}
            
            for loc in locations:
                # Use city + neighborhood as cluster key
                cluster_key = f"{loc.city or 'Unknown'}, {loc.neighborhood or loc.state or 'Unknown'}"
                
                if cluster_key not in location_clusters:
                    location_clusters[cluster_key] = {
                        'visits': 0,
                        'addresses': [],
                        'coordinates': [],
                        'first_visit': loc.timestamp,
                        'last_visit': loc.timestamp
                    }
                
                cluster = location_clusters[cluster_key]
                cluster['visits'] += 1
                cluster['addresses'].append(loc.formatted_address or loc.full_address)
                cluster['coordinates'].append((loc.latitude, loc.longitude))
                
                if loc.timestamp < cluster['first_visit']:
                    cluster['first_visit'] = loc.timestamp
                if loc.timestamp > cluster['last_visit']:
                    cluster['last_visit'] = loc.timestamp
            
            # Filter by minimum visits and format results
            frequent_locations = []
            for cluster_key, cluster in location_clusters.items():
                if cluster['visits'] >= min_visits:
                    # Get most common address
                    from collections import Counter
                    most_common_address = Counter(cluster['addresses']).most_common(1)[0][0]
                    
                    # Calculate center coordinates
                    avg_lat = sum(coord[0] for coord in cluster['coordinates']) / len(cluster['coordinates'])
                    avg_lon = sum(coord[1] for coord in cluster['coordinates']) / len(cluster['coordinates'])
                    
                    frequent_locations.append({
                        'location': cluster_key,
                        'address': most_common_address,
                        'visits': cluster['visits'],
                        'latitude': avg_lat,
                        'longitude': avg_lon,
                        'first_visit': cluster['first_visit'].isoformat(),
                        'last_visit': cluster['last_visit'].isoformat()
                    })
            
            # Sort by visit count
            frequent_locations.sort(key=lambda x: x['visits'], reverse=True)
            
            return frequent_locations
            
        except Exception as e:
            logger.error(f"Failed to get frequent locations: {e}")
            raise
    
    def retry_failed_geocoding(self, user_id: int = None, limit: int = 100) -> dict:
        """
        Retry geocoding for failed addresses
        """
        try:
            query = LocationData.query.filter(
                LocationData.geocoding_failed == True,
                LocationData.address_resolved == False
            )
            
            if user_id:
                query = query.filter(LocationData.user_id == user_id)
            
            failed_locations = query.limit(limit).all()
            
            success_count = 0
            still_failed = 0
            
            for location in failed_locations:
                # Reset failure flag and try again
                location.geocoding_failed = False
                self._resolve_location_address(location)
                
                if location.address_resolved:
                    success_count += 1
                else:
                    still_failed += 1
            
            db.session.commit()
            
            logger.info(f"Geocoding retry: {success_count} succeeded, {still_failed} still failed")
            
            return {
                'processed': len(failed_locations),
                'successful': success_count,
                'still_failed': still_failed
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to retry geocoding: {e}")
            raise