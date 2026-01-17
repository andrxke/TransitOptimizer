import googlemaps
import os
from datetime import datetime, timedelta, timezone

LOG_FILE = "debug_routes.txt"

def log_to_file(message):
    """Logs a message to both console and a file."""
    print(message)
    with open(LOG_FILE, "a") as f:
        f.write(message + "\n")

class GoogleMapsClient:
    def __init__(self, api_key):
        self.gmaps = googlemaps.Client(key=api_key)

    def get_trip_details(self, origin, destination, departure_time, mode="transit"):
        """
        Get detailed trip info (duration + steps) from origin to destination at a specific departure time.
        """
        log_to_file(f"Checking trip: {origin} -> {destination} at {departure_time}")
        try:
            # Directions API provides full route details
            # generating alternatives=True allows us to see other options that might be faster
            directions_result = self.gmaps.directions(
                origin,
                destination,
                mode=mode,
                departure_time=departure_time,
                alternatives=True
            )
            
            if directions_result:
                # Iterate through ALL returned routes to find the one with the shortest duration
                best_route = None
                min_route_duration = float('inf')

                for route in directions_result:
                    leg = route['legs'][0]
                    duration = leg['duration']['value']
                    
                    if duration < min_route_duration:
                        min_route_duration = duration
                        best_route = route

                # Process the best route found
                leg = best_route['legs'][0]
                duration = leg['duration']['value'] # seconds
                duration_text = leg['duration']['text']
                
                # Extract steps
                steps_summary = []
                for step in leg['steps']:
                    instructions = step['html_instructions']
                    if 'transit_details' in step:
                        line = step['transit_details']['line']['short_name']
                        vehicle = step['transit_details']['line']['vehicle']['name']
                        steps_summary.append(f"{vehicle} {line}")
                    else:
                        # Normalize walking/other steps
                        clean_instr = instructions.replace('<b>', '').replace('</b>', '').replace('  ', ' ')
                        if "Walk" in clean_instr:
                            steps_summary.append("Walk")
                        else:
                            steps_summary.append(clean_instr)
                
                route_summary = " -> ".join(steps_summary)
                
                # Try to get the actual departure and arrival times from the API response
                actual_departure_text = None
                actual_departure_iso = None
                arrival_text = None
                arrival_iso = None
                
                if 'departure_time' in leg:
                    actual_departure_text = leg['departure_time']['text']
                    dt_obj = datetime.fromtimestamp(leg['departure_time']['value'])
                    actual_departure_iso = dt_obj.isoformat()

                if 'arrival_time' in leg:
                    arrival_text = leg['arrival_time']['text']
                    dt_obj = datetime.fromtimestamp(leg['arrival_time']['value'])
                    arrival_iso = dt_obj.isoformat()
                
                log_to_file(f"  Found best route among {len(directions_result)} options: {duration_text} ({route_summary}) - Departs: {actual_departure_text}, Arrives: {arrival_text}")
                
                return {
                    "duration_seconds": duration,
                    "duration_text": duration_text,
                    "route_summary": route_summary,
                    "steps": steps_summary,
                    "actual_departure_text": actual_departure_text,
                    "actual_departure_iso": actual_departure_iso,
                    "arrival_text": arrival_text,
                    "arrival_iso": arrival_iso
                }
            else:
                log_to_file("  No route found.")
        except Exception as e:
            log_to_file(f"  Error fetching directions: {e}")
            import traceback
            traceback.print_exc()
            return None
        return None

def find_best_departure(api_key, origin, destination, window_start, window_end, interval_minutes=15):
    """
    Finds the shortest travel time within a window by sampling every interval_minutes.
    window_start and window_end should be datetime objects.
    """
    client = GoogleMapsClient(api_key)
    best_time = None
    min_duration = float('inf')
    best_details = None
    results = []

    log_to_file(f"\n--- Starting Optimization: Window {window_start} to {window_end} ---")

    current_time = window_start
    while current_time <= window_end:
        details = client.get_trip_details(origin, destination, current_time)
        if details is not None:
            # Use actual departure if available, otherwise fallback to requested
            display_time = details.get('actual_departure_iso') or current_time.isoformat()
            
            results.append({
                "departure_time": display_time,
                "requested_time": current_time.isoformat(),
                "duration_seconds": details['duration_seconds'],
                "duration_text": details['duration_text'],
                "route_summary": details['route_summary'],
                "actual_departure_text": details.get('actual_departure_text'),
                "arrival_text": details.get('arrival_text')
            })
            if details['duration_seconds'] < min_duration:
                min_duration = details['duration_seconds']
                best_time = current_time # Keep tracking the best *window* slot
                best_details = details
        
        current_time += timedelta(minutes=interval_minutes)

    log_to_file(f"--- Optimization Complete. Best Time: {best_time}. Min Duration: {min_duration}s ---\n")

    return {
        "best_departure": best_details.get('actual_departure_iso') if best_details else (best_time.isoformat() if best_time else None),
        "min_duration_seconds": min_duration if min_duration != float('inf') else None,
        "best_route_summary": best_details['route_summary'] if best_details else None,
        "results": results
    }


def optimize_work_schedule(api_key, origins, destination, work_duration_hours, window_start, window_end, interval_minutes=30):
    """
    Finds the best schedule (departure to work) that minimizes total round trip time (to work + from work).
    Accepts a list of origins.
    """
    client = GoogleMapsClient(api_key)
    all_results = []

    # Ensure origins is a list
    if isinstance(origins, str):
        origins = [origins]

    log_to_file(f"\n--- Optimizing Work Schedule for {len(origins)} origins: Window {window_start} to {window_end} ---")

    for origin in origins:
        log_to_file(f"Checking schedules for origin: {origin}")
        current_departure = window_start
        while current_departure <= window_end:
            # Trip 1: Home -> Work
            to_work = client.get_trip_details(origin, destination, current_departure)
            
            if to_work is not None:
                # Calculate arrival at work
                arrival_at_work = current_departure + timedelta(seconds=to_work['duration_seconds'])
                
                # Identify time to leave work (must stay for work_duration_hours)
                leave_work_time = arrival_at_work + timedelta(hours=work_duration_hours)
                
                # Trip 2: Work -> Home
                to_home = client.get_trip_details(destination, origin, leave_work_time)
                
                if to_home is not None:
                    total_duration = to_work['duration_seconds'] + to_home['duration_seconds']
                    
                    all_results.append({
                        "origin": origin,
                        "departure_to_work": to_work.get('actual_departure_iso') or current_departure.isoformat(),
                        "duration_to_work": to_work['duration_seconds'],
                        "route_to_work": to_work['route_summary'],
                        
                        "leave_work_time": to_home.get('actual_departure_iso') or leave_work_time.isoformat(),
                        "duration_to_home": to_home['duration_seconds'],
                        "route_to_home": to_home['route_summary'],
                        
                        "total_commute_seconds": total_duration,
                        "total_commute_text": f"{total_duration // 60} mins"
                    })
            
            current_departure += timedelta(minutes=interval_minutes)
        
    # Sort all results by total commute time (least to most)
    all_results.sort(key=lambda x: x['total_commute_seconds'])
    
    best_schedule = all_results[0] if all_results else None

    return {
        "best_schedule": best_schedule,
        "results": all_results
    }
