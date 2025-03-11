from google.generativeai import configure, list_models
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the API
configure(api_key=os.getenv("GOOGLE_API_KEY"))

# List available models
print("Available models:")
models = list_models()
for model in models:
    print(f"- {model.name}") 