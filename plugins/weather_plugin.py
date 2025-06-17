import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run(city="Unionville"):
    """
    Get current weather data for a specified city using OpenWeatherMap API
    Args:
        city (str): Name of the city to get weather data for. Defaults to London.
    Returns:
        dict: Weather data including temperature, description, and other metrics
    """
    api_key = os.getenv('OPENWEATHER_API_KEY')
    
    if not api_key:
        return {
            "error": "API key not found. Please set OPENWEATHER_API_KEY in your .env file",
            "status": "error"
        }
    
    try:
        # Make API request
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        data = response.json()
        
        # Extract relevant information
        weather_data = {
            "status": "success",
            "city": data["name"],
            "country": data["sys"]["country"],
            "temperature": {
                "current": round(data["main"]["temp"], 1),
                "feels_like": round(data["main"]["feels_like"], 1),
                "min": round(data["main"]["temp_min"], 1),
                "max": round(data["main"]["temp_max"], 1)
            },
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "weather": {
                "main": data["weather"][0]["main"],
                "description": data["weather"][0]["description"].capitalize()
            },
            "wind": {
                "speed": data["wind"]["speed"],
                "degrees": data["wind"]["deg"]
            }
        }
        
        return weather_data
        
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Failed to fetch weather data: {str(e)}",
            "status": "error"
        }
    except (KeyError, ValueError) as e:
        return {
            "error": f"Failed to parse weather data: {str(e)}",
            "status": "error"
        } 