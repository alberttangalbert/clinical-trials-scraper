from openai import AzureOpenAI
from openai.types.chat import ChatCompletion

from app.config import Config
from app.services.azure.azure_error_decorator import handle_azure_errors

class AzureOpenaiService:
    def __init__(self):
        """
        Initializes the AzureOpenaiService instance.
        """
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            api_key=Config.AZURE_OPENAI_API_KEY,
            api_version=Config.AZURE_OPENAI_API_VERSION,
            azure_endpoint=Config.AZURE_OPENAI_API_ENDPOINT,
        )
        self.deployment_name = Config.AZURE_OPENAI_DEPLOYMENT_NAME

    @handle_azure_errors
    def query(self, messages: list[dict]) -> str:
        """
        Sends a list of messages to Azure OpenAI and retrieves the response.

        :param messages: A list of message dictionaries in the format [{"role": "user", "content": "message"}].
        :param temperature: The temperature for the model's response (higher = more creative).
        :return: The content of the assistant's response.
        """
        # Make the API request
        response: ChatCompletion = self.client.chat.completions.create(
            model=self.deployment_name,
            messages=messages,
        )
        # Return the assistant's response
        return response.choices[0].message.content.strip()