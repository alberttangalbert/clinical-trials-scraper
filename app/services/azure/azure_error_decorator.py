from functools import wraps

def handle_azure_errors(func):
    """
    A decorator to catch and handle exceptions related to Azure OpenAI errors.
    :param func: The function to wrap.
    :return: The wrapped function with error handling.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Execute the decorated function
            return func(*args, **kwargs)
        except Exception as e:
            # Handle Azure/OpenAI-specific errors or other exceptions
            return f"Error querying Azure OpenAI: {str(e)}"

    return wrapper
