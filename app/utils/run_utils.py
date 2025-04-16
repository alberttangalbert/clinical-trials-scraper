import os 
import pandas as pd
from app.utils.general_utils import ensure_directory_exists
from app.utils.geocoding_utils import parse_addresses

def ensure_classification_input_output_exists():
    ensure_directory_exists("data/raw")
    ensure_directory_exists("data/processed")

    output_file_path = "data/raw/biotech_comp_descriptions_w_name.csv"
    input_addresses_file_path = "data/raw/biotech_comp_addresses.csv"
    input_descriptions_file_path = "data/raw/biotech_comp_descriptions.csv"

    # Check if the output file already exists
    if os.path.exists(output_file_path):
        print(f"Input file '{output_file_path}' already exists.")
        return output_file_path

    # Check if the raw files exist
    if not os.path.exists(input_addresses_file_path) or not os.path.exists(input_descriptions_file_path):
        raise FileNotFoundError(
            f"Required raw files '{input_addresses_file_path}' or '{input_descriptions_file_path}' are missing."
        )

    # Load the raw files and merge them
    print("Creating the input file by merging raw data...")
    addresses = pd.read_csv(input_addresses_file_path)
    descriptions = pd.read_csv(input_descriptions_file_path)

    merged = descriptions.merge(addresses, left_on="COMPANY_ID", right_on="COMPANYID", how="left")
    output = merged.loc[:, ["COMPANY_ID", "COMPANYNAME", "IQ_BUSINESS_DESCRIPTION"]]
    output = output.rename(columns={"COMPANYNAME": "COMPANY_NAME"})


    # Save the merged file
    output.to_csv(output_file_path, index=False)
    print(f"The new CSV file '{output_file_path}' has been created.")
    return output_file_path


def ensure_geocoding_input_output_exists():
    ensure_directory_exists("output/")
    ensure_directory_exists("data/processed")

    input_addresses_file_path = "data/raw/biotech_comp_addresses.csv"
    output_file_path = "data/raw/biotech_comp_parsed_addresses.csv"

    # Check if the output file already exists
    if os.path.exists(output_file_path):
        print(f"Input file '{output_file_path}' already exists.")
        return output_file_path

    # Check if the raw file exists
    if not os.path.exists(input_addresses_file_path):
        raise FileNotFoundError(
            f"Required raw files '{input_addresses_file_path}' is missing."
        )
    
    # Load the raw file and parse the addresses
    print("Creating the input file by parsing addresses...")
    parsed_addresses = parse_addresses(input_addresses_file_path)

    # Save the parsed addresses file
    parsed_addresses.to_csv("data/raw/biotech_comp_parsed_addresses.csv", index=False)
    print(f"The new CSV file '{output_file_path}' has been created.")
    return output_file_path
