import os
import googlemaps
from datetime import datetime, timedelta
import database
import config

API_KEY = config.GOOGLE_MAPS_API_KEY

def calculate_commutes():
    if not API_KEY or API_KEY == 'your_api_key_here':
        print("Please set your GOOGLE_MAPS_API_KEY in .env file")
        return

    gmaps = googlemaps.Client(key=API_KEY)
    
    # Determine destination dynamically (lat/lng tuple if available, fallback to name)
    destination = config.TARGET_DESTINATION_NAME
    if config.TARGET_LAT is not None and config.TARGET_LNG is not None:
        destination = (config.TARGET_LAT, config.TARGET_LNG)
        print(f"Target destination: Coordinates {destination}")
    else:
        print(f"Target destination: Name '{destination}'")
    
    # Target arrival time is next Monday at the configured arrival time (default 1:00 PM)
    now = datetime.now()
    days_ahead = 0 - now.weekday()
    if days_ahead <= 0: # Target next week if it's already Monday or later
        days_ahead += 7
    next_monday = now + timedelta(days=days_ahead)
    
    # Parse target arrival time
    arrival_hour, arrival_minute = 13, 0
    if config.TARGET_ARRIVAL_TIME:
        try:
            parts = config.TARGET_ARRIVAL_TIME.split(":")
            arrival_hour = int(parts[0])
            arrival_minute = int(parts[1])
        except (ValueError, AttributeError, IndexError):
            print(f"Failed to parse TARGET_ARRIVAL_TIME '{config.TARGET_ARRIVAL_TIME}'. Falling back to 13:00.")
            arrival_hour, arrival_minute = 13, 0

    target_arrival = next_monday.replace(hour=arrival_hour, minute=arrival_minute, second=0, microsecond=0)
    print(f"Target arrival time set to: {target_arrival}")
    
    unprocessed = database.get_unprocessed_commutes()
    print(f"Found {len(unprocessed)} listings needing commute times.")
    
    for listing in unprocessed:
        # If we have lat/lng, use it. Otherwise fallback to locality string.
        origin = listing['locality'] + ", Bangalore"
        if listing['latitude'] and listing['longitude']:
            origin = (listing['latitude'], listing['longitude'])
            
        print(f"Calculating commute from {origin}...")
        
        try:
            # Simulate departure exactly 1 hour before target arrival time to model typical commute window
            target_departure = target_arrival - timedelta(hours=1)
            
            result = gmaps.distance_matrix(
                origins=[origin],
                destinations=[destination],
                mode="driving",
                departure_time=target_departure
            )
            
            element = result['rows'][0]['elements'][0]
            
            if element['status'] == 'OK':
                # Time is in seconds, convert to minutes
                duration_in_traffic = element.get('duration_in_traffic', element['duration'])['value']
                commute_mins = duration_in_traffic // 60
                
                # Distance is in meters, convert to km
                distance_km = element['distance']['value'] / 1000.0
                
                database.update_commute(listing['id'], commute_mins, distance_km)
                print(f"Updated {listing['id']}: {commute_mins} mins, {distance_km} km")
            else:
                print(f"Could not route from {origin}: {element['status']}")
                
        except Exception as e:
            print(f"Error calculating commute for {listing['id']}: {e}")

if __name__ == "__main__":
    calculate_commutes()
