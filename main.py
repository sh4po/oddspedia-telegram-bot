from src.bot import TelegramBot
from src.odds_analyzer import OddsAnalyzer
from datetime import datetime

def main():
    print("🚀 Bắt đầu phân tích kèo...")
    
    # 1. Phân tích kèo
    analyzer = OddsAnalyzer()
    top_odds = analyzer.get_top_odds()
    
    # 2. Tạo tin nhắn
    message = "🎯 <b>TOP 3 KÈO TỐT NHẤT</b>\n\n"
    message += f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
    
    for i, odd in enumerate(top_odds, 1):
        message += f"🔥 <b>Kèo {i}: {odd['match']}</b>\n"
        message += f"💰 Tỷ lệ: <b>{odd['odds']}</b>\n"
        message += f"🏛 Nhà cái: {odd['bookmaker']}\n"
        message += f"📊 Phân tích: {odd['analysis']}\n"
        message += f"⏰ Thời gian: {odd['match_time']}\n\n"
    
    message += "💡 <i>Bot cập nhật tự động</i>"
    
    # 3. Gửi Telegram
    bot = TelegramBot()
    success = bot.send_message(message)
    
    if success:
        print("✅ Đã gửi báo cáo kèo!")
    else:
        print("❌ Lỗi khi gửi!")

if __name__ == "__main__":
    main()