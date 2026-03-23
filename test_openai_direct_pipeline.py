import os
import httpx
import asyncio

# Setup your API key as an environment variable, or hardcode here temporarily for testing.
# WARNING: Do not commit hardcoded API keys to version control.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key_here")

# You can also use Groq or Gemini endpoints if you want to test them instead.
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

async def test_ai_pipeline(prompt_text: str):
    """
    An isolated function to test AI prompt requests directly.
    Touches NO internal databases, Redis queues, or cloud infrastructure.
    """
    print(f"--- Sending Prompt ---\n{prompt_text}\n----------------------")
    
    if OPENAI_API_KEY == "your_openai_api_key_here":
        print("WARNING: Please set the OPENAI_API_KEY environment variable or hardcode it in the script to run.")
        return

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-4-turbo-preview", # or "gpt-3.5-turbo"
        "messages": [
            {"role": "system", "content": "You are a helpful medical assistant. Provide concise answers."},
            {"role": "user", "content": prompt_text}
        ],
        "max_tokens": 512,
        "temperature": 0.3
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print("Calling OpenAI API...")
            response = await client.post(OPENAI_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            message_content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            
            print("\n--- Response Received ---")
            print(message_content)
            print("\n--- Token Usage ---")
            print(f"Prompt Tokens:     {usage.get('prompt_tokens', 0)}")
            print(f"Completion Tokens: {usage.get('completion_tokens', 0)}")
            print(f"Total Tokens:      {usage.get('total_tokens', 0)}")
            print("-------------------------")
            
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Test Prompt
    sample_prompt = "Explain the difference between Type 1 and Type 2 diabetes briefly for a patient."
    
    # Run the async pipeline
    asyncio.run(test_ai_pipeline(sample_prompt))
