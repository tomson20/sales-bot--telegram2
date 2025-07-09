import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
#STRIPE_PROVIDER_TOKEN = os.getenv("STRIPE_PROVIDER_TOKEN")
PAYZE_API_KEY = os.getenv("PAYZE_API_KEY")
PAYZE_MERCHANT_ID = os.getenv("PAYZE_MERCHANT_ID")
# თუ Sandbox-ს იყენებ, გამოიყენე Payze-ს ტესტ გასაღებები და Merchant ID
# PAYZE_API_KEY = "sandbox_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# PAYZE_MERCHANT_ID = "sandbox_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# თუ Production-ს იყენებ, გამოიყენე რეალური გასაღებები