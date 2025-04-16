from typing import List

from app.services.azure.azure_openai_service import AzureOpenaiService
from app.utils import parse_chatbot_response, validate_classifications


def create_outcome_classification_prompt(company_name: str, outcome_areas: List[str]) -> str:
    """
    Creates a system prompt string to identify all outcome areas associated with a specific company.
    
    Parameters:
        company_name (str): Name of the company.
        outcome_areas (List[str]): List of possible outcome areas.

    Returns:
        str: A prompt for identifying the outcome areas.
    """
    return (
        f"You are an expert in pharmaceutical and biotech domains, specializing in analyzing clinical trial outcomes. "
        f"You have extensive knowledge about the company {company_name} and will use all your expertise and insights to complete the task. "
        f"The task is to identify ALL the outcome areas that {company_name} is focused on, based on the provided trial description.\n\n"
        f"Here is the list of possible outcome areas: {', '.join(outcome_areas)}."
        "For the outcome areas the company focuses on, explain how and be very very concise."
        "For outcome areas the company does not focus on, do not include them in your response!"
    )


def parse_outcome_classification_response(outcome_areas: List[str]) -> str:
    """
    Creates a parsing prompt to extract outcome areas from a given response.

    Parameters:
        outcome_areas (List[str]): List of possible outcome areas.

    Returns:
        str: A parsing prompt for extracting outcome areas as a Python list.
    """
    return (
        "You are an expert in pharmaceutical and biotech domains, specializing in analyzing clinical trial outcomes. "
        "You are given a description of outcome areas that a company is focused on and need to extract all the outcome areas. "
        f"Here is the list of possible outcome areas: {', '.join(outcome_areas)}."
        "Instructions:\n"
        "1. Based on the provided description, identify and return all the outcome areas that match the company focus.\n"
        "2. Prioritize only including outcome areas from the provided list of possible outcome areas.\n"
        "3. Return your answer strictly as a Python list of strings (e.g., [\"Clinical Outcomes\", \"Safety/Tolerability Outcomes\"]).\n"
        "4. Do not include any explanations, text outside the list, or commentary.\n"
        "5. If you are uncertain about an outcome area, make an educated guess based on the description.\n"
        "6. If no outcome areas match the description, return an empty list (e.g., [])."
        "Please think step by step"
    )


def get_outcome_areas_from_description(
    description: str, 
    company_name: str,
    azure_service: AzureOpenaiService, 
    outcome_areas: List[str],
    max_retries: int = 3
) -> List[str]:
    """
    Given a trial description, queries the Azure OpenAI service to find the outcome areas.
    Tries up to 'max_retries' times if parsing fails or the response is invalid.
    Returns a list of outcome areas or an empty list if unsuccessful.

    :param description: The trial's description text.
    :param company_name: Name of the company.
    :param azure_service: An initialized instance of AzureOpenaiService.
    :param outcome_areas: A list of possible outcome areas.
    :param max_retries: Maximum number of attempts before returning an empty list.
    :return: A list of outcome areas as strings.
    """

    # Create initial system and user prompts to retrieve a description of outcome areas
    system_prompt = create_outcome_classification_prompt(company_name, outcome_areas)
    user_prompt = f"Provided Trial description:\n{description}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    for _ in range(max_retries):
        classification_response = azure_service.query(messages=messages)
        # Parse the response using another chatbot prompt to get outcome areas in a Python-parseable format
        system_prompt = parse_outcome_classification_response(outcome_areas)
        user_prompt = f"Description of outcome areas:\n{classification_response}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        extraction_response = azure_service.query(messages=messages)
        # Parse the structured response to extract outcome areas
        areas = parse_chatbot_response(extraction_response)
        if areas is not None and validate_classifications(areas, outcome_areas):
            return areas

    return [] 