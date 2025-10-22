from src.bot import TelegramBot
from src.odds_analyzer import OddsAnalyzer
from datetime import datetime

def main():
    print("🚀 Bắt đầu phân tích kèo từ 3 môn thể thao...")
    
    try:
        # 1. Phân tích kèo
        analyzer = OddsAnalyzer()
        top_odds = analyzer.get_top_odds()
        
        # 2. Tạo tin nhắn chi tiết
        message = "🎯 <b>TOP 3 KÈO TỐT NHẤT - 3 MÔN THỂ THAO</b>\n\n"
        message += f"⏰ Cập nhật: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        message += f"📊 Tiêu chí: Tỷ lệ từ {analyzer.min_odds} đến {analyzer.max_odds}\n\n"
        
        for i, odd in enumerate(top_odds, 1):
            message += f"🔥 <b>Kèo {i}: {odd['match']}</b>\n"
            message += f"🎯 {odd.get('sport', '⚽ Bóng đá')} | 🏆 {odd['league']}\n"
            message += f"💰 <b>Tỷ lệ: {odd['odds']}</b> | 🏛 {odd['bookmaker']}\n"
            message += f"⏰ Thời gian: {odd['match_time']}\n"
            message += f"📈 Phân tích: {odd['analysis']}\n\n"
        
        message += "💡 <i>Dữ liệu thời gian thực từ The Odds API</i>\n"
        message += "⚠️ <i>Chỉ phân tích, không khuyến nghị đầu tư</i>"
        
        # 3. Gửi Telegram
        bot = TelegramBot()
        success = bot.send_message(message)
        
        if success:
            print("✅ Đã gửi báo cáo kèo thật!")
        else:
            print("❌ Lỗi khi gửi!")
            
        return success
        
    except Exception as e:
        error_msg = f"❌ Lỗi hệ thống: {str(e)}"
        print(error_msg)
        bot = TelegramBot()
        bot.send_message(error_msg)
        return False

if __name__ == "__main__":
    main()