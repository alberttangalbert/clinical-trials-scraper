import ast
from typing import List
from app.services.azure.azure_openai_service import AzureOpenaiService
from app.utils.classification_utils import parse_chatbot_response

def get_modality_areas_from_description(
    description: str,
    azure_service: AzureOpenaiService,
    modality_areas: List[str],
    company_name: str = "",
    max_retries: int = 3
) -> List[str]:
    """
    Given a clinical trial description, queries the Azure OpenAI service to directly extract the most relevant modality area.
    A single LLM prompt is used that instructs the model to output a response that should mention the appropriate modality area
    from the provided list. If no modality area is clearly identified in the response, it retries up to 'max_retries' times,
    returning an empty list if unsuccessful.

    :param description: The clinical trial's description text.
    :param azure_service: An initialized instance of AzureOpenaiService.
    :param modality_areas: A list of possible modality areas.
    :param company_name: The name of the company conducting the trial.
    :param max_retries: Maximum number of attempts before returning an empty list.
    :return: A list of modality areas as strings.
    """
    system_prompt = (
        "You are an expert in the pharmaceutical and biotech domains, specializing in analyzing clinical trial descriptions "
        "and identifying modality areas. You are given a description of a clinical trial along with a list of possible "
        "modality areas. Based on the description, identify and return the most relevant modality area from the provided "
        "list. Do not include any additional commentary or explanation. "
        "Please think step by step and output only the final result."
    )

    modalities_str = "\n".join(modality_areas)
    user_prompt = (
        f"Company: {company_name}\n"
        f"Clinical Trial Description:\n{description}\n\n"
        f"Possible Modality Areas:\n{modalities_str}\n\n"
        "To the best of your which modality fits the description?"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    for _ in range(max_retries):
        response = azure_service.query(messages=messages)
        areas = parse_chatbot_response(response, modality_areas)
        if areas:
            return areas
    return []