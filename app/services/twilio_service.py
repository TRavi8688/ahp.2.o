import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER")

def send_sms_otp(phone_number: str, otp: str):
    """
    Sends an OTP via Twilio SMS.
    Expects phone_number in E.164 format (e.g., +919876543210).
    """
    if not TWILIO_ACCOUNT_SID or TWILIO_ACCOUNT_SID == "your_twilio_sid_here":
        print(f"[MOCK SMS] Real Twilio credentials not set. OTP for {phone_number}: {otp}")
        return True

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        # Ensure phone number has country code
        if not phone_number.startswith("+"):
            phone_number = f"+91{phone_number}"
            
        message = client.messages.create(
            body=f"Your AI Health Passport (AHP) verification code is: {otp}. Valid for 10 minutes.",
            from_=TWILIO_FROM_NUMBER,
            to=phone_number
        )
        print(f"Twilio message sent: {message.sid}")
        return True
    except Exception as e:
        print(f"Twilio Error: {e}")
        return False
