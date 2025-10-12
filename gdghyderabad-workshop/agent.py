from google.adk.agents.llm_agent import Agent
from datetime import datetime
import pytz

def get_timezones() -> list:
    """Returns a list of all available timezones."""
    return pytz.all_timezones

def get_current_time(city: str) -> dict:
    """Gets the current time in a specified city."""
    try:
        # Find the timezone for the city
        timezone_str = None
        for tz in pytz.all_timezones:
            if city.lower().replace(" ", "_") in tz.lower():
                timezone_str = tz
                break

        if timezone_str:
            timezone = pytz.timezone(timezone_str)
            current_time = datetime.now(timezone)
            return {
                "status": True,
                "city": city,
                "time": current_time.strftime("%I:%M %p"),
                "timezone": timezone_str,
            }
        else:
            return {"status": False, "error": f"Could not find timezone for {city}"}
    except Exception as e:
        return {"status": False, "error": str(e)}

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='Tells the current time in a specified city.',
    instruction='You are a helpful assistant that tells the current time in cities. Use the "get_current_time" tool for this purpose.',
    tools=[get_current_time, get_timezones],
)
