from src.config import Config

class OddsAnalyzer:
    def __init__(self):
        self.min_odds = Config.MIN_ODDS
        self.max_odds = Config.MAX_ODDS
        self.max_selection = Config.MAX_SELECTION
        
    def get_sample_odds(self):
        return [
            {
                'match': 'Manchester United vs Liverpool',
                'odds': 1.45,
                'bookmaker': 'Bet365',
                'match_time': '2024-01-15 20:00:00',
                'analysis': 'Phong độ ổn định, lịch sử đối đầu tốt'
            },
            {
                'match': 'Real Madrid vs Barcelona', 
                'odds': 1.62,
                'bookmaker': 'William Hill',
                'match_time': '2024-01-16 21:00:00',
                'analysis': 'Trận derby, nhiều bàn thắng'
            },
            {
                'match': 'Bayern Munich vs Dortmund',
                'odds': 1.52,
                'bookmaker': 'Pinnacle', 
                'match_time': '2024-01-17 19:30:00',
                'analysis': 'Đội nhà mạnh, sân nhà'
            }
        ]
    
    def get_top_odds(self):
        all_odds = self.get_sample_odds()
        filtered_odds = [odd for odd in all_odds if self.min_odds <= odd['odds'] <= self.max_odds]
        return filtered_odds[:self.max_selection]

if __name__ == "__main__":
    analyzer = OddsAnalyzer()
    print("🔍 Đang phân tích kèo...")
    top_odds = analyzer.get_top_odds()
    for odd in top_odds:
        print(f"⚽ {odd['match']} - Tỷ lệ: {odd['odds']}")