import os
import googlemaps
from datetime import datetime, timedelta
import database
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
DESTINATION = "Bagmane Constellation Business Park, Doddanekundi, Bengaluru, Karnataka"

def calculate_commutes():
    if not API_KEY or API_KEY == 'your_api_key_here':
        print("Please set your GOOGLE_MAPS_API_KEY in .env file")
        return

    gmaps = googlemaps.Client(key=API_KEY)
    
    # Target arrival time is next Monday at 1:00 PM
    now = datetime.now()
    days_ahead = 0 - now.weekday()
    if days_ahead <= 0: # Target next week if it's already Monday or later
        days_ahead += 7
    next_monday = now + timedelta(days=days_ahead)
    target_arrival = next_monday.replace(hour=13, minute=0, second=0, microsecond=0)
    
    unprocessed = database.get_unprocessed_commutes()
    print(f"Found {len(unprocessed)} listings needing commute times.")
    
    for listing in unprocessed:
        # If we have lat/lng, use it. Otherwise fallback to locality string.
        # But NoBroker might not expose lat/lng easily in the basic DOM.
        # For now, if lat/lng is None, we can try to geocode the locality.
        
        origin = listing['locality'] + ", Bangalore"
        if listing['latitude'] and listing['longitude']:
            origin = (listing['latitude'], listing['longitude'])
            
        print(f"Calculating commute from {origin}...")
        
        try:
            # Note: departure_time or arrival_time can be used. Distance Matrix supports arrival_time for transit.
            # For driving, departure_time is usually preferred but we can just use departure_time = 12:00 PM to simulate 1 PM arrival loosely.
            target_departure = next_monday.replace(hour=12, minute=0, second=0, microsecond=0)
            
            result = gmaps.distance_matrix(
                origins=[origin],
                destinations=[DESTINATION],
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
