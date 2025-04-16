from app.services import AzureMapsService
from typing import Dict

def geocode_address(
        geocoder: AzureMapsService, 
        address: str, 
        company_id: int, 
        company_name: str
) -> Dict:
    """
    Geocode a single address.
    :param geocoder: Instance of Geocoder.
    :param address: Address to geocode.
    :param company_id: Company ID.
    :param company_name: Company name.
    :return: A dictionary with geocoding results.
    """
    try:
        latitude, longitude = geocoder.get_coordinates(address)
        return {
            "company_id": company_id,
            "company_name": company_name,
            "address": address,
            "latitude": latitude,
            "longitude": longitude,
        }
    except Exception as e:
        print(f"Error geocoding {address}: {e}")
        return {
            "company_id": company_id,
            "company_name": company_name,
            "address": address,
            "latitude": None,
            "longitude": None,
        }