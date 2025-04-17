import ast
import re
from typing import List

def clean_text(text: str) -> str:
    """
    Cleans text by converting to lowercase and replacing non-letter characters with spaces.
    
    Args:
        text (str): Text to clean.
        
    Returns:
        str: Cleaned text.
    """
    # Convert to lowercase
    text = text.lower()
    # Replace non-letter characters with spaces
    text = re.sub(r'[^a-z]', ' ', text)
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_chatbot_response(response: str, possible_classifications: List[str]) -> List[str]:
    """
    Parses the chatbot's response to find all occurrences of the known indication or modality areas.
    It loops over each possible classification and checks if it is mentioned in the response.
    The matching is case-insensitive and handles various text formats.
    
    If found, it adds the classification to the returned list. This avoids needing to evaluate
    the response as a literal Python list.

    Args:
        response (str): Chatbot response as a string.
        possible_classifications (List[str]): List of valid possible indication or modality areas.

    Returns:
        List[str]: List of indication areas found in the chatbot response.
    
    Examples:
        >>> response = "The description is about risedronate, a drug primarily used to treat metabolic bone diseases. These conditions fall under the category of: Cardiovascular/Metabolic"
        >>> possible_classifications = [
        ...   "Oncology", "Neurology/Psychiatry", "Cardiovascular/Metabolic", "Immunology/Autoimmune",
        ...   "Infectious Diseases", "Hematology", "Gastrointestinal/Hepatology", "Dermatology",
        ...   "Ophthalmology", "Respiratory", "Urology/Renal", "Pain Management/Anesthetics"
        ... ]
        >>> parse_chatbot_response(response, possible_classifications)
        ['Cardiovascular/Metabolic']
    """
    # Clean the response text
    cleaned_response = clean_text(response)
    
    found = []
    for classification in possible_classifications:
        # Clean the classification text
        cleaned_classification = clean_text(classification)
        
        # Check if the cleaned classification is in the cleaned response
        if cleaned_classification in cleaned_response:
            # Add the original classification (not the cleaned version) to the results
            found.append(classification)
    
    return found