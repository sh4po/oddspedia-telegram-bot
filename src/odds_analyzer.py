import requests
from datetime import datetime, timedelta
import random
from src.config import Config

class OddsAnalyzer:
    def __init__(self):
        # BỎ GIỚI HẠN ODDS - lấy mọi odds
        self.min_odds = 1.01  # Giữ tối thiểu nhưng rất thấp
        self.max_odds = 100.0  # Giữ tối đa nhưng rất cao
        self.max_selection = Config.MAX_SELECTION
        self.api_key = Config.API_KEY
        
    def get_real_odds(self):
        """
        Lấy dữ liệu kèo thật từ The Odds API - ĐA DẠNG GIẢI ĐẤU
        """
        all_sports_odds = []
        
        # DANH SÁCH GIẢI ĐẤU ĐA DẠNG
        sports = [
            # BÓNG ĐÁ
            'soccer',               # Tổng hợp
            'soccer_epl',           # Premier League
            'soccer_laliga',        # La Liga
            'soccer_serie_a',       # Serie A
            'soccer_bundesliga',    # Bundesliga
            'soccer_ligue_one',     # Ligue 1
            'soccer_uefa_champs_league', # Champions League
            
            # BÓNG RỔ - NHIỀU GIẢI
            'basketball_nba',       # NBA
            'basketball_euroleague', # Euroleague
            'basketball_wnba',      # WNBA
            'basketball_ncaab',     # NCAA Men's
            
            # TENNIS THAY THẾ (nếu ATP lỗi)
            'tennis_wta',           # Tennis WTA
            'americanfootball_nfl', # NFL (thay thế tennis nếu cần)
            'baseball_mlb'          # MLB (thay thế tennis nếu cần)
        ]
        
        sport_names = {
            'soccer': '⚽ Bóng đá',
            'soccer_epl': '⚽ Premier League',
            'soccer_laliga': '⚽ La Liga', 
            'soccer_serie_a': '⚽ Serie A',
            'soccer_bundesliga': '⚽ Bundesliga',
            'soccer_ligue_one': '⚽ Ligue 1',
            'soccer_uefa_champs_league': '⚽ Champions League',
            'basketball_nba': '🏀 NBA',
            'basketball_euroleague': '🏀 Euroleague',
            'basketball_wnba': '🏀 WNBA',
            'basketball_ncaab': '🏀 NCAA',
            'tennis_wta': '🎾 Tennis WTA',
            'americanfootball_nfl': '🏈 NFL',
            'baseball_mlb': '⚾ MLB'
        }
        
        successful_sports = 0
        
        for sport in sports:
            try:
                print(f"🔍 Đang lấy dữ liệu {sport_names.get(sport, sport)}...")
                
                url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
                params = {
                    'apiKey': self.api_key,
                    'regions': 'eu,uk,us',
                    'markets': 'h2h',
                    'oddsFormat': 'decimal',
                    'dateFormat': 'iso'
                }
                
                response = requests.get(url, params=params, timeout=20)
                
                if response.status_code == 200:
                    data = response.json()
                    if data:  # Chỉ xử lý nếu có dữ liệu
                        sport_odds = self.process_sport_odds(data, sport, sport_names.get(sport, sport))
                        all_sports_odds.extend(sport_odds)
                        successful_sports += 1
                        print(f"✅ Tìm thấy {len(sport_odds)} kèo {sport_names.get(sport, sport)}")
                    else:
                        print(f"ℹ️  {sport_names.get(sport, sport)}: Không có trận nào")
                elif response.status_code == 404:
                    print(f"❌ {sport_names.get(sport, sport)}: Giải đấu không khả dụng (404)")
                else:
                    print(f"❌ Lỗi {sport}: {response.status_code}")
                    
                # Dừng nếu đã có đủ dữ liệu từ 4-5 giải
                if successful_sports >= 5 and len(all_sports_odds) >= 8:
                    break
                    
            except Exception as e:
                print(f"❌ Lỗi kết nối {sport}: {e}")
                continue
        
        print(f"🎯 Đã thu thập từ {successful_sports} giải đấu, tổng {len(all_sports_odds)} kèo")
        
        # Nếu không có kèo thật, dùng dữ liệu mẫu
        if not all_sports_odds:
            print("⚠️ Không tìm thấy kèo thật, dùng dữ liệu mẫu")
            return self.get_sample_odds()
        
        # Sắp xếp và chọn top 3 từ tất cả giải đấu
        all_sports_odds.sort(key=lambda x: x['odds'], reverse=True)
        return all_sports_odds[:self.max_selection]
    
    def process_sport_odds(self, data, sport, sport_display_name):
        """
        Xử lý dữ liệu cho từng giải đấu - CHỈ LẤY TRẬN TRONG 24H TỚI
        """
        processed_odds = []
        seen_matches = set()
        
        for match in data:
            try:
                # KIỂM TRA THỜI GIAN - CHỈ LẤY TRẬN TRONG 24H TỚI
                commence_time = match.get('commence_time', '')
                if not self.is_within_24_hours(commence_time):
                    continue
                
                # Xử lý tên đội cho các môn khác nhau
                home_team = match.get('home_team', '').strip()
                away_team = match.get('away_team', '').strip()
                
                # Nếu không có home/away team (tennis), sử dụng các trường khác
                if not home_team or not away_team:
                    # Thử các trường khác cho tennis
                    competitors = match.get('competitors', [])
                    if len(competitors) >= 2:
                        home_team = competitors[0].get('name', 'Player 1')
                        away_team = competitors[1].get('name', 'Player 2')
                    else:
                        continue
                
                sport_title = match.get('sport_title', sport_display_name)
                
                # Tạo ID duy nhất cho trận đấu
                match_id = f"{sport}_{home_team}_{away_team}"
                
                # Bỏ qua nếu đã xử lý trận này
                if match_id in seen_matches:
                    continue
                
                # Tìm tỷ lệ TỐT NHẤT cho trận này - BỎ GIỚI HẠN ODDS
                best_odds = None
                best_bookmaker = None
                
                for bookmaker in match.get('bookmakers', []):
                    bookmaker_name = bookmaker.get('title', 'Unknown')
                    
                    for market in bookmaker.get('markets', []):
                        if market.get('key') == 'h2h':
                            for outcome in market.get('outcomes', []):
                                odds = outcome.get('price', 0)
                                
                                # BỎ GIỚI HẠN ODDS - LẤY MỌI ODDS
                                # Chỉ kiểm tra odds hợp lệ (lớn hơn 1)
                                if odds >= 1.0:
                                    # Chọn tỷ lệ tốt nhất (cao nhất)
                                    if best_odds is None or odds > best_odds:
                                        best_odds = odds
                                        best_bookmaker = bookmaker_name
                
                # Nếu tìm thấy kèo phù hợp cho trận này
                if best_odds is not None:
                    processed_odds.append({
                        'match': f"{home_team} vs {away_team}",
                        'odds': best_odds,
                        'bookmaker': best_bookmaker,
                        'match_time': self.format_match_time(commence_time),
                        'league': sport_title,
                        'sport': sport_display_name,
                        'analysis': self.generate_analysis(best_odds, home_team, away_team, sport)
                    })
                    
                    # Đánh dấu trận đã xử lý
                    seen_matches.add(match_id)
                    
                # Dừng khi đã thu thập đủ 3 trận cho mỗi giải
                if len(processed_odds) >= 3:
                    break
                    
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
                
            # Chuyển đổi thời gian
            match_time = datetime.fromisoformat(commence_time_str.replace('Z', '+00:00'))
            now = datetime.now(match_time.tzinfo) if match_time.tzinfo else datetime.utcnow()
            
            # Tính khoảng cách thời gian
            time_diff = match_time - now
            
            # Chỉ lấy trận trong 24h tới (0 đến 24 giờ)
            return timedelta(0) <= time_diff <= timedelta(hours=24)
            
        except Exception as e:
            print(f"⚠️ Lỗi kiểm tra thời gian: {e}")
            return False
    
    def format_match_time(self, match_time_str):
        """
        Định dạng thời gian trận đấu
        """
        try:
            if match_time_str:
                dt = datetime.fromisoformat(match_time_str.replace('Z', '+00:00'))
                dt_vn = dt + timedelta(hours=7)
                return dt_vn.strftime('%d/%m/%Y %H:%M')
            return "Chưa xác định"
        except:
            return "Chưa xác định"
    
    def generate_analysis(self, odds, home_team, away_team, sport):
        """
        Tạo phân tích CHI TIẾT dựa trên odds và thông tin trận đấu
        """
        # Phân tích dựa trên giá trị odds
        if odds <= 1.5:
            strength = "RẤT MẠNH"
            confidence = "cao"
            recommendation = "nên xem xét"
        elif odds <= 2.0:
            strength = "MẠNH" 
            confidence = "khá cao"
            recommendation = "có tiềm năng"
        elif odds <= 3.0:
            strength = "TƯƠNG ĐỐI"
            confidence = "trung bình"
            recommendation = "cần cân nhắc"
        else:
            strength = "CÂN BẰNG"
            confidence = "thấp"
            recommendation = "có thể rủi ro"
        
        # Phân tích theo môn thể thao
        if 'soccer' in sport:
            base_analysis = [
                f"{home_team} {strength} trước {away_team}",
                f"Tỷ lệ {odds} cho thấy {home_team} có lợi thế {confidence}",
                f"Phong độ sân nhà của {home_team} {recommendation}",
                f"{home_team} vs {away_team}: odds {odds} {recommendation} đầu tư",
                f"Phân tích: {home_team} có {confidence} cơ hội thắng"
            ]
        elif 'basketball' in sport:
            base_analysis = [
                f"{home_team} {strength} trên sân nhà",
                f"NBA: {home_team} có odds {odds} {recommendation}",
                f"Phong độ tấn công của {home_team} {confidence}",
                f"{home_team} vs {away_team}: tỷ lệ {odds} {recommendation}",
                f"Phân tích NBA: {home_team} có lợi thế {strength.lower()}"
            ]
        elif 'tennis' in sport:
            base_analysis = [
                f"Tay vợt {home_team} {strength}",
                f"Tennis: {home_team} có odds {odds} {recommendation}",
                f"Phong độ gần đây của {home_team} {confidence}",
                f"{home_team} vs {away_team}: tỷ lệ {odds} {recommendation}",
                f"Phân tích tennis: {home_team} có ưu thế {strength.lower()}"
            ]
        else:
            base_analysis = [
                f"{home_team} {strength} trước đối thủ",
                f"Tỷ lệ {odds} cho thấy cơ hội {confidence}",
                f"{home_team} vs {away_team}: {recommendation} theo odds {odds}",
                f"Phân tích: {home_team} có triển vọng {confidence}",
                f"Odds {odds} {recommendation} cho {home_team}"
            ]
        
        return random.choice(base_analysis)
    
    def get_sample_odds(self):
        """
        Dữ liệu mẫu dự phòng - ĐA DẠNG GIẢI ĐẤU
        """
        current_time = datetime.now().strftime('%d/%m/%Y %H:%M')
        print("⚠️ Sử dụng dữ liệu mẫu đa giải đấu")
        return [
            {
                'match': 'Manchester United vs Liverpool',
                'odds': 2.10,  # Odds đa dạng
                'bookmaker': 'Bet365',
                'match_time': current_time,
                'league': 'Premier League',
                'sport': '⚽ Premier League',
                'analysis': 'Trận derby nước Anh - cả hai đều có cơ hội'
            },
            {
                'match': 'LA Lakers vs Boston Celtics', 
                'odds': 1.85,  # Odds đa dạng
                'bookmaker': 'William Hill',
                'match_time': current_time,
                'league': 'NBA',
                'sport': '🏀 NBA',
                'analysis': 'Classic NBA rivalry - Lakers có lợi thế sân nhà'
            },
            {
                'match': 'Barcelona vs Real Madrid',
                'odds': 2.45,  # Odds đa dạng
                'bookmaker': 'Pinnacle', 
                'match_time': current_time,
                'league': 'La Liga',
                'sport': '⚽ La Liga',
                'analysis': 'El Clásico - trận đấu cân bằng'
            }
        ]
    
    def get_top_odds(self):
        """
        Lấy top kèo - ưu tiên dữ liệu thật
        """
        return self.get_real_odds()

if __name__ == "__main__":
    analyzer = OddsAnalyzer()
    print("🔍 Đang phân tích kèo thật từ đa giải đấu...")
    top_odds = analyzer.get_top_odds()
    print(f"🎯 Tìm thấy {len(top_odds)} kèo:")
    for i, odd in enumerate(top_odds, 1):
        print(f"{i}. {odd['sport']}: {odd['match']}")
        print(f"   📊 Tỷ lệ: {odd['odds']} | 🏛 {odd['bookmaker']}")
        print(f"   ⏰ {odd['match_time']} | {odd['analysis']}")
