import os
from openai import AzureOpenAI
from openai.types.chat import ChatCompletion
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import openai

from app.config import Config
from app.services.azure.azure_error_decorator import handle_azure_errors

class AzureOpenaiService:
    def __init__(self):
        """
        Initializes the AzureOpenaiService instance with multiple endpoint support.
        """
        self.endpoints = [
            {
                "api_key": getattr(Config, "AZURE_OPENAI_API_KEY", os.getenv("AZURE_OPENAI_API_KEY")),
                "api_version": getattr(Config, "AZURE_OPENAI_API_VERSION", os.getenv("AZURE_OPENAI_API_VERSION")),
                "azure_endpoint": getattr(Config, "AZURE_OPENAI_API_ENDPOINT", os.getenv("AZURE_OPENAI_API_ENDPOINT"))
            },
            {
                "api_key": os.getenv("AZURE_OPENAI_API_KEY_0"),
                "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
                "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT_0")
            },
            {
                "api_key": os.getenv("AZURE_OPENAI_API_KEY_1"),
                "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
                "azure_endpoint": os.getenv("AZURE_OPENAI_ENDPOINT_1")
            }
        ]
        self.deployment_name = getattr(Config, "AZURE_OPENAI_DEPLOYMENT_NAME", os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"))

    @handle_azure_errors
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APIError))
    )
    def query(self, messages: list[dict]) -> str:
        """
        Sends a list of messages to Azure OpenAI with retry and fallback.

        :param messages: List of message dicts [{"role": "user", "content": "..."}]
        :return: Model response content
        """
        last_exception = None

        for endpoint in self.endpoints:
            try:
                client = AzureOpenAI(
                    api_key=endpoint["api_key"],
                    api_version=endpoint["api_version"],
                    azure_endpoint=endpoint["azure_endpoint"]
                )
                response: ChatCompletion = client.chat.completions.create(
                    model=self.deployment_name,
                    messages=messages,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                last_exception = e
                continue

        raise last_exception