# services/geocoding_service.py
import requests
import time
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class GeocodingService:
    """Service for converting GPS coordinates to addresses (reverse geocoding)"""
    
    def __init__(self, provider='nominatim'):
        """
        Initialize geocoding service
        
        Args:
            provider: 'nominatim' (free), 'google' (requires API key), 'mapbox' (requires API key)
        """
        self.provider = provider
        self.cache = {}  # Simple in-memory cache
        self.last_request_time = 0
        self.rate_limit_delay = 1  # 1 second between requests for free APIs
        
    def _make_request_with_rate_limit(self, url: str, params: dict) -> Optional[dict]:
        """Make HTTP request with rate limiting"""
        try:
            # Rate limiting for free APIs
            if self.provider == 'nominatim':
                time_since_last = time.time() - self.last_request_time
                if time_since_last < self.rate_limit_delay:
                    time.sleep(self.rate_limit_delay - time_since_last)
            
            response = requests.get(url, params=params, timeout=10)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Geocoding API error: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Geocoding request failed: {e}")
            return None
    
    def _get_cache_key(self, lat: float, lon: float) -> str:
        """Generate cache key for coordinates (rounded to reduce cache size)"""
        return f"{round(lat, 4)},{round(lon, 4)}"
    
    def reverse_geocode_nominatim(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Reverse geocode using OpenStreetMap Nominatim (FREE)
        """
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json',
            'addressdetails': 1,
            'zoom': 18,
            'email': 'your-email@example.com'  # Required for Nominatim
        }
        
        headers = {
            'User-Agent': 'YourAppName/1.0'  # Required for Nominatim
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                
                if data and 'address' in data:
                    address_components = data['address']
                    
                    return {
                        'full_address': data.get('display_name', ''),
                        'street_number': address_components.get('house_number', ''),
                        'street_name': address_components.get('road', ''),
                        'neighborhood': address_components.get('neighbourhood', ''),
                        'city': address_components.get('city') or address_components.get('town') or address_components.get('village', ''),
                        'state': address_components.get('state', ''),
                        'postal_code': address_components.get('postcode', ''),
                        'country': address_components.get('country', ''),
                        'country_code': address_components.get('country_code', ''),
                        'formatted_address': self._format_address(address_components),
                        'raw_response': data
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Nominatim geocoding failed: {e}")
            return None
    
    def reverse_geocode_google(self, latitude: float, longitude: float, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Reverse geocode using Google Maps Geocoding API (PAID)
        Requires Google Maps API key
        """
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'latlng': f"{latitude},{longitude}",
            'key': api_key
        }
        
        data = self._make_request_with_rate_limit(url, params)
        
        if data and data.get('status') == 'OK' and data.get('results'):
            result = data['results'][0]
            components = {comp['types'][0]: comp for comp in result['address_components']}
            
            return {
                'full_address': result['formatted_address'],
                'street_number': components.get('street_number', {}).get('long_name', ''),
                'street_name': components.get('route', {}).get('long_name', ''),
                'neighborhood': components.get('neighborhood', {}).get('long_name', ''),
                'city': components.get('locality', {}).get('long_name', ''),
                'state': components.get('administrative_area_level_1', {}).get('long_name', ''),
                'postal_code': components.get('postal_code', {}).get('long_name', ''),
                'country': components.get('country', {}).get('long_name', ''),
                'country_code': components.get('country', {}).get('short_name', ''),
                'formatted_address': result['formatted_address'],
                'raw_response': result
            }
        
        return None
    
    def reverse_geocode_mapbox(self, latitude: float, longitude: float, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Reverse geocode using MapBox Geocoding API (PAID)
        Requires MapBox API key
        """
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{longitude},{latitude}.json"
        params = {
            'access_token': api_key,
            'types': 'address'
        }
        
        data = self._make_request_with_rate_limit(url, params)
        
        if data and data.get('features'):
            feature = data['features'][0]
            context = {item['id'].split('.')[0]: item['text'] for item in feature.get('context', [])}
            
            return {
                'full_address': feature.get('place_name', ''),
                'street_number': feature.get('address', ''),
                'street_name': feature.get('text', ''),
                'neighborhood': context.get('neighborhood', ''),
                'city': context.get('place', ''),
                'state': context.get('region', ''),
                'postal_code': context.get('postcode', ''),
                'country': context.get('country', ''),
                'country_code': '',  # MapBox doesn't provide this easily
                'formatted_address': feature.get('place_name', ''),
                'raw_response': feature
            }
        
        return None
    
    def _format_address(self, address_components: dict) -> str:
        """Format address components into a readable address"""
        parts = []
        
        # Add house number and road
        if address_components.get('house_number') and address_components.get('road'):
            parts.append(f"{address_components['house_number']} {address_components['road']}")
        elif address_components.get('road'):
            parts.append(address_components['road'])
        
        # Add city
        city = address_components.get('city') or address_components.get('town') or address_components.get('village')
        if city:
            parts.append(city)
        
        # Add state and postal code
        if address_components.get('state'):
            state_part = address_components['state']
            if address_components.get('postcode'):
                state_part += f" {address_components['postcode']}"
            parts.append(state_part)
        
        return ', '.join(parts)
    
    def reverse_geocode(self, latitude: float, longitude: float, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Main method to reverse geocode coordinates to address
        
        Args:
            latitude: GPS latitude
            longitude: GPS longitude
            **kwargs: Additional parameters like api_key for paid services
        
        Returns:
            Dictionary with address information or None if failed
        """
        # Check cache first
        cache_key = self._get_cache_key(latitude, longitude)
        if cache_key in self.cache:
            logger.info(f"Using cached address for {cache_key}")
            return self.cache[cache_key]
        
        # Validate coordinates
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            logger.error(f"Invalid coordinates: {latitude}, {longitude}")
            return None
        
        result = None
        
        # Choose provider and make request
        if self.provider == 'nominatim':
            result = self.reverse_geocode_nominatim(latitude, longitude)
        elif self.provider == 'google':
            api_key = kwargs.get('google_api_key')
            if not api_key:
                logger.error("Google API key required for Google geocoding")
                return None
            result = self.reverse_geocode_google(latitude, longitude, api_key)
        elif self.provider == 'mapbox':
            api_key = kwargs.get('mapbox_api_key')
            if not api_key:
                logger.error("MapBox API key required for MapBox geocoding")
                return None
            result = self.reverse_geocode_mapbox(latitude, longitude, api_key)
        else:
            logger.error(f"Unknown provider: {self.provider}")
            return None
        
        # Cache successful result
        if result:
            self.cache[cache_key] = result
            # Limit cache size
            if len(self.cache) > 1000:
                # Remove oldest entries (simple FIFO)
                oldest_keys = list(self.cache.keys())[:100]
                for key in oldest_keys:
                    del self.cache[key]
        
        return result
    
    def get_simple_address(self, latitude: float, longitude: float, **kwargs) -> str:
        """
        Get a simple, formatted address string
        
        Returns:
            Simple address string like "123 Main St, New York, NY"
        """
        address_data = self.reverse_geocode(latitude, longitude, **kwargs)
        
        if not address_data:
            return f"Near {latitude:.4f}, {longitude:.4f}"
        
        return address_data.get('formatted_address', address_data.get('full_address', ''))
    
    def bulk_reverse_geocode(self, coordinates_list: list, **kwargs) -> list:
        """
        Reverse geocode multiple coordinates with rate limiting
        
        Args:
            coordinates_list: List of (latitude, longitude) tuples
            **kwargs: Additional parameters like api_key
        
        Returns:
            List of address dictionaries
        """
        results = []
        
        for i, (lat, lon) in enumerate(coordinates_list):
            logger.info(f"Processing coordinate {i+1}/{len(coordinates_list)}: {lat}, {lon}")
            
            address = self.reverse_geocode(lat, lon, **kwargs)
            results.append({
                'latitude': lat,
                'longitude': lon,
                'address': address
            })
            
            # Rate limiting for bulk requests
            if self.provider == 'nominatim' and i < len(coordinates_list) - 1:
                time.sleep(1)  # 1 second delay between requests
        
        return results


# Usage examples and configuration
class GeocodingConfig:
    """Configuration for geocoding service"""
    
    # Free option (rate limited)
    NOMINATIM = {
        'provider': 'nominatim',
        'daily_limit': 'unlimited (rate limited)',
        'cost': 'free',
        'accuracy': 'good'
    }
    
    # Paid options (better accuracy and limits)
    GOOGLE_MAPS = {
        'provider': 'google',
        'daily_limit': '40,000 requests/month free, then $0.005/request',
        'cost': 'paid after free tier',
        'accuracy': 'excellent'
    }
    
    MAPBOX = {
        'provider': 'mapbox',
        'daily_limit': '100,000 requests/month free, then $0.75/1000 requests',
        'cost': 'paid after free tier',
        'accuracy': 'excellent'
    }


