"""Drill 02.3: call Azure OpenAI with your Microsoft Entra ID identity. No API key at all."""
import os

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# DefaultAzureCredential tries, in order: environment variables, managed identity,
# Azure CLI login (az login), VS Code sign-in, and more. Locally, az login is enough.
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
)
client = OpenAI(base_url=os.environ["AZURE_OPENAI_BASE_URL"], api_key=token_provider)

r = client.chat.completions.create(
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "chat"),
    messages=[{"role": "user", "content": "Say 'keyless works' and nothing else."}],
)
print(r.choices[0].message.content)
