from typing import List, Dict, Tuple, Optional

from app.utils.general_utils import get_distance


def find_closest_hub(
    company_lat: float,
    company_lon: float,
    hubs: List[Dict[str, float]],
    distance_threshold: float = -1
) -> Tuple[Optional[str], Optional[float]]:
    """
    Find the closest hub to a given company's location.

    :param company_lat: Latitude of the company.
    :param company_lon: Longitude of the company.
    :param hubs: List of hub dictionaries with 'city', 'latitude', and 'longitude'.
    :param distance_threshold: Maximum allowable distance to a hub (in kilometers).
    :return: A tuple (closest hub name, distance in kilometers), or (None, None) if no hub is within the threshold.
    """
    min_distance = float("inf")
    closest_hub = None

    for hub in hubs:
        distance = get_distance(
            company_lat, company_lon, hub["latitude"], hub["longitude"]
        )
        if distance < min_distance:
            min_distance = distance
            closest_hub = hub["city"]

    # Apply distance threshold
    if distance_threshold > 0 and min_distance > distance_threshold:
        return None, None

    return closest_hub, min_distance