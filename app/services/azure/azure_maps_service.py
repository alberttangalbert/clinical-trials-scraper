from azure.core.credentials import AzureKeyCredential
from azure.maps.search import MapsSearchClient
from app.config import Config
from typing import Optional, Tuple

from app.services.azure.azure_error_decorator import handle_azure_errors

class AzureMapsService:
    def __init__(self):
        """
        Initializes the Geocoder class and validates the Azure Maps key.
        """
        self.client = MapsSearchClient(
            credential=AzureKeyCredential(Config.AZURE_MAPS_KEY)
        )

    @handle_azure_errors
    def get_coordinates(self, address: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Geocodes an address into latitude and longitude using Azure Maps.

        :param address: The address to geocode.
        :return: A tuple of (latitude, longitude) if successful, otherwise (None, None).
        """
        result = self.client.get_geocoding(query=address)
        if result.get("features", False):
            coordinates = result["features"][0]["geometry"]["coordinates"]
            longitude: float = coordinates[0]
            latitude: float = coordinates[1]
            return latitude, longitude
        return None, None