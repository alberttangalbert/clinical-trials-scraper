import os
import pandas as pd
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv 

from app.services import AzureOpenaiService, AzureMapsService
from app.core import (
    get_indication_areas_from_description, 
    get_modality_areas_from_description, 
    geocode_address,
    find_closest_hub
)
from app.utils import calculate_max_workers

def run_indication_classifier(company_ids: List[str], company_names: List[str], company_descriptions: List[str]) -> pd.DataFrame:
    """
    Runs the indication classifier to determine the focus areas of biotech companies.

    This function processes a list of company descriptions, uses the Azure OpenAI service to classify
    indication areas, and returns the results as a DataFrame where each row corresponds to a company.

    The output DataFrame contains:
        - 'company_id': The unique identifier for each company.
        - Columns for each possible indication area with binary values (1 if the company works in that area, 0 otherwise).

    :param company_ids: A list of unique company identifiers.
    :param company_descriptions: A list of descriptions corresponding to the companies.
    :return: A pandas DataFrame with indication areas classified for each company.
    :raises FileNotFoundError: If the `indication_areas.txt` file is not found.
    """
    # Path to the indication areas configuration file
    indication_areas_file = "data/config/indications.txt"

    # Ensure the indication areas file exists
    if not os.path.exists(indication_areas_file):
        raise FileNotFoundError(f"The file '{indication_areas_file}' was not found.")

    # Load indication areas from the configuration file
    with open(indication_areas_file, "r") as file:
        indication_areas = [line.strip() for line in file if line.strip()]

    # Initialize the Azure OpenAI service
    azure_openai_service = AzureOpenaiService()

    # List to store results for each company
    results = []

    # Process each company description and classify indication areas
    for company_id, name, description in zip(company_ids, company_names, company_descriptions):
        classified_areas = get_indication_areas_from_description(
            description, name, azure_openai_service, indication_areas
        )
        results.append({"company_id": company_id, "indication_areas": classified_areas})

    # Prepare the data for the output DataFrame
    processed_data = []
    for result in results:
        row = {"company_id": result["company_id"]}
        for area in indication_areas:
            row[area] = 1 if area in result["indication_areas"] else 0
        processed_data.append(row)

    # Convert the processed data into a pandas DataFrame
    return pd.DataFrame(processed_data)

def run_modality_classifier(company_ids: List[str], company_names: List[str], company_descriptions: List[str]) -> pd.DataFrame:
    """
    Runs the modality classifier to determine the modality focus areas of biotech companies.

    This function processes a list of company descriptions, uses the Azure OpenAI service to classify
    modality areas, and returns the results as a DataFrame where each row corresponds to a company.

    The output DataFrame contains:
        - 'company_id': The unique identifier for each company.
        - Columns for each possible modality area with binary values (1 if the company works in that area, 0 otherwise).

    :param company_ids: A list of unique company identifiers.
    :param company_descriptions: A list of descriptions corresponding to the companies.
    :return: A pandas DataFrame with modality areas classified for each company.
    :raises FileNotFoundError: If the `modality_areas.txt` file is not found.
    """
    # Path to the modality areas configuration file
    modality_areas_file = "data/config/modalities.txt"

    # Ensure the modality areas file exists
    if not os.path.exists(modality_areas_file):
        raise FileNotFoundError(f"The file '{modality_areas_file}' was not found.")

    # Load modality areas from the configuration file
    with open(modality_areas_file, "r") as file:
        modality_areas = [line.strip() for line in file if line.strip()]

    # # Create the system prompt for the Azure OpenAI service
    # system_prompt = create_modality_system_prompt(modality_areas)

    # Initialize the Azure OpenAI service
    azure_openai_service = AzureOpenaiService()

    # List to store results for each company
    results = []

    # Process each company description and classify modality areas
    for company_id, name, description in zip(company_ids, company_names, company_descriptions):
        classified_areas = get_modality_areas_from_description(
            description, name, azure_openai_service, modality_areas
        )
        results.append({"company_id": company_id, "modality_areas": classified_areas})

    # Prepare the data for the output DataFrame
    processed_data = []
    for result in results:
        row = {"company_id": result["company_id"]}
        for area in modality_areas:
            row[area] = 1 if area in result["modality_areas"] else 0
        processed_data.append(row)

    # Convert the processed data into a pandas DataFrame
    return pd.DataFrame(processed_data)

def run_geocoding(
    company_ids: List[str], 
    company_names: List[str], 
    company_addresses: List[str]
) -> Tuple[pd.DataFrame, List[Dict]]:
    """
    Run geocoding for a list of company addresses using Azure Maps Service.

    Args:
        company_ids (List[str]): List of company IDs to be geocoded.
        company_names (List[str]): List of company names corresponding to the IDs.
        company_addresses (List[str]): List of company addresses to be geocoded.

    Returns:
        Tuple[pd.DataFrame, List[Dict]]: A tuple containing:
            - pd.DataFrame: A DataFrame with geocoding results including company ID, name, address, latitude, and longitude.
            - List[Dict]: A list of dictionaries with detailed geocoding results.
    """

    azure_maps_service = AzureMapsService()

    # Prepare results list
    results: List[Dict] = []

    # Dynamically calculate max_workers for ThreadPoolExecutor
    max_workers = calculate_max_workers(io_bound=True)

    # Use ThreadPoolExecutor for concurrent geocoding
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_address = {
            executor.submit(
                geocode_address, azure_maps_service, company_addresses[i], company_ids[i], company_names[i]
            ): i
            for i in range(len(company_ids))
        }

        for future in as_completed(future_to_address):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error processing a future: {e}")
    
    # Create DataFrame for results, explicitly including "COMPANYID"
    results_df = pd.DataFrame(results, columns=["company_id", "company_name", "address", "latitude", "longitude"])

    return results_df, results


def run_hub_proximity_calculator(
    data: List[Dict[str, object]],
    hub_coords_file_path: str,
    distance_threshold: float = -1
) -> Dict[Tuple[Optional[int], Optional[str], Optional[str]], Tuple[Optional[str], Optional[float]]]:
    """
    Determine the closest hub and distance for each company's location by calling `find_closest_hub`.

    :param data: List of dictionaries with keys:
                    - 'company_id': int or None
                    - 'company_name': str or None
                    - 'address': str or None
                    - 'latitude': float or None
                    - 'longitude': float or None
    :param hub_coords_file_path: Path to the CSV file containing hub coordinates.
    :param distance_threshold: Maximum allowable distance to a hub (in kilometers).
    :return: Dictionary where the key is a tuple (company_id, company_name, company_address),
             and the value is a tuple (closest hub name, distance in kilometers), or (None, None) if out of range.
    """
    # Load hub coordinates from the CSV file
    hubs = []
    try:
        with open(hub_coords_file_path, mode="r") as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                hubs.append({
                    "city": row["city"],
                    "latitude": float(row["latitude"]),
                    "longitude": float(row["longitude"]),
                })
    except Exception as e:
        raise ValueError(f"Error reading hub coordinates file: {e}")

    # Calculate closest hub for each company
    hub_mapping = {}
    for item in data:
        company_id = item.get("company_id")
        company_name = item.get("company_name")
        company_address = item.get("address")
        company_lat = item.get("latitude")
        company_lon = item.get("longitude")

        if company_lat is None or company_lon is None:
            hub_mapping[(company_id, company_name, company_address)] = (None, None)
            continue

        # Use the `find_closest_hub` function to calculate the closest hub
        closest_hub, min_distance = find_closest_hub(
            company_lat, company_lon, hubs, distance_threshold
        )
        hub_mapping[(company_id, company_name, company_address)] = (closest_hub, min_distance)

    return hub_mapping