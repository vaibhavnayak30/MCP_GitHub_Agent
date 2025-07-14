import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from azure.identity import get_bearer_token_provider, EnvironmentCredential

# Load env variables from .env into environment
load_dotenv()

def get_llm():
    """Initializes and returns the AzureChatOpenAI instance."""
    azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    chat_deployment_name = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

    token_provider = get_bearer_token_provider(
        EnvironmentCredential(), "https://cognitiveservices.azure.com/.default"
    )

    llm = AzureChatOpenAI(
        azure_endpoint=azure_openai_endpoint,
        api_version=openai_api_version,
        azure_ad_token_provider=token_provider,
        deployment_name=chat_deployment_name,
    )
    return llm