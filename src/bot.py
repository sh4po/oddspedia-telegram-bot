import requests
from src.config import Config

class TelegramBot:
    def __init__(self):
        self.token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        
    def send_message(self, text):
        if not self.token or not self.chat_id:
            print("❌ Lỗi: Thiếu Telegram Bot Token hoặc Chat ID")
            return False
            
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        
        try:
            response = requests.post(url, data=payload)
            if response.status_code == 200:
                print("✅ Đã gửi tin nhắn Telegram!")
                return True
            else:
                print(f"❌ Lỗi: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Lỗi kết nối: {e}")
            return False

def test_bot():
    bot = TelegramBot()
    message = "🤖 <b>Test Bot</b>\n\nBot đã hoạt động!"
    return bot.send_message(message)

if __name__ == "__main__":
    test_bot()