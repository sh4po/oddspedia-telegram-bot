import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')
    MIN_ODDS = 1.4
    MAX_ODDS = 1.65
    MAX_SELECTION = 3
    
    # The Odds API Configuration
    API_KEY = os.getenv('API_KEY', '481d04fe5a172fb6439a3cf816244eec')
    API_URL = "https://api.the-odds-api.com/v4/sports/soccer/odds"
