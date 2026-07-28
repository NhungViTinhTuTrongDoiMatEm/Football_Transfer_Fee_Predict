import os
import json
import sys
from dotenv import load_dotenv

load_dotenv()

from utils.api import fetch_recent_fixtures, fetch_fixture_player_stats
from utils.db import get_db_connection, save_fixture_players

def main():
    # 1. Đọc file cấu hình targets
    targets_file = os.path.join(os.path.dirname(__file__), "targets.json")
    with open(targets_file, "r", encoding="utf-8") as f:
        targets = json.load(f)
        
    print(f"Đã tải {len(targets)} mục tiêu cào dữ liệu.")

    # 2. Kết nối tới database
    conn = get_db_connection()
    
    print("\n==============================================")
    print("   KICH HOAT CHE DO CAO THEO TRAN DAU HANG TUAN (WEEKLY MODE)  ")
    print("==============================================")
    
    # Lấy các giải đấu đang diễn ra từ targets.json
    active_targets = [t for t in targets if t.get("active", False)]
    if not active_targets:
        # Fallback lấy các giải năm 2025/2026
        active_targets = [t for t in targets if t.get("season", 0) >= 2025]
        
    print(f"Phat hien {len(active_targets)} giai dau dang hoat dong de cao fixtures.")
    
    total_fixtures_saved = 0
    try:
        for target in active_targets:
            league_id = target.get("league_id")
            season = target.get("season")
            name = target.get("name")
            
            print(f"\n--- Tim tran dau gan day cua giai: {name} (Mua giai: {season}) ---")
            try:
                # Cào danh sách trận đấu trong 7 ngày qua
                fixtures_data = fetch_recent_fixtures(league_id, season, days=7, force_refresh=True)
                fixtures = fixtures_data.get("response", [])
                print(f"Tim thay {len(fixtures)} tran dau.")
                
                for f_item in fixtures:
                    fixture = f_item.get("fixture", {})
                    fixture_id = fixture.get("id")
                    status = fixture.get("status", {}).get("short")
                    
                    # Chỉ cào nếu trận đấu đã kết thúc
                    if status in ["FT", "AET", "PEN"]:
                        home_name = f_item.get("teams", {}).get("home", {}).get("name")
                        away_name = f_item.get("teams", {}).get("away", {}).get("name")
                        print(f"Dang tai chi tiet tran ID: {fixture_id} ({home_name} vs {away_name})...")
                        
                        try:
                            player_stats = fetch_fixture_player_stats(fixture_id, force_refresh=True)
                            if save_fixture_players(conn, fixture_id, league_id, season, player_stats):
                                total_fixtures_saved += 1
                        except Exception as e:
                            print(f"Loi khi cao chi tiet tran {fixture_id}: {e}")
            except Exception as e:
                print(f"Loi khi lay fixtures cho giai {name}: {e}")
                
        print(f"\nHoan tat cao tuan. Tong so tran da luu: {total_fixtures_saved}")
    finally:
        if conn:
            conn.close()
            print("Da dong ket noi database.")

if __name__ == "__main__":
    main()
