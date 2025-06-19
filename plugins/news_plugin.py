import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run(country="us", category=None):
    """
    Get top news headlines using NewsAPI
    Args:
        country (str): Country code for headlines (default: 'us')
        category (str): News category (e.g., 'business', 'sports', etc.)
    Returns:
        dict: News headlines or error message
    """
    api_key = os.getenv('NEWS_API_KEY')
    if not api_key:
        return {
            "error": "API key not found. Please set NEWS_API_KEY in your .env file",
            "status": "error"
        }
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "apiKey": api_key,
        "country": country
    }
    if category:
        params["category"] = category
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get("status") != "ok":
            return {
                "error": data.get("message", "Unknown error from NewsAPI"),
                "status": "error"
            }
        headlines = [
            {
                "title": article["title"],
                "description": article["description"],
                "url": article["url"],
                "source": article["source"]["name"]
            }
            for article in data.get("articles", [])
        ]
        return {
            "status": "success",
            "country": country,
            "category": category,
            "headlines": headlines
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": f"Failed to fetch news: {str(e)}",
            "status": "error"
        }
    except (KeyError, ValueError) as e:
        return {
            "error": f"Failed to parse news data: {str(e)}",
            "status": "error"
        } 