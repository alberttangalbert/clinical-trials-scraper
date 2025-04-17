import ast
from typing import List
from app.services.azure.azure_openai_service import AzureOpenaiService
from app.utils.classification_utils import parse_chatbot_response

def get_indication_areas_from_description(
    description: str,
    azure_service: AzureOpenaiService,
    indication_areas: List[str],
    company_name: str = "",
    max_retries: int = 3
) -> List[str]:
    """
    Given a clinical trial description, queries the Azure OpenAI service to directly extract relevant indication areas.
    A single LLM prompt is used that instructs the model to output a response that should mention one or more of the
    provided indication areas. If the response does not clearly include any of these indication areas, it retries up to
    'max_retries' times, returning an empty list if unsuccessful.

    :param description: The clinical trial's description text.
    :param azure_service: An initialized instance of AzureOpenaiService.
    :param indication_areas: A list of possible indication areas.
    :param company_name: The name of the company conducting the trial.
    :param max_retries: Maximum number of attempts before returning an empty list.
    :return: A list of indication areas as strings.
    """
    system_prompt = (
        "You are an expert in the pharmaceutical and biotech domains, specializing in analyzing clinical trial descriptions "
        "and identifying indication areas. You are given a description of a clinical trial along with a list of possible "
        "indication areas. Based on the description, identify and return the most relevant indication area from the provided "
        "list. Do not include any additional commentary or explanation. "
        "Please think step by step and output only the final result."
    )

    # Prepare the user prompt similar to a conversation example:
    # "Assess the relative bioavailability of the risedronate 20 mg DR tablet ... which indication is the description?"
    # Followed by the list of possible indications.
    indications_str = "\n".join(indication_areas)
    user_prompt = (
        f"Company: {company_name}\n"
        f"Clinical Trial Description:\n{description}\n\n"
        f"Possible Indication Areas:\n{indications_str}\n\n"
        "To the best of your knowledge which indication fits the description?"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    for _ in range(max_retries):
        response = azure_service.query(messages=messages)
        # Use the revised parser that loops over the possible indication areas and extracts those present
        areas = parse_chatbot_response(response, indication_areas)
        if areas:
            return areas
    return []