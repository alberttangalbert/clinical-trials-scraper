# File: bing_search.py
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Endpoint and subscription key for Bing Search API
BING_API_ENDPOINT = os.getenv("BING_API_ENDPOINT")
BING_API_KEY = os.getenv("BING_API_KEY")


def search_bing(query: str, domain: str = None) -> dict:
    """
    Query the Bing Search API and return JSON results.

    Args:
        query: Search query string.
        domain: Optional domain filter (e.g., "@example.com" or "example.com").

    Returns:
        Parsed JSON response from the Bing Search API.
    """
    # Construct the base URL
    url = BING_API_ENDPOINT

    # If a domain filter is provided, prefix the query with site:domain
    if domain:
        # Remove leading '@' if present
        domain = domain.lstrip('@')
        query = f"site:{domain} {query}"

    # Define query parameters
    params = {
        "q": query,
        "count": 7,
    }
    # Set subscription key in headers
    headers = {
        "Ocp-Apim-Subscription-Key": BING_API_KEY
    }

    # Perform GET request
    response = requests.get(url, params=params, headers=headers)
    # Raise an error for bad status codes
    response.raise_for_status()

    # Return the JSON payload
    return response.json()