from openai import OpenAI


API_URL = "https://gateway-test-default-gateway.spaces.kalavai.net/v1"
API_KEY = ""  # Replace with your actual API key

# point this to your vLLM API server
client = OpenAI(
    base_url=API_URL,  # change if your server runs elsewhere
    api_key=API_KEY  # vLLM ignores the key, but the client requires it
)

def list_models():
    """Fetch and display available models from the API."""
    print("Fetching available models...\n")
    
    try:
        models = client.models.list()
        
        if not models.data:
            print("No models found.")
            return
        
        print(f"Found {len(models.data)} model(s):\n")
        for model in models.data:
            print(f"- {model.id}")
        
    except Exception as e:
        print(f"Error fetching models: {e}")


if __name__ == "__main__":
    list_models()
