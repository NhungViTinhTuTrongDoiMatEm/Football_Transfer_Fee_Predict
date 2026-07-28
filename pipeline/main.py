import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

from utils.api import fetch_league, fetch_teams, fetch_players, fetch_transfers
from utils.db import get_db_connection, save_league, save_teams, save_players, save_transfers

def main():
    # 1. Đọc file cấu hình targets
    targets_file = os.path.join(os.path.dirname(__file__), "targets.json")
    with open(targets_file, "r", encoding="utf-8") as f:
        targets = json.load(f)
        
    print(f"Đã tải {len(targets)} mục tiêu cào dữ liệu.")

    # 2. Kết nối tới database
    conn = get_db_connection()
    
    processed_team_ids = set()
    
    # 3. Chạy qua từng mục tiêu cào
    try:
        for idx, target in enumerate(targets):
            league_id = target.get("league_id")
            season = target.get("season")
            name = target.get("name")
            active = target.get("active", False)
            
            # Nếu target là active (đang diễn ra) hoặc không có file JSON cục bộ, ta ép buộc tải lại từ API
            # Nếu target không active, fetch_* sẽ tự động đọc cache nếu file đã tồn tại
            force_refresh = active
            
            print(f"\n--- Bắt đầu xử lý giải đấu: {name} (Mùa giải: {season}) ---")
            
            # A. Cào & lưu Giải đấu
            league_data = fetch_league(league_id, season, force_refresh)
            save_league(conn, league_id, season, league_data)
            
            # B. Cào & lưu Đội bóng
            teams_data = fetch_teams(league_id, season, force_refresh)
            save_teams(conn, league_id, season, teams_data)
            
            # Thu thập các team_id để cào transfers sau
            for item in teams_data.get("response", []):
                tid = item.get("team", {}).get("id")
                if tid:
                    processed_team_ids.add(tid)
            
            # C. Cào & lưu Cầu thủ (xử lý phân trang trực tiếp trong main)
            page = 1
            total_players = 0
            while True:
                players_data = fetch_players(league_id, season, page, force_refresh)
                saved_count = save_players(conn, league_id, season, players_data)
                total_players += saved_count
                
                # Đọc thông tin phân trang từ API response
                paging = players_data.get("paging", {})
                current_page = paging.get("current", 1)
                total_pages = paging.get("total", 1)
                
                print(f"Trang {current_page}/{total_pages}: Đã lưu {saved_count} cầu thủ.")
                
                # Dừng nếu đã tải hết các trang hoặc API không trả về thêm cầu thủ
                if current_page >= total_pages or saved_count == 0:
                    break
                    
                page += 1
                
                # Nếu tải trực tiếp từ internet, ta chờ 2s (Đã tối ưu cho tài khoản Paid)
                if force_refresh:
                    print("Đợi 2 giây trước khi cào trang tiếp theo...")
                    time.sleep(2)
                    
            print(f"Hoàn thành giải đấu {name}. Tổng cộng lưu/cập nhật {total_players} cầu thủ.")
            
        # D. Cào lịch sử chuyển nhượng cho các câu lạc bộ đã thu thập
        if processed_team_ids:
            print(f"\n--- Bắt đầu cào lịch sử chuyển nhượng cho {len(processed_team_ids)} đội bóng ---")
            for idx, team_id in enumerate(sorted(processed_team_ids)):
                print(f"[{idx+1}/{len(processed_team_ids)}] Đang xử lý đội {team_id}...")
                try:
                    transfers_data = fetch_transfers(team_id, force_refresh)
                    saved_count = save_transfers(conn, transfers_data)
                    print(f"Đội {team_id}: Đã lưu chuyển nhượng của {saved_count} cầu thủ.")
                except Exception as e:
                    print(f"Lỗi khi cào transfers cho đội {team_id}: {e}")
            
        print("\n==============================================")
        print("   HOÀN THÀNH TOÀN BỘ QUÁ TRÌNH ELT PIPELINE (E & L)  ")
        print("==============================================")
        
    finally:
        if conn:
            conn.close()
            print("Đã đóng kết nối database.")

if __name__ == "__main__":
    main()
