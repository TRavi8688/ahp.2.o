import httpx
import asyncio
import os
import json

BASE_URL = "http://localhost:8005/api/v1"

async def test_ride():
    print("🚦 Starting System Test Drive...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Health Check
        print("🔍 Checking API Liveness...")
        try:
            resp = await client.get(f"http://localhost:8000/health")
            print(f"✅ API Liveness: {resp.status_code}")
        except Exception as e:
            print(f"❌ API OFFLINE: {e}")
            return

        # 2. Register Test User
        print("👤 Registering Test User...")
        user_data = {
            "email": f"tester_{os.getpid()}@example.com",
            "password": "Password123!",
            "first_name": "Test",
            "last_name": "User",
            "role": "patient"
        }
        resp = await client.post(f"{BASE_URL}/auth/register", json=user_data)
        if resp.status_code != 200:
            print(f"❌ Registration Failed: {resp.text}")
            return
        print(f"✅ User Registered")

        # 3. Login
        print("🔑 Logging In...")
        login_data = {"username": user_data["email"], "password": user_data["password"]}
        resp = await client.post(f"{BASE_URL}/auth/login", data=login_data)
        if resp.status_code != 200:
            print(f"❌ Login Failed: {resp.text}")
            return
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"✅ Login Successful")

        # 4. Upload & AI Extraction (Demo Mode)
        print("📄 Testing Report Upload & AI Extraction...")
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
            print(f"❌ AI Extraction Failed: {resp.text}")
        else:
            data = resp.json()
            print(f"✅ AI Analysis: {data.get('summary')}")
            print(f"✅ Conditions: {data.get('extracted_data', {}).get('conditions')}")

        # 5. Chat with Chitti
        print("🤖 Testing Chitti AI Chat...")
        chat_data = {"text": "What should I do for my fever?", "language_code": "en-IN"}
        # Frontend uses Form data for chat
        resp = await client.post(f"{BASE_URL}/patient/chat", headers=headers, data=chat_data)
        if resp.status_code != 200:
            print(f"❌ Chat Failed: {resp.text}")
        else:
            print(f"🤖 Chitti Response: {resp.json().get('ai_text')}")

        # 6. Chat History
        print("📜 Verifying Chat History...")
        resp = await client.get(f"{BASE_URL}/patient/chat-history", headers=headers)
        if resp.status_code == 200:
            history = resp.json()
            print(f"✅ History count: {len(history)}")
        else:
            print(f"❌ History Fetch Failed: {resp.text}")

    print("\n🏁 Test Drive Complete!")

if __name__ == "__main__":
    asyncio.run(test_ride())
