import os
import json
import requests
import time
from pathlib import Path

API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL", "https://v3.football.api-sports.io").rstrip("/")

def get_headers():
    return {"x-apisports-key": API_KEY}

def save_json(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_from_api(endpoint, params=None):
    url = f"{API_URL}/{endpoint}"
    max_retries = 5
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            print(f"Calling API: {url} with params: {params} (Lượt thử {attempt + 1}/{max_retries})")
            response = requests.get(url, headers=get_headers(), params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                print(f"Lỗi kết nối nghiêm trọng sau {max_retries} lượt thử: {e}")
                raise e
            print(f"Gặp lỗi mạng ({e}). Thử lại sau {retry_delay} giây...")
            time.sleep(retry_delay)
            retry_delay *= 2

def get_cache_path(league_id, season, filename):
    return Path("data/raw") / f"league_{league_id}" / f"season_{season}" / filename

def fetch_league(league_id, season, force_refresh=False):
    cache_file = get_cache_path(league_id, season, "league.json")
    has_api_key = API_KEY and API_KEY != "your_api_key_here"
    
    # Nếu không có API Key hoặc không bắt buộc refresh, ưu tiên đọc từ cache cục bộ
    if (not has_api_key or not force_refresh) and cache_file.exists():
        if not has_api_key and force_refresh:
            print(f"Cảnh báo: Không có API key nhưng giải đấu đang active. Đọc tạm từ cache: {cache_file}")
        else:
            print(f"Đọc thông tin giải đấu {league_id} từ local JSON cache.")
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
            
    if not has_api_key:
        raise ValueError(f"Không có API Key và không có file cache cho giải đấu {league_id}.")
            
    data = fetch_from_api("leagues", {"id": league_id, "season" : season})
    save_json(data, cache_file)
    return data

def fetch_teams(league_id, season, force_refresh=False):
    cache_file = get_cache_path(league_id, season, "teams.json")
    has_api_key = API_KEY and API_KEY != "your_api_key_here"
    
    if (not has_api_key or not force_refresh) and cache_file.exists():
        if not has_api_key and force_refresh:
            print(f"Cảnh báo: Không có API key nhưng giải đấu đang active. Đọc tạm từ cache: {cache_file}")
        else:
            print(f"Đọc danh sách đội bóng của giải {league_id} từ local JSON cache.")
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
            
    if not has_api_key:
        raise ValueError(f"Không có API Key và không có file cache cho đội bóng giải {league_id}.")
            
    data = fetch_from_api("teams", {"league": league_id, "season": season})
    save_json(data, cache_file)
    return data

def fetch_players(league_id, season, page=1, force_refresh=False):
    cache_file = get_cache_path(league_id, season, f"players_page_{page}.json")
    has_api_key = API_KEY and API_KEY != "your_api_key_here"
    
    if (not has_api_key or not force_refresh) and cache_file.exists():
        if not has_api_key and force_refresh:
            print(f"Cảnh báo: Không có API key nhưng giải đấu đang active. Đọc tạm từ cache: {cache_file}")
        else:
            print(f"Đọc danh sách cầu thủ trang {page} của giải {league_id} từ local JSON cache.")
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
            
    if not has_api_key:
        raise ValueError(f"Không có API Key và không có file cache cho cầu thủ trang {page} giải {league_id}.")
            
    data = fetch_from_api("players", {"league": league_id, "season": season, "page": page})
    save_json(data, cache_file)
    return data

def fetch_transfers(team_id, force_refresh=False):
    cache_file = Path("data/raw") / "transfers" / f"team_{team_id}.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    has_api_key = API_KEY and API_KEY != "your_api_key_here"
    
    if (not has_api_key or not force_refresh) and cache_file.exists():
        if not has_api_key and force_refresh:
            print(f"Cảnh báo: Không có API key nhưng đang yêu cầu tải transfers. Đọc tạm từ cache: {cache_file}")
        else:
            print(f"Đọc lịch sử chuyển nhượng của đội {team_id} từ local JSON cache.")
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
            
    if not has_api_key:
        raise ValueError(f"Không có API Key và không có file cache transfers cho đội {team_id}.")
            
    data = fetch_from_api("transfers", {"team": team_id})
    save_json(data, cache_file)
    print("Đợi 2 giây để tránh bị chặn giới hạn tốc độ gọi API...")
    time.sleep(2)
    return data
