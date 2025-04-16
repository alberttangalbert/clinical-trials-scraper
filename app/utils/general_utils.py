import os 
from math import radians, cos, sin, sqrt, atan2

def ensure_directory_exists(file_path: str) -> None:
    """
    Ensures that the directory for the given file path exists. Creates it if it doesn't exist.
    :param file_path: The path to the file.
    """
    # Extract the directory path from the given file path
    directory = os.path.dirname(file_path)
    
    # Check if the directory exists; if not, create it
    if not os.path.exists(directory):
        os.makedirs(directory)
        

def calculate_max_workers(io_bound: bool = True) -> int:
    """
    Calculate the optimal number of workers based on system resources and workload type.
    :param io_bound: Set to True for I/O-bound tasks (e.g., API calls), False for CPU-bound tasks.
    :return: Optimal number of workers.
    """
    cpu_count = os.cpu_count() or 1  # Fallback to 1 if CPU count is unavailable
    if io_bound:
        # I/O-bound tasks can benefit from more threads due to latency
        return min(32, cpu_count * 5)  # Limit max_workers to prevent resource exhaustion
    else:
        # For CPU-bound tasks, match the number of workers to the number of cores
        return cpu_count
    

def get_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """
    Calculate the great-circle distance between two points on the Earth.
    
    :param lat1: Latitude of the first point.
    :param lon1: Longitude of the first point.
    :param lat2: Latitude of the second point.
    :param lon2: Longitude of the second point.
    :return: Distance in kilometers between the two points.
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula to calculate the great-circle distance
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    radius_of_earth_km = 6371  # Radius of the Earth in kilometers
    return radius_of_earth_km * c