import httpx
import asyncio
import os
import json

BASE_URL = "http://localhost:8000/api/v1"

async def test_ride():
    print("STARTING SYSTEM TEST DRIVE...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Health Check
        print("CHECKING API LIVENESS...")
        try:
            resp = await client.get(f"http://localhost:8000/health")
            print(f"API Liveness: {resp.status_code}")
        except Exception as e:
            print(f"API OFFLINE: {e}")
            return

        # 2. Register Test User
        print("REGISTERING TEST USER...")
        user_data = {
            "email": f"tester_{os.getpid()}@example.com",
            "password": "Password123!",
            "first_name": "Test",
            "last_name": "User",
            "role": "patient"
        }
        resp = await client.post(f"{BASE_URL}/auth/register", json=user_data)
        if resp.status_code != 200:
            print(f"Registration Failed: {resp.text}")
            return
        print(f"User Registered")

        # 3. Login
        print("LOGGING IN...")
        login_data = {"username": user_data["email"], "password": user_data["password"]}
        resp = await client.post(f"{BASE_URL}/auth/login", data=login_data)
        if resp.status_code != 200:
            print(f"Login Failed: {resp.text}")
            return
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"Login Successful")

        # 4. Upload & AI Extraction (Demo Mode)
        print("TESTING REPORT UPLOAD & AI EXTRACTION...")
        # Create a dummy file
        dummy_file = "test_report.jpg"
        with open(dummy_file, "w") as f:
            f.write("Clinical Report: Patient has mild viral fever and was prescribed Paracetamol.")
        
        with open(dummy_file, "rb") as f:
            resp = await client.post(
                f"{BASE_URL}/patient/upload-report",
                headers=headers,
                files={"file": (dummy_file, f, "image/jpeg")}
            )
        
        if resp.status_code != 200:
            print(f"AI Extraction Failed: {resp.text}")
        else:
            data = resp.json()
            if data:
                print(f"AI Analysis: {data.get('summary', 'Pending...')}")
                # Ensure extracted_data is handled safely even if None
                extracted = data.get('extracted_data') or {}
                print(f"Conditions: {extracted.get('conditions', 'N/A')}")
            else:
                print("AI Extraction: Response received (Empty)")

        # 5. Chat with Chitti
        print("TESTING CHITTI AI CHAT...")
        chat_data = {"text": "What should I do for my fever?", "language_code": "en-IN"}
        # Frontend uses Form data for chat
        resp = await client.post(f"{BASE_URL}/patient/chat", headers=headers, data=chat_data)
        if resp.status_code != 200:
            print(f"Chat Failed: {resp.text}")
        else:
            print(f"Chitti Response: {resp.json().get('ai_text')}")

        # 6. Chat History
        print("VERIFYING CHAT HISTORY...")
        resp = await client.get(f"{BASE_URL}/patient/chat-history", headers=headers)
        if resp.status_code == 200:
            history = resp.json()
            print(f"History count: {len(history)}")
        else:
            print(f"History Fetch Failed: {resp.text}")

    print("\nTEST DRIVE COMPLETE!")

if __name__ == "__main__":
    asyncio.run(test_ride())
