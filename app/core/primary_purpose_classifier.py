from typing import List

from app.services.azure.azure_openai_service import AzureOpenaiService
from app.utils import parse_chatbot_response, validate_classifications


def create_primary_purpose_classification_prompt(company_name: str, primary_purpose_areas: List[str]) -> str:
    """
    Creates a system prompt string to identify all primary purpose areas associated with a specific company.
    
    Parameters:
        company_name (str): Name of the company.
        primary_purpose_areas (List[str]): List of possible primary purpose areas.

    Returns:
        str: A prompt for identifying the primary purpose areas.
    """
    return (
        f"You are an expert in pharmaceutical and biotech domains, specializing in analyzing clinical trial primary purposes. "
        f"You have extensive knowledge about the company {company_name} and will use all your expertise and insights to complete the task. "
        f"The task is to identify ALL the primary purpose areas that {company_name} is focused on, based on the provided trial description.\n\n"
        f"Here is the list of possible primary purpose areas: {', '.join(primary_purpose_areas)}."
        "For the primary purpose areas the company focuses on, explain how and be very very concise."
        "For primary purpose areas the company does not focus on, do not include them in your response!"
    )


def parse_primary_purpose_classification_response(primary_purpose_areas: List[str]) -> str:
    """
    Creates a parsing prompt to extract primary purpose areas from a given response.

    Parameters:
        primary_purpose_areas (List[str]): List of possible primary purpose areas.

    Returns:
        str: A parsing prompt for extracting primary purpose areas as a Python list.
    """
    return (
        "You are an expert in pharmaceutical and biotech domains, specializing in analyzing clinical trial primary purposes. "
        "You are given a description of primary purpose areas that a company is focused on and need to extract all the primary purpose areas. "
        f"Here is the list of possible primary purpose areas: {', '.join(primary_purpose_areas)}."
        "Instructions:\n"
        "1. Based on the provided description, identify and return all the primary purpose areas that match the company focus.\n"
        "2. Prioritize only including primary purpose areas from the provided list of possible primary purpose areas.\n"
        "3. Return your answer strictly as a Python list of strings (e.g., [\"Treatment\", \"Prevention\"]).\n"
        "4. Do not include any explanations, text outside the list, or commentary.\n"
        "5. If you are uncertain about a primary purpose area, make an educated guess based on the description.\n"
        "6. If no primary purpose areas match the description, return an empty list (e.g., [])."
        "Please think step by step"
    )


def get_primary_purpose_areas_from_description(
    description: str, 
    company_name: str,
    azure_service: AzureOpenaiService, 
    primary_purpose_areas: List[str],
    max_retries: int = 3
) -> List[str]:
    """
    Given a trial description, queries the Azure OpenAI service to find the primary purpose areas.
    Tries up to 'max_retries' times if parsing fails or the response is invalid.
    Returns a list of primary purpose areas or an empty list if unsuccessful.

    :param description: The trial's description text.
    :param company_name: Name of the company.
    :param azure_service: An initialized instance of AzureOpenaiService.
    :param primary_purpose_areas: A list of possible primary purpose areas.
    :param max_retries: Maximum number of attempts before returning an empty list.
    :return: A list of primary purpose areas as strings.
    """

    # Create initial system and user prompts to retrieve a description of primary purpose areas
    system_prompt = create_primary_purpose_classification_prompt(company_name, primary_purpose_areas)
    user_prompt = f"Provided Trial description:\n{description}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    for _ in range(max_retries):
        classification_response = azure_service.query(messages=messages)
        # Parse the response using another chatbot prompt to get primary purpose areas in a Python-parseable format
        system_prompt = parse_primary_purpose_classification_response(primary_purpose_areas)
        user_prompt = f"Description of primary purpose areas:\n{classification_response}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        extraction_response = azure_service.query(messages=messages)
        # Parse the structured response to extract primary purpose areas
        areas = parse_chatbot_response(extraction_response)
        if areas is not None and validate_classifications(areas, primary_purpose_areas):
            return areas

    return [] 