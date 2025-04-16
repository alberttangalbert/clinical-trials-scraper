from typing import List

from app.services.azure.azure_openai_service import AzureOpenaiService
from app.utils import parse_chatbot_response, validate_classifications


def create_modality_classification_prompt(company_name: str, modality_areas: List[str]) -> str:
    """
    Creates a system prompt string to identify all modality areas associated with a specific company.
    
    Parameters:
        company_name (str): Name of the company.
        modality_areas (List[str]): List of possible modality areas.

    Returns:
        str: A prompt for identifying the modality areas.
    """
    return (
        f"You are an expert in pharmaceutical and biotech domains, specializing in analyzing company profiles and identifying modality focus areas. "
        f"You have extensive knowledge about the company {company_name} and will use all your expertise and insights to complete the task. "
        f"The task is to identify ALL the modality areas that {company_name} is focused on, based on the provided company description.\n\n"
        f"Here is the list of possible modality areas: {', '.join(modality_areas)}."
        "For the modality areas the company focuses on, explain how and be very very concise."
        "For modality areas the company does not focus on, do not include them in your response!"
    )


def parse_modality_classification_response(modality_areas: List[str]) -> str:
    """
    Creates a parsing prompt to extract modality areas from a given response.

    Parameters:
        modality_areas (List[str]): List of possible modality areas.

    Returns:
        str: A parsing prompt for extracting modality areas as a Python list.
    """
    return (
        "You are an expert in pharmaceutical and biotech domains, specializing in analyzing company profiles and identifying modality focus areas. "
        "You are given a description of modality areas that a company is focused on and need to extract all the modality areas. "
        f"Here is the list of possible modality areas: {', '.join(modality_areas)}."
        "Instructions:\n"
        "1. Based on the provided description, identify and return all the modality areas that match the company focus.\n"
        "2. Prioritize only including modality areas from the provided list of possible modality areas.\n"
        "3. Return your answer strictly as a Python list of strings (e.g., [\"Protein/Monoclonal Antibodies\", \"Small molecules and Natural Products\"]).\n"
        "4. Do not include any explanations, text outside the list, or commentary.\n"
        "5. If you are uncertain about a modality area, make an educated guess based on the description.\n"
        "6. If no modality areas match the description, return an empty list (e.g., [])."
        "Please think step by step"
    )


def get_modality_areas_from_description(
    description: str, 
    company_name: str,
    azure_service: AzureOpenaiService, 
    modality_areas: List[str],
    max_retries: int = 3
) -> List[str]:
    """
    Given a company description, queries the Azure OpenAI service to find the modality areas.
    Tries up to 'max_retries' times if parsing fails or the response is invalid.
    Returns a list of modality areas or an empty list if unsuccessful.

    :param description: The company's description text.
    :param company_name: Name of the company.
    :param azure_service: An initialized instance of AzureOpenaiService.
    :param modality_areas: A list of possible modality areas.
    :param max_retries: Maximum number of attempts before returning an empty list.
    :return: A list of modality areas as strings.
    """

    # Create initial system and user prompts to retrieve a description of modality areas
    system_prompt = create_modality_classification_prompt(company_name, modality_areas)
    user_prompt = f"Provided Company description:\n{description}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    for _ in range(max_retries):
        classification_response = azure_service.query(messages=messages)
        print(classification_response)
        # Parse the response using another chatbot prompt to get modality areas in a Python-parseable format
        system_prompt = parse_modality_classification_response(modality_areas)
        user_prompt = f"Description of modality areas:\n{classification_response}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        extraction_response = azure_service.query(messages=messages)
        # Parse the structured response to extract modality areas
        areas = parse_chatbot_response(extraction_response)
        if areas is not None and validate_classifications(areas, modality_areas):
            return areas

    return []
