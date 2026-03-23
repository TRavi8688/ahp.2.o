import httpx
import asyncio
import os

async def test():
    base_url = "https://ke6vx29r.us-east.insforge.app"
    anon_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3OC0xMjM0LTU2NzgtOTBhYi1jZGVmMTIzNDU2NzgiLCJlbWFpbCI6ImFub25AaW5zZm9yZ2UuY29tIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM2ODI4MzF9.0uWPcUKLoQuqlU5m826bXNT5Kr-6jFSPqkaUke9Vaq8"
    
    # Try different variations
    paths = ["/chat/completion", "/api/ai/chat/completion", "/v1/chat/completions"]
    
    async with httpx.AsyncClient() as client:
        for path in paths:
            url = f"{base_url}{path}"
            print(f"Testing URL: {url}")
            headers = {
                "Authorization": f"Bearer {anon_key}",
                "apikey": anon_key,
                "Content-Type": "application/json"
            }
            payload = {
                "model": "openai/gpt-4o-mini",
                "messages": [{"role": "user", "content": "Hello"}]
            }
            try:
                resp = await client.post(url, headers=headers, json=payload)
                print(f"  Status: {resp.status_code}")
                if resp.status_code == 200:
                    print(f"  Success! Response: {resp.text[:100]}...")
            except Exception as e:
                print(f"  Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
