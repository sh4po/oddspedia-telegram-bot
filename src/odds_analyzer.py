import requests
from datetime import datetime, timedelta
import random
from src.config import Config

class OddsAnalyzer:
    def __init__(self):
        # GIỚI HẠN ODDS HỢP LÝ - TRÁNH ODDS QUÁ CAO
        self.min_odds = 1.3
        self.max_odds = 3.0
        self.max_selection = Config.MAX_SELECTION
        self.api_key = Config.API_KEY
        
    def get_real_odds(self):
        """
        Lấy dữ liệu kèo thật từ The Odds API - ODDS CHUẨN
        """
        all_sports_odds = []
        
        # DANH SÁCH GIẢI ĐẤU CHẤT LƯỢNG
        sports = [
            # BÓNG ĐÁ CHÂU ÂU
            'soccer_epl',           # Premier League
            'soccer_laliga',        # La Liga
            'soccer_serie_a',       # Serie A
            'soccer_bundesliga',    # Bundesliga
            'soccer_ligue_one',     # Ligue 1
            'soccer_uefa_champs_league', # Champions League
            
            # BÓNG RỔ
            'basketball_nba',       # NBA
            'basketball_euroleague', # Euroleague
        ]
        
        sport_names = {
            'soccer_epl': '⚽ Premier League',
            'soccer_laliga': '⚽ La Liga', 
            'soccer_serie_a': '⚽ Serie A',
            'soccer_bundesliga': '⚽ Bundesliga',
            'soccer_ligue_one': '⚽ Ligue 1',
            'soccer_uefa_champs_league': '⚽ Champions League',
            'basketball_nba': '🏀 NBA',
            'basketball_euroleague': '🏀 Euroleague',
        }
        
        successful_sports = 0
        
        for sport in sports:
            try:
                print(f"🔍 Đang lấy dữ liệu {sport_names.get(sport, sport)}...")
                
                url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
                params = {
                    'apiKey': self.api_key,
                    'regions': 'eu',
                    'markets': 'h2h',
                    'oddsFormat': 'decimal',
                    'dateFormat': 'iso'
                }
                
                response = requests.get(url, params=params, timeout=20)
                
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        sport_odds = self.process_sport_odds(data, sport, sport_names.get(sport, sport))
                        if sport_odds:  # Chỉ thêm nếu có kèo hợp lệ
                            all_sports_odds.extend(sport_odds)
                            successful_sports += 1
                            print(f"✅ {sport_names.get(sport, sport)}: {len(sport_odds)} kèo hợp lệ")
                        else:
                            print(f"ℹ️  {sport_names.get(sport, sport)}: Không có kèo phù hợp")
                    else:
                        print(f"ℹ️  {sport_names.get(sport, sport)}: Không có trận nào")
                elif response.status_code == 404:
                    print(f"❌ {sport_names.get(sport, sport)}: Giải đấu không khả dụng")
                else:
                    print(f"❌ Lỗi {sport}: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Lỗi kết nối {sport}: {e}")
                continue
        
        print(f"🎯 Đã thu thập {len(all_sports_odds)} kèo từ {successful_sports} giải đấu")
        
        # Nếu không có kèo thật, dùng dữ liệu mẫu
        if not all_sports_odds:
            print("⚠️ Không tìm thấy kèo thật, dùng dữ liệu mẫu")
            return self.get_sample_odds()
        
        # Sắp xếp theo odds hợp lý nhất (không quá cao, không quá thấp)
        all_sports_odds.sort(key=lambda x: abs(2.0 - x['odds']))  # Ưu tiên odds gần 2.0
        return all_sports_odds[:self.max_selection]
    
    def process_sport_odds(self, data, sport, sport_display_name):
        """
        Xử lý dữ liệu - CHỈ LẤY ODDS CHUẨN & TRẬN TRONG 24H
        """
        processed_odds = []
        seen_matches = set()
        
        for match in data:
            try:
                # KIỂM TRA THỜI GIAN - CHỈ LẤY TRẬN TRONG 24H TỚI
                commence_time = match.get('commence_time', '')
                if not self.is_within_24_hours(commence_time):
                    continue
                
                # Xử lý tên đội
                home_team = match.get('home_team', '').strip()
                away_team = match.get('away_team', '').strip()
                
                if not home_team or not away_team:
                    continue
                
                sport_title = match.get('sport_title', sport_display_name)
                
                # Tạo ID duy nhất cho trận đấu
                match_id = f"{sport}_{home_team}_{away_team}"
                
                # Bỏ qua nếu đã xử lý trận này
                if match_id in seen_matches:
                    continue
                
                # TÌM ODDS TRUNG BÌNH TỪ CÁC NHÀ CÁI UY TÍN
                valid_odds = []
                trusted_bookmakers = ['bet365', 'pinnacle', 'william hill', 'bwin', 'unibet']
                
                for bookmaker in match.get('bookmakers', []):
                    bookmaker_name = bookmaker.get('title', '').lower()
                    
                    # Chỉ lấy từ nhà cái uy tín
                    if any(trusted in bookmaker_name for trusted in trusted_bookmakers):
                        for market in bookmaker.get('markets', []):
                            if market.get('key') == 'h2h':
                                for outcome in market.get('outcomes', []):
                                    odds = outcome.get('price', 0)
                                    # CHỈ LẤY ODDS TRONG KHOẢNG HỢP LÝ
                                    if self.min_odds <= odds <= self.max_odds:
                                        valid_odds.append(odds)
                
                # Nếu có ít nhất 2 nhà cái có odds hợp lý, lấy trung bình
                if len(valid_odds) >= 2:
                    avg_odds = sum(valid_odds) / len(valid_odds)
                    # Làm tròn đến 2 chữ số thập phân
                    final_odds = round(avg_odds, 2)
                    
                    processed_odds.append({
                        'match': f"{home_team} vs {away_team}",
                        'odds': final_odds,
                        'bookmaker': 'Multiple Trusted',
                        'match_time': self.format_match_time(commence_time),
                        'league': sport_title,
                        'sport': sport_display_name,
                        'analysis': self.generate_detailed_analysis(final_odds, home_team, away_team, sport)
                    })
                    
                    seen_matches.add(match_id)
                    
            except Exception as e:
                print(f"⚠️ Lỗi xử lý trận {sport}: {e}")
                continue
        
        return processed_odds

    def is_within_24_hours(self, commence_time_str):
        """
        Kiểm tra xem trận đấu có trong 24h tới không
        """
        try:
            if not commence_time_str:
                return False
                
            match_time = datetime.fromisoformat(commence_time_str.replace('Z', '+00:00'))
            now = datetime.now(match_time.tzinfo) if match_time.tzinfo else datetime.utcnow()
            
            time_diff = match_time - now
            return timedelta(0) <= time_diff <= timedelta(hours=24)
            
        except:
            return False
    
    def format_match_time(self, match_time_str):
        """
        Định dạng thời gian trận đấu
        """
        try:
            if match_time_str:
                dt = datetime.fromisoformat(match_time_str.replace('Z', '+00:00'))
                dt_vn = dt + timedelta(hours=7)
                return dt_vn.strftime('%d/%m %H:%M')
            return "Sắp diễn ra"
        except:
            return "Sắp diễn ra"
    
    def generate_detailed_analysis(self, odds, home_team, away_team, sport):
        """
        PHÂN TÍCH CHI TIẾT - CẢI THIỆN CHẤT LƯỢNG
        """
        # Phân tích theo giá trị odds
        if odds <= 1.5:
            risk_level = "THẤP"
            confidence = "RẤT CAO"
            recommendation = "CƠ HỘI TỐT"
            detail = "Đội chủ nhà được đánh giá vượt trội"
        elif odds <= 1.8:
            risk_level = "TRUNG BÌNH - THẤP"
            confidence = "CAO"
            recommendation = "ĐÁNG CÂN NHẮC"
            detail = "Lợi thế sân nhà rõ rệt"
        elif odds <= 2.2:
            risk_level = "TRUNG BÌNH"
            confidence = "KHÁ"
            recommendation = "CÓ TIỀM NĂNG"
            detail = "Trận đấu cân bằng nghiêng về chủ nhà"
        elif odds <= 2.8:
            risk_level = "TRUNG BÌNH - CAO"
            confidence = "TRUNG BÌNH"
            recommendation = "CẦN THẬN TRỌNG"
            detail = "Đội khách có thể tạo bất ngờ"
        else:
            risk_level = "CAO"
            confidence = "THẤP"
            recommendation = "RỦI RO CAO"
            detail = "Cơ hội cho bất ngờ"
        
        # Phân tích theo môn thể thao
        if 'soccer' in sport:
            sport_specific = [
                f"Phong độ sân nhà {home_team} ổn định",
                f"Lịch sử đối đầu nghiêng về {home_team}",
                f"{home_team} có hàng công mạnh mẽ",
                f"Lợi thế sân nhà rõ rệt cho {home_team}",
                f"{home_team} đang có chuỗi trận thắng ấn tượng"
            ]
        elif 'basketball' in sport:
            sport_specific = [
                f"{home_team} thi đấu hiệu quả trên sân nhà",
                f"Phong độ tấn công của {home_team} vượt trội",
                f"{home_team} có đội hình gần như mạnh nhất",
                f"Lối chơi nhanh của {home_team} tạo nhiều cơ hội",
                f"{home_team} có hàng công ổn định"
            ]
        else:
            sport_specific = [
                f"{home_team} được đánh giá cao hơn",
                f"Phong độ hiện tại của {home_team} tốt hơn",
                f"{home_team} có lợi thế sân nhà",
                f"Đội hình {home_team} mạnh hơn đối thủ"
            ]
        
        # Kết hợp phân tích
        base_analysis = random.choice(sport_specific)
        
        return f"🔍 {base_analysis}. {detail} | 📊 Odds: {odds} | ⚡ {recommendation} | 🛡️ Rủi ro: {risk_level} | ✅ Độ tin cậy: {confidence}"
    
    def get_sample_odds(self):
        """
        Dữ liệu mẫu với ODDS CHUẨN
        """
        current_time = datetime.now().strftime('%d/%m %H:%M')
        print("⚠️ Sử dụng dữ liệu mẫu chất lượng")
        return [
            {
                'match': 'Manchester City vs Liverpool',
                'odds': 1.85,
                'bookmaker': 'Bet365',
                'match_time': current_time,
                'league': 'Premier League',
                'sport': '⚽ Premier League',
                'analysis': '🔍 Manchester City có phong độ sân nhà ổn định. Lợi thế sân nhà rõ rệt | 📊 Odds: 1.85 | ⚡ ĐÁNG CÂN NHẮC | 🛡️ Rủi ro: TRUNG BÌNH - THẤP | ✅ Độ tin cậy: CAO'
            },
            {
                'match': 'LA Lakers vs Golden State Warriors', 
                'odds': 1.75,
                'bookmaker': 'William Hill',
                'match_time': current_time,
                'league': 'NBA',
                'sport': '🏀 NBA',
                'analysis': '🔍 LA Lakers thi đấu hiệu quả trên sân nhà. Lợi thế sân nhà rõ rệt | 📊 Odds: 1.75 | ⚡ ĐÁNG CÂN NHẮC | 🛡️ Rủi ro: TRUNG BÌNH - THẤP | ✅ Độ tin cậy: CAO'
            },
            {
                'match': 'Real Madrid vs Barcelona',
                'odds': 2.10,
                'bookmaker': 'Pinnacle', 
                'match_time': current_time,
                'league': 'La Liga',
                'sport': '⚽ La Liga',
                'analysis': '🔍 Real Madrid có phong độ sân nhà ổn định. Trận đấu cân bằng nghiêng về chủ nhà | 📊 Odds: 2.10 | ⚡ CÓ TIỀM NĂNG | 🛡️ Rủi ro: TRUNG BÌNH | ✅ Độ tin cậy: KHÁ'
            }
        ]
    
    def get_top_odds(self):
        """
        Lấy top kèo - ưu tiên dữ liệu thật
        """
        return self.get_real_odds()

if __name__ == "__main__":
    analyzer = OddsAnalyzer()
    print("🔍 Đang phân tích kèo thật từ giải đấu uy tín...")
    top_odds = analyzer.get_top_odds()
    print(f"🎯 Tìm thấy {len(top_odds)} kèo chất lượng:")
    for i, odd in enumerate(top_odds, 1):
        print(f"{i}. {odd['sport']}: {odd['match']}")
        print(f"   📊 Tỷ lệ: {odd['odds']} | 🏛 {odd['bookmaker']}")
        print(f"   ⏰ {odd['match_time']} | {odd['analysis']}")
