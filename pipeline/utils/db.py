import os
import time
import psycopg2
from psycopg2.extras import Json

def get_db_connection():
    """
    Kết nối tới PostgreSQL, thử lại sau mỗi 2 giây nếu chưa sẵn sàng (tối đa 10 lần)
    """
    for attempt in range(10):
        try:
            sslmode = os.getenv("DB_SSLMODE")
            conn_args = {
                "host": os.getenv("DB_HOST", "db"),
                "port": os.getenv("DB_PORT", "5432"),
                "database": os.getenv("DB_NAME", "football_db"),
                "user": os.getenv("DB_USER", "football_user"),
                "password": os.getenv("DB_PASSWORD", "football_pass")
            }
            if sslmode:
                conn_args["sslmode"] = sslmode
            return psycopg2.connect(**conn_args)
        except psycopg2.OperationalError as e:
            if attempt == 9:
                raise e
            print(f"Database chưa sẵn sàng, đang thử lại kết nối ({attempt + 1}/10)...")
            time.sleep(2)

def save_league(conn, league_id, season, data):
    responses = data.get("response", [])
    if not responses:
        return
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO staging_leagues_raw (league_id, season, data_raw)
            VALUES (%s, %s, %s)
            ON CONFLICT (league_id, season) DO UPDATE SET data_raw = EXCLUDED.data_raw;
            """,
            (league_id, season, Json(responses[0]))
        )
        conn.commit()
    print(f"Đã lưu thông tin giải đấu {league_id} vào database.")

def save_teams(conn, league_id, season, data):
    responses = data.get("response", [])
    if not responses:
        return
    with conn.cursor() as cur:
        for item in responses:
            team_id = item.get("team", {}).get("id")
            cur.execute(
                """
                INSERT INTO staging_teams_raw (team_id, league_id, season, data_raw)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (team_id, league_id, season) DO UPDATE SET data_raw = EXCLUDED.data_raw;
                """,
                (team_id, league_id, season, Json(item))
            )
        conn.commit()
    print(f"Đã lưu {len(responses)} đội bóng của giải {league_id} vào database.")

def save_players(conn, league_id, season, data):
    responses = data.get("response", [])
    if not responses:
        return 0
    with conn.cursor() as cur:
        for item in responses:
            player_id = item.get("player", {}).get("id")
            cur.execute(
                """
                INSERT INTO staging_players_raw (player_id, league_id, season, data_raw)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (player_id, league_id, season) DO UPDATE SET data_raw = EXCLUDED.data_raw;
                """,
                (player_id, league_id, season, Json(item))
            )
        conn.commit()
    return len(responses)

def run_sql_file(conn, file_path):
    """
    Đọc và thực thi file SQL trên database.
    """
    if not os.path.exists(file_path):
        print(f"Lỗi: Không tìm thấy file SQL tại {file_path}")
        return False
        
    print(f"Đang thực thi file SQL: {file_path}...")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            sql_script = f.read()
            
        with conn.cursor() as cur:
            cur.execute(sql_script)
        conn.commit()
        print(f"Thực thi thành công {file_path}.")
        return True
    except Exception as e:
        conn.rollback()
        print(f"Lỗi khi chạy file SQL {file_path}: {e}")
        return False

def save_transfers(conn, data):
    responses = data.get("response", [])
    if not responses:
        return 0
    with conn.cursor() as cur:
        for item in responses:
            player_id = item.get("player", {}).get("id")
            if not player_id:
                continue
            cur.execute(
                """
                INSERT INTO staging_transfers_raw (player_id, data_raw)
                VALUES (%s, %s)
                ON CONFLICT (player_id) DO UPDATE SET data_raw = EXCLUDED.data_raw;
                """,
                (player_id, Json(item))
            )
        conn.commit()
    return len(responses)

def save_fixture_players(conn, fixture_id, league_id, season, data):
    responses = data.get("response", [])
    if not responses:
        return False
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO staging_fixture_players_raw (fixture_id, league_id, season, data_raw)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (fixture_id) DO UPDATE SET 
                league_id = EXCLUDED.league_id,
                season = EXCLUDED.season,
                data_raw = EXCLUDED.data_raw;
            """,
            (fixture_id, league_id, season, Json(data))
        )
        conn.commit()
    return True
