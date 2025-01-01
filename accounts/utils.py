import os
from dotenv import load_dotenv
from twilio.rest import Client

def send_verification(phone_number, verification_code):
    load_dotenv()
    account_sid = str(os.environ["TWILIO_SID"])
    auth_token = str(os.environ["TWILIO_TOKEN"])
    sender_number = str(os.environ["TWILIO_NUMBER"])
    
    client = Client(account_sid, auth_token)
    client.messages.create(
        body = f"Your GigLoom Verification Code is:{verification_code}",
        from_= sender_number,
        to = phone_number,
    )