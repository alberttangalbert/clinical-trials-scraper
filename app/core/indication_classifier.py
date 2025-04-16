import ast
from typing import List
from app.services.azure.azure_openai_service import AzureOpenaiService
from app.utils import parse_chatbot_response, validate_classifications

def get_indication_areas_from_description(
    description: str,
    azure_service: AzureOpenaiService,
    indication_areas: List[str],
    max_retries: int = 3
) -> List[str]:
    """
    Given a clinical trial description, queries the Azure OpenAI service to directly extract relevant indication areas.
    A single LLM prompt is used that instructs the model to output a Python list containing only indication areas
    present in the provided indication_areas list. If parsing fails, it retries up to 'max_retries' times,
    returning an empty list if unsuccessful.

    :param description: The clinical trial's description text.
    :param azure_service: An initialized instance of AzureOpenaiService.
    :param indication_areas: A list of possible indication areas.
    :param max_retries: Maximum number of attempts before returning an empty list.
    :return: A list of indication areas as strings.
    """
    system_prompt = (
        "You are an expert in pharmaceutical and biotech domains, specializing in analyzing clinical trial descriptions "
        "and identifying indication areas. You are given a description of a clinical trial along with a list of possible "
        "indication areas. Based on the description, identify and return all relevant indication areas strictly as a Python "
        "list of strings (e.g., [\"Oncology\", \"Neurology\"]). "
        "Include only indication areas from the provided list. If no indication areas match, return an empty list (i.e., []). "
        "Do not include any additional commentary or explanation. Here is the list of possible indication areas: "
        f"{', '.join(indication_areas)}.\n"
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
        if areas is not None and validate_classifications(areas, indication_areas):
            return areas
    return []