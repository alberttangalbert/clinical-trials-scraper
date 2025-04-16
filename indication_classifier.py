from typing import List

from app.services.azure.azure_openai_service import AzureOpenaiService
from app.utils import parse_chatbot_response, validate_classifications


def create_indication_classification_prompt(company_name: str, indication_areas: List[str]) -> str:
    """
    Creates a system prompt string to identify all indication areas associated with a specific company.
    
    Parameters:
        company_name (str): Name of the company.
        indication_areas (List[str]): List of possible indication areas.

    Returns:
        str: A prompt for identifying the indication areas.
    """
    return (
        f"You are an expert in pharmaceutical and biotech domains, specializing in analyzing company profiles and identifying indication focus areas. "
        f"You have extensive knowledge about the company {company_name} and will use all your expertise and insights to complete the task. "
        f"The task is to identify ALL the indication areas that {company_name} is focused on, based on the provided company description.\n\n"
        f"Here is the list of possible indication areas: {', '.join(indication_areas)}."
        "For the indication areas the company focuses on, explain how and be very very concise."
        "For indication areas the company does not focus on, do not include them in your response!"
    )

def parse_indication_classification_response(indication_areas: List[str]) -> str:
    """
    Creates a parsing prompt to extract indication areas from a given response.

    Parameters:
        prompt (str): The system prompt with the company description and indication areas.
        indication_areas (List[str]): List of possible indication areas.

    Returns:
        str: A parsing prompt for extracting indication areas as a Python list.
    """
    return (
        "You are an expert in pharmaceutical and biotech domains, specializing in analyzing company profiles and identifying indication focus areas. "
        "You are given a description of indication areas that a company is focused on and need to extract all the indication areas. "
        f"Here is the list of possible indication areas: {', '.join(indication_areas)}."
        "Instructions:\n"
        "1. Based on the provided description, identify and return all the indication areas that match the company focus.\n"
        "2. Prioritize only including indication areas from the provided list of possible indication areas.\n"
        "3. Return your answer strictly as a Python list of strings (e.g., [\"Oncology\", \"Neurology\"]).\n"
        "4. Do not include any explanations, text outside the list, or commentary.\n"
        "5. If you are uncertain about an indication area, make an educated guess based on the description.\n"
        "6. If no indication areas match the description, return an empty list (e.g., [])."
        "Please think step by step"
    )

def get_indication_areas_from_description(
    description: str, 
    company_name: str,
    azure_service: AzureOpenaiService, 
    indication_areas: List[str],
    max_retries: int = 3
) -> List[str]:
    """
    Given a company description, queries the Azure OpenAI service to find the indication areas.
    Tries up to 'max_retries' times if parsing fails or the response is invalid.
    Returns a list of indication areas or an empty list if unsuccessful.

    :param description: The company's description text.
    :param azure_service: An initialized instance of AzureOpenaiService.
    :param max_retries: Maximum number of attempts before returning an empty list.
    :return: A list of indication areas as strings.
    """

    # Create initial system and user prompts to retrieve a description of indication areas
    system_prompt = create_indication_classification_prompt(company_name, indication_areas)
    user_prompt = f"Provided Company description:\n{description}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    for _ in range(max_retries):
        classification_response = azure_service.query(messages=messages)
        # Parse the response using another chatbot prompt to get indication areas in a python parseable format
        system_prompt = parse_indication_classification_response(indication_areas)
        user_prompt = f"Description of indication areas:\n{classification_response}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        extraction_response = azure_service.query(messages=messages)
        # Parse the structured response to extract indication areas
        areas = parse_chatbot_response(extraction_response)
        if areas is not None and validate_classifications(areas, indication_areas):
            return areas

    return []
