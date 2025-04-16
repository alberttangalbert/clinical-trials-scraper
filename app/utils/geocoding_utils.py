import folium
from typing import List, Dict, Tuple
import folium.plugins
import pandas as pd
from typing import Optional
import csv

def _format_address(row: pd.Series) -> Optional[str]:
    """
    Helper function to format the address by concatenating relevant columns.
    :param row: A row of the DataFrame.
    :return: Formatted address as a string or None if no valid address parts exist.
    """
    # Combine street address fields
    street_parts = [
        str(row.get("STREETADDRESS", "")).strip(),
        str(row.get("STREETADDRESS2", "")).strip(),
        str(row.get("STREETADDRESS3", "")).strip(),
        str(row.get("STREETADDRESS4", "")).strip(),
    ]

    # Collect city and zip code
    city = str(row.get("CITY", "")).strip()
    zipcode = str(row.get("ZIPCODE", "")).strip()

    # Filter out 'nan' and empty parts
    address_parts = [part for part in street_parts if part and part.lower() != 'nan']
    if city and city.lower() != 'nan':
        address_parts.append(city)
    if zipcode and zipcode.lower() != 'nan':
        address_parts.append(zipcode)

    # Join the parts with commas and return
    formatted_address = ", ".join(address_parts)

    return formatted_address if formatted_address else None

def parse_addresses(input_file: str) -> pd.DataFrame:
    """
    Parse the input CSV file and extract a clean list of addresses.
    :param input_file: Path to the input CSV file.
    :return: A DataFrame with a single 'ADDRESS' column containing parsed addresses.
    """
    # Load the dataset
    df = pd.read_csv(input_file)

    # Concatenate address fields into a single string
    df["ADDRESS"] = df.apply(lambda row: _format_address(row), axis=1)

    # Filter rows with valid addresses
    parsed_df = df[["COMPANYID", "COMPANYNAME", "ADDRESS"]].dropna(subset=["ADDRESS"])

    return parsed_df

def plot_coordinates(
    data: List[Dict[str, object]], 
    output_file_path: str = "output/map.html"
) -> None:
    """
    Plot geocoded data on a map and save it as an HTML file.

    :param data: List of dictionaries with keys:
                    - 'address': str (the address as a string)
                    - 'latitude': float (latitude of the address) or None
                    - 'longitude': float (longitude of the address) or None
    :param output_file: Name of the output HTML file.
    :return: None
    """
    # Initialize the map centered at an arbitrary location
    m: folium.Map = folium.Map(location=[0, 0], zoom_start=2)  # Start with a world view

    for item in data:
        latitude = item.get("latitude")
        longitude = item.get("longitude")
        address = item.get("address", "Unknown Address")
        company_name = item.get("company_name", "Unknown Company")

        if latitude is not None and longitude is not None:
            folium.Marker(
                location=[latitude, longitude],
                popup=company_name + "\n" + address
            ).add_to(m)

    # Save map to file
    m.save(output_file_path)
    print(f"Map saved to {output_file_path}")


def plot_heatmap(
    data: List[Dict[str, object]],
    output_file_path: str = "output/heatmap.html",
    hub_coords_file_path: str = "app/resources/hub_coords.csv"
) -> None:
    """
    Plot geocoded data as a heatmap and save it as an HTML file.

    :param data: List of dictionaries with keys:
                    - 'address': str (the address as a string)
                    - 'latitude': float (latitude of the address) or None
                    - 'longitude': float (longitude of the address) or None
    :param output_file_path: Path to the output HTML file.
    :param hub_coords_file_path: Path to the CSV file containing hub coordinates.
    :return: None
    """
    # Initialize the map centered at an arbitrary location
    m: folium.Map = folium.Map(location=[0, 0], zoom_start=2)  # Start with a world view

    # Prepare data for the heatmap
    heat_data = [
        [item["latitude"], item["longitude"]]
        for item in data
        if item.get("latitude") is not None and item.get("longitude") is not None
    ]

    # Add heatmap to the map
    folium.plugins.HeatMap(heat_data).add_to(m)

    # Add markers for hubs
    try:
        with open(hub_coords_file_path, mode="r") as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                latitude = float(row["latitude"])
                longitude = float(row["longitude"])
                city = row["city"]
                folium.Marker(
                    location=[latitude, longitude],
                    popup=city
                ).add_to(m)
    except Exception as e:
        print(f"Error reading hub coordinates file: {e}")

    # Save map to file
    m.save(output_file_path)
    print(f"Heatmap with hubs saved to {output_file_path}")


def plot_hubs_and_companies(
    data: List[Dict[str, object]],
    hub_mapping: Dict[Tuple[int, str, str], Tuple[str, float]],
    output_file_path: str = "output/hubmap.html",
    hub_coords_file_path: str = "app/resources/hub_coords.csv",
    distance_threshold: float = 200.0
) -> None:
    """
    Plot hubs and companies on a map with connections and save as an HTML file.

    :param data: List of dictionaries with keys:
                    - 'address': str (the company address)
                    - 'latitude': float (latitude of the company) or None
                    - 'longitude': float (longitude of the company) or None
    :param hub_mapping: Dictionary where keys are tuples (company ID, name, address),
                        and values are tuples (hub name, distance to hub).
    :param output_file_path: Path to the output HTML file.
    :param hub_coords_file_path: Path to the CSV file containing hub coordinates.
    :param distance_threshold: Maximum distance for drawing connections (in kilometers).
    :return: None
    """
    # Initialize the map centered at an arbitrary location
    m = folium.Map(location=[0, 0], zoom_start=2)  # Start with a world view

    # Load hub coordinates from the CSV file
    hubs = {}
    try:
        with open(hub_coords_file_path, mode="r") as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                hubs[row["city"]] = {
                    "latitude": float(row["latitude"]),
                    "longitude": float(row["longitude"]),
                }
    except Exception as e:
        print(f"Error reading hub coordinates file: {e}")
        return

    # Plot hubs as red markers
    for city, coords in hubs.items():
        folium.Marker(
            location=[coords["latitude"], coords["longitude"]],
            popup=f"Hub: {city}",
            icon=folium.Icon(color="red")
        ).add_to(m)

    # Plot companies as blue markers and draw connections
    for company, (closest_hub, distance) in hub_mapping.items():
        company_id, company_name, company_address = company
        company_coords = next(
            (item for item in data if item.get("address") == company_address),
            None,
        )

        if not company_coords or company_coords["latitude"] is None or company_coords["longitude"] is None:
            continue

        # Plot the company
        folium.Marker(
            location=[company_coords["latitude"], company_coords["longitude"]],
            popup=f"Company: {company_name}",
            icon=folium.Icon(color="blue")
        ).add_to(m)

        # Draw line if distance is within threshold
        if closest_hub in hubs and distance <= distance_threshold:
            hub_coords = hubs[closest_hub]
            folium.PolyLine(
                locations=[
                    [company_coords["latitude"], company_coords["longitude"]],
                    [hub_coords["latitude"], hub_coords["longitude"]],
                ],
                color="green",
                weight=2,
            ).add_to(m)

    # Save map to file
    m.save(output_file_path)
    print(f"Map with hubs and companies saved to {output_file_path}")

def save_hub_mapping_to_csv(
    hub_mapping: Dict[Tuple[int, str, str], Tuple[str, float]],
    output_file_path: str = "output/hub_mapping.csv"
) -> None:
    """
    Save the hub mapping data to a CSV file.

    :param hub_mapping: Dictionary where keys are tuples (company ID, name, address),
                        and values are tuples (hub name, distance to hub).
    :param output_file_path: Path to the output CSV file.
    :return: None
    """
    # Define CSV headers
    headers = [
        "Company_ID",
        "Company_Name",
        "Company_Address",
        "Closest_Hub",
        "Hub_Distance_km"
    ]

    # Write to CSV
    with open(output_file_path, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)  # Write the header row

        for company_info, hub_info in hub_mapping.items():
            company_id, company_name, company_address = company_info
            closest_hub, distance = hub_info
            writer.writerow([company_id, company_name, company_address, closest_hub, distance])

    print(f"Hub mapping has been saved to {output_file_path}")