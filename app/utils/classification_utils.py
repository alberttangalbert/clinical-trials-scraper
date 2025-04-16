import ast
from typing import List

def parse_chatbot_response(response: str) -> List[str]:
    """
    Parses the chatbot's response into a list of modality or indication areas.
    The response should be a Python list in string form, e.g. ["Protein/Monoclonal Antibodies", "Small molecules and Natural Products"].
    Returns an empty list if parsing fails or the format is invalid.

    Args:
        response (str): Chatbot response as a string.

    Returns:
        List[str]: Parsed list of modality or indication areas.
        
    Examples:
        >>> parse_chatbot_response("['Protein/Monoclonal Antibodies', 'Small molecules and Natural Products']")
        ['Protein/Monoclonal Antibodies', 'Small molecules and Natural Products']

        >>> parse_chatbot_response("['Peptides/Cyclic', 'Vaccines']")
        ['Peptides/Cyclic', 'Vaccines']

        >>> parse_chatbot_response("[]")
        []

        >>> parse_chatbot_response("Invalid input")
    """
    try:
        data = ast.literal_eval(response)
        if isinstance(data, list) and all(isinstance(item, str) for item in data):
            return data
    except (SyntaxError, ValueError):
        return None  
    return None


def validate_classifications(classifications: List[str], possible_classifications: List[str]) -> bool:
    """
    Validates that each classification in the returned classifications is in the provided possible_classifications list.

    :param classifications: The list of classifications returned by a model or function.
    :param possible_classifications: The list of valid possible classifications.
    :return: True if all classifications are valid, False otherwise.

    Examples:
        >>> validate_classifications(['Pain Management/Anesthetics', 'Dermatology'], 
        ...                           ['Oncology', 'Neurology/Psychiatry', 'Cardiovascular/Metabolic', 'Immunology/Autoimmune', 
        ...                            'Pain Management/Anesthetics', 'Dermatology'])
        True

        >>> validate_classifications(['Protein/Monoclonal Antibodies', 'Small molecules and Natural Products'], 
        ...                           ['Protein/Monoclonal Antibodies', 'Small molecules and Natural Products', 'Peptides/Cyclic'])
        True
        
        >>> validate_classifications(['Protein/Others', 'Peptides/Pegylated'], 
        ...                           ['Protein/Monoclonal Antibodies', 'Small molecules and Natural Products', 'Peptides/Amino Acids with More than 40 Residues'])
        False
        
    """
    return all(classification in possible_classifications for classification in classifications)