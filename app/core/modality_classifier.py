import ast
from typing import List
from app.utils import parse_chatbot_response, validate_classifications

def get_modality_areas_from_description(
    description: str,
    azure_service,  # Expected to be an instance of AzureOpenaiService
    modality_areas: List[str],
    max_retries: int = 3
) -> List[str]:
    """
    Given a clinical trial description, queries the Azure OpenAI service to directly extract relevant modality areas.
    A single LLM prompt is used that instructs to output a Python list containing only modality areas
    present in the provided modality_areas list. If parsing fails, it retries up to 'max_retries' times,
    returning an empty list if unsuccessful.

    :param description: The clinical trial's description text.
    :param azure_service: An initialized instance of AzureOpenaiService.
    :param modality_areas: A list of possible modality areas.
    :param max_retries: Maximum number of attempts before returning an empty list.
    :return: A list of modality areas as strings.
    """
    system_prompt = (
        "You are an expert in pharmaceutical and biotech domains, specializing in analyzing clinical trial descriptions "
        "and identifying modality areas. You are given a description of a clinical trial along with a list of possible "
        "modality areas. Based on the description, identify and return all relevant modality areas strictly as a Python "
        "list of strings (e.g., [\"Protein/Monoclonal Antibodies\", \"Small molecules and Natural Products\"]). "
        "Include only modality areas from the provided list. If no modality areas match, return an empty list (i.e., []). "
        "Do not include any additional commentary or explanation. Here is the list of possible modality areas: "
        f"{', '.join(modality_areas)}.\n"
        "Please think step by step and output only the final list."
    )
    
    user_prompt = f"Clinical Trial Description:\n{description}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    for _ in range(max_retries):
        response = azure_service.query(messages=messages)
        areas = parse_chatbot_response(response)
        if areas is not None and validate_classifications(areas, modality_areas):
            return areas
    return []
