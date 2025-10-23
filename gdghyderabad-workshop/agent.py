from google.adk.agents.llm_agent import Agent
from datetime import datetime
import pytz
import googlemaps
from datetime import datetime
import os
import logging
import requests

BASE_URL = os.getenv("GOOGLEAPIS_BASE_URL")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

gmaps = googlemaps.Client(key=os.getenv("GOOGLE_MAPS_API_KEY"))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger.info("Logger initialized.")

def get_location(city: str) -> dict:
    """Helper function to get the geographical location of a city using Google Maps API."""
    geocoding_result = gmaps.geocode(city)
    if geocoding_result and len(geocoding_result) > 0:
        location = geocoding_result[0]['geometry']['location']
        logger.debug(f"Geocoding result for {city}: {location}")
        return location
    else:
        raise ValueError(f"Could not geocode city: {city}")

def get_current_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city for which to retrieve the weather report.

    Returns:
        dict: status and result or error msg.
    """
    if not city or not isinstance(city, str):
        return {
            "status": "error",
            "error_message": "City name must be a non-empty string."
        }
    
    city_normalized = city.lower().strip().replace(" ", "_")

    try:
        location = get_location(city_normalized)
        logger.info(f"Location for {city}: {location}")
        endpoint = f"{BASE_URL}/currentConditions:lookup"
        params = {
            "location.latitude": location["lat"],
            "location.longitude": location["lng"],
            "key": GOOGLE_MAPS_API_KEY
        }
        # weather_result = gmaps.weather(location)
        # logger.info(f"Weather result for {city}: {weather_result}")

        response = requests.get(endpoint, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()

        # return {
        #     "status": "success",
        #     "city": city,
        #     "degree": response['temperature']['degrees'],
        #     "unit": response['temperature']['unit']
        # }
    except Exception as e:
        logger.error(f"Error getting weather for {city}: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error getting weather: {str(e)}"
        }
    
    # if city.lower() == "new york":
    #     return {
    #         "status": "success",
    #         "report": (
    #             "The weather in New York is sunny with a temperature of 25 degrees"
    #             " Celsius (77 degrees Fahrenheit)."
    #         ),
    #     }
    # else:
    #     return {
    #         "status": "error",
    #         "error_message": f"Weather information for '{city}' is not available.",
    #     }

def get_timezones() -> list:
    """Returns a list of all available timezones."""
    return pytz.all_timezones

def get_current_time(city: str) -> dict:
    """Gets the current time in a specified city.
    
    Args:
        city (str): The name of the city for which to retrieve the current time.
        
    Returns:
        dict: Dictionary with status ("success" or "error") and time information
            or error message.
    """
    if not city or not isinstance(city, str):
        return {
            "status": "error",
            "error_message": "City name must be a non-empty string."
        }
    
    try:
        # Method 1: Try to find the timezone from pytz timezone database
        timezone_str = None
        city_normalized = city.lower().replace(" ", "_")

        # Try to find in timezone strings
        for tz in pytz.all_timezones:
                if city_normalized in tz.lower():
                    timezone_str = tz
                    logger.debug(f"Found timezone by name match: {timezone_str}")
                    break
        
        # Method 2: Use Google Maps API if available and API key is set
        if not timezone_str and os.getenv("GOOGLE_API_KEY"):
            try:
                # Use the Places API (New) as recommended
                # First, geocode the city name to get coordinates
                location = get_location(city_normalized)

                # Get timezone from coordinates
                timezone_result = gmaps.timezone(
                    location=location,
                    timestamp=int(datetime.now().timestamp())
                )
                if timezone_result['status'] == 'OK':
                    timezone_str = timezone_result['timeZoneId']
                    logger.debug(f"Found timezone via Google Maps: {timezone_str}")
            except Exception as maps_error:
                logger.warning(f"Google Maps API error: {maps_error}")
                # Continue with the function, we'll handle the case if timezone_str is still None
        
        if timezone_str:
            timezone = pytz.timezone(timezone_str)
            current_time = datetime.now(timezone)
            
            return {
                "status": "success",
                "city": city,
                "time": current_time.strftime("%I:%M %p"),
                "date": current_time.strftime("%Y-%m-%d"),
                "timezone": timezone_str,
                "utc_offset": current_time.strftime("%z")
            }
        else:
            return {
                "status": "error",
                "error_message": f"Could not find timezone for '{city}'."
            }
    except Exception as e:
        logger.error(f"Error getting time for {city}: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error getting time: {str(e)}"
        }

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='Tells the current time and current weather in a specified city.',
    instruction='You are a helpful assistant that tells the current time and current weather in cities.',
    tools=[get_current_time, get_timezones, get_current_weather],
)


