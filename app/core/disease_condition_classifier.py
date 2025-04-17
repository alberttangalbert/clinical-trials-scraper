import json
from typing import List, Dict, Tuple
from app.services.azure.azure_openai_service import AzureOpenaiService
from app.utils import parse_chatbot_response

def load_disease_conditions() -> Tuple[List[str], Dict[str, List[str]]]:
    """
    Load the disease conditions from the JSON file and return:
    1. List of top-level categories
    2. Dictionary mapping categories to their specific conditions
    
    :return: Tuple of (categories, category_to_conditions)
    """
    with open("data/config/disease_conditions.json", "r") as f:
        disease_data = json.load(f)
    
    categories = list(disease_data.keys())
    category_to_conditions = {
        category: list(conditions.keys())
        for category, conditions in disease_data.items()
    }
    
    return categories, category_to_conditions

def get_disease_condition_from_description(
    description: str,
    azure_service: AzureOpenaiService,
    company_name: str = "",
    max_retries: int = 3
) -> List[str]:
    """
    Given a clinical trial description, queries the Azure OpenAI service to classify the disease condition
    in two steps: first identifying the top-level category, then the specific condition within that category.
    
    :param description: The clinical trial's description text.
    :param azure_service: An initialized instance of AzureOpenaiService.
    :param company_name: The name of the company conducting the trial.
    :param max_retries: Maximum number of attempts before returning an empty list.
    :return: A list containing the category and specific condition, or empty list if classification fails.
    """
    # Load disease conditions
    categories, category_to_conditions = load_disease_conditions()
    
    # Step 1: Classify the top-level category
    category_system_prompt = (
        "You are an expert in pharmaceutical and biotech domains, specializing in analyzing clinical trial descriptions "
        "and identifying disease categories. You are given a description of a clinical trial along with a list of possible "
        "disease categories. Based on the description, identify the most relevant disease category from the provided list. "
        "Do not use any other categories, even if they seem relevant. "
        "If no category from the provided list matches, return an empty list. "
        "Do not include any additional commentary or explanation."
    )

    category_user_prompt = (
        f"Company: {company_name}\n"
        f"Clinical Trial Description:\n{description}\n\n"
        f"Possible Disease Categories:\n{chr(10).join(categories)}\n\n"
        "Which disease category fits the description?"
    )

    category_messages = [
        {"role": "system", "content": category_system_prompt},
        {"role": "user", "content": category_user_prompt}
    ]

    # Try to classify the category
    for _ in range(max_retries):
        category_response = azure_service.query(messages=category_messages)
        categories_found = parse_chatbot_response(category_response, categories)
        
        if categories_found and categories_found[0] in categories:
            category = categories_found[0]  # Take the first (and should be only) category
            break
    else:
        return []  # Return empty if we couldn't classify the category

    # Step 2: Classify the specific condition within the category
    conditions = category_to_conditions[category]
    condition_system_prompt = (
        "You are an expert in pharmaceutical and biotech domains, specializing in analyzing clinical trial descriptions "
        "and identifying specific disease conditions. You are given a description of a clinical trial along with a list of possible "
        f"specific conditions within the {category} category. Based on the description, identify the most relevant specific condition "
        "from the provided list. Do not use any other conditions, even if they seem relevant. "
        "If no condition from the provided list matches, return an empty list. "
        "Do not include any additional commentary or explanation."
    )

    condition_user_prompt = (
        f"Company: {company_name}\n"
        f"Clinical Trial Description:\n{description}\n"
        f"Category: {category}\n\n"
        f"Possible Conditions in {category}:\n{chr(10).join(conditions)}\n\n"
        "Which specific condition fits the description?"
    )

    condition_messages = [
        {"role": "system", "content": condition_system_prompt},
        {"role": "user", "content": condition_user_prompt}
    ]

    # Try to classify the specific condition
    for _ in range(max_retries):
        condition_response = azure_service.query(messages=condition_messages)
        conditions_found = parse_chatbot_response(condition_response, conditions)
        
        if conditions_found and conditions_found[0] in conditions:
            return [category, conditions_found[0]]  # Return both category and specific condition

    return [category]  # Return just the category if we couldn't classify the specific condition 