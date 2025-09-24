import logging
from typing import Optional, Dict, Tuple, List

logger = logging.getLogger(__name__)


def normalize_location(latitude: Optional[str], longitude: Optional[str]) -> Optional[Dict[str, float]]:
    """
    Normalize and validate GPS coordinates.
    
    Args:
        latitude: Latitude as string
        longitude: Longitude as string
        
    Returns:
        Dictionary with normalized coordinates or None if invalid
    """
    try:
        if latitude is None or longitude is None:
            logger.debug("Latitude or longitude is None")
            return None
        
        # Convert to float
        lat = float(latitude)
        lng = float(longitude)
        
        # Validate coordinate ranges
        if not (-90.0 <= lat <= 90.0):
            logger.warning(f"Invalid latitude: {lat} (must be between -90 and 90)")
            return None
        
        if not (-180.0 <= lng <= 180.0):
            logger.warning(f"Invalid longitude: {lng} (must be between -180 and 180)")
            return None
        
        # Return normalized coordinates
        normalized = {
            "latitude": lat,
            "longitude": lng
        }
        
        logger.debug(f"Normalized coordinates: {lat}, {lng}")
        return normalized
        
    except (ValueError, TypeError) as e:
        logger.warning(f"Error parsing coordinates '{latitude}', '{longitude}': {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error normalizing location: {e}")
        return None


def calculate_distance(coord1: Dict[str, float], coord2: Dict[str, float]) -> float:
    """
    Calculate the great circle distance between two GPS coordinates.
    
    Args:
        coord1: First coordinate dict with 'latitude' and 'longitude'
        coord2: Second coordinate dict with 'latitude' and 'longitude'
        
    Returns:
        Distance in kilometers
    """
    try:
        from math import radians, sin, cos, asin, sqrt
        
        lat1 = radians(coord1["latitude"])
        lon1 = radians(coord1["longitude"])
        lat2 = radians(coord2["latitude"])
        lon2 = radians(coord2["longitude"])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon/2) ** 2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        distance = c * r
        
        logger.debug(f"Distance calculated: {distance:.3f} km")
        return distance
        
    except (KeyError, TypeError, ValueError) as e:
        logger.error(f"Error calculating distance: {e}")
        return 0.0


def is_valid_coordinates(latitude: float, longitude: float) -> bool:
    """
    Check if coordinates are valid.
    
    Args:
        latitude: Latitude value
        longitude: Longitude value
        
    Returns:
        True if coordinates are valid, False otherwise
    """
    try:
        return (-90.0 <= latitude <= 90.0) and (-180.0 <= longitude <= 180.0)
    except (TypeError, ValueError):
        return False


def format_coordinates(latitude: float, longitude: float, precision: int = 6) -> str:
    """
    Format coordinates as a human-readable string.
    
    Args:
        latitude: Latitude value
        longitude: Longitude value
        precision: Decimal places to include
        
    Returns:
        Formatted coordinate string
    """
    try:
        if not is_valid_coordinates(latitude, longitude):
            return "Invalid coordinates"
        
        # Determine cardinal directions
        lat_dir = "N" if latitude >= 0 else "S"
        lng_dir = "E" if longitude >= 0 else "W"
        
        # Format with specified precision
        lat_str = f"{abs(latitude):.{precision}f}°{lat_dir}"
        lng_str = f"{abs(longitude):.{precision}f}°{lng_dir}"
        
        return f"{lat_str}, {lng_str}"
        
    except Exception as e:
        logger.error(f"Error formatting coordinates: {e}")
        return "Error formatting coordinates"


def get_location_bounds(coordinates: List[Dict[str, float]], padding: float = 0.01) -> Dict[str, float]:
    """
    Get bounding box for a list of coordinates.
    
    Args:
        coordinates: List of coordinate dictionaries
        padding: Additional padding around bounds
        
    Returns:
        Dictionary with north, south, east, west bounds
    """
    try:
        if not coordinates:
            return {}
        
        latitudes = [coord["latitude"] for coord in coordinates]
        longitudes = [coord["longitude"] for coord in coordinates]
        
        bounds = {
            "north": max(latitudes) + padding,
            "south": min(latitudes) - padding,
            "east": max(longitudes) + padding,
            "west": min(longitudes) - padding
        }
        
        # Ensure bounds are within valid ranges
        bounds["north"] = min(bounds["north"], 90.0)
        bounds["south"] = max(bounds["south"], -90.0)
        bounds["east"] = min(bounds["east"], 180.0)
        bounds["west"] = max(bounds["west"], -180.0)
        
        return bounds
        
    except (KeyError, TypeError, ValueError) as e:
        logger.error(f"Error calculating bounds: {e}")
        return {}


def geocode_address(address: str) -> Optional[Dict[str, float]]:
    """
    Geocode an address to coordinates (placeholder implementation).
    
    Note: This is a placeholder. In production, you would integrate with
    a geocoding service like Google Maps, OpenStreetMap Nominatim, etc.
    
    Args:
        address: Address string to geocode
        
    Returns:
        Coordinates dictionary or None if geocoding fails
    """
    logger.warning("Geocoding not implemented - placeholder function")
    # In a real implementation, you would:
    # 1. Call a geocoding API
    # 2. Parse the response
    # 3. Return normalized coordinates
    return None


def reverse_geocode(latitude: float, longitude: float) -> Optional[str]:
    """
    Reverse geocode coordinates to an address (placeholder implementation).
    
    Note: This is a placeholder. In production, you would integrate with
    a reverse geocoding service.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        
    Returns:
        Address string or None if reverse geocoding fails
    """
    logger.warning("Reverse geocoding not implemented - placeholder function")
    # In a real implementation, you would:
    # 1. Call a reverse geocoding API
    # 2. Parse the response
    # 3. Return formatted address
    return None


def is_within_area(coordinate: Dict[str, float], 
                   center: Dict[str, float], 
                   radius_km: float) -> bool:
    """
    Check if a coordinate is within a specified radius of a center point.
    
    Args:
        coordinate: Coordinate to check
        center: Center point coordinate
        radius_km: Radius in kilometers
        
    Returns:
        True if coordinate is within radius, False otherwise
    """
    try:
        distance = calculate_distance(coordinate, center)
        return distance <= radius_km
    except Exception as e:
        logger.error(f"Error checking if coordinate is within area: {e}")
        return False


# Predefined city boundaries for common Indian cities (sample data)
CITY_BOUNDARIES = {
    "pune": {
        "center": {"latitude": 18.5204, "longitude": 73.8567},
        "bounds": {
            "north": 18.6298,
            "south": 18.4109,
            "east": 73.9345,
            "west": 73.7788
        }
    },
    "mumbai": {
        "center": {"latitude": 19.0760, "longitude": 72.8777},
        "bounds": {
            "north": 19.2695,
            "south": 18.8826,
            "east": 72.9781,
            "west": 72.7767
        }
    },
    "bangalore": {
        "center": {"latitude": 12.9716, "longitude": 77.5946},
        "bounds": {
            "north": 13.1394,
            "south": 12.8039,
            "east": 77.7815,
            "west": 77.4076
        }
    }
}


def get_city_info(city_name: str) -> Optional[Dict]:
    """
    Get predefined city boundary information.
    
    Args:
        city_name: Name of the city
        
    Returns:
        City information dictionary or None if not found
    """
    return CITY_BOUNDARIES.get(city_name.lower())


def is_in_city(coordinate: Dict[str, float], city_name: str) -> bool:
    """
    Check if a coordinate is within a predefined city boundary.
    
    Args:
        coordinate: Coordinate to check
        city_name: Name of the city
        
    Returns:
        True if coordinate is within city bounds, False otherwise
    """
    try:
        city_info = get_city_info(city_name)
        if not city_info:
            logger.warning(f"City '{city_name}' not found in predefined boundaries")
            return False
        
        bounds = city_info["bounds"]
        lat = coordinate["latitude"]
        lng = coordinate["longitude"]
        
        return (bounds["south"] <= lat <= bounds["north"] and 
                bounds["west"] <= lng <= bounds["east"])
        
    except (KeyError, TypeError) as e:
        logger.error(f"Error checking if coordinate is in city: {e}")
        return False
