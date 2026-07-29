import os
import sys
import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, text

app = FastAPI(title="Football Player Stats & Value Predictor API")

# Cấu hình encoding utf-8 trên Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Kết nối database
def get_db_engine():
    db_host = os.getenv("DB_HOST", "db")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "football_db")
    db_user = os.getenv("DB_USER", "football_user")
    db_password = os.getenv("DB_PASSWORD", "football_pass")
    
    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return create_engine(connection_string)

engine = get_db_engine()

# Load model ML
MODEL_PATH = "/app/ml_predictor/player_value_model.joblib"
model_artifact = None

if os.path.exists(MODEL_PATH):
    try:
        model_artifact = joblib.load(MODEL_PATH)
        print("Loaded ML model artifact successfully.")
    except Exception as e:
        print(f"Error loading ML model: {e}")
else:
    print(f"Warning: Model file not found at {MODEL_PATH}")

def preprocess_input(df):
    numeric_cols = [
        'age', 'games_appearances', 'games_lineups', 'games_minutes', 'games_rating',
        'goals_total', 'goals_assists', 'shots_total', 'shots_on', 'passes_total',
        'passes_key', 'tackles_total', 'tackles_interceptions', 'duels_total',
        'duels_won', 'dribbles_attempts', 'dribbles_success', 'fouls_drawn',
        'fouls_committed', 'cards_yellow', 'cards_red', 'penalty_scored'
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    minutes = np.maximum(df['games_minutes'], 90)
    df['goals_per_90'] = (df['goals_total'] / minutes) * 90
    df['assists_per_90'] = (df['goals_assists'] / minutes) * 90
    df['shots_per_90'] = (df['shots_total'] / minutes) * 90
    df['passes_per_90'] = (df['passes_total'] / minutes) * 90
    df['key_passes_per_90'] = (df['passes_key'] / minutes) * 90
    df['dribbles_per_90'] = (df['dribbles_success'] / minutes) * 90
    df['tackles_per_90'] = (df['tackles_total'] / minutes) * 90

    df['is_world_cup'] = df['stats_league_id'].apply(lambda x: 1 if str(x) == '1' else 0)
    df['is_wc_year'] = df['season'].apply(lambda x: 1 if str(x) in ['2022', '2026'] else 0)

    return df

@app.get("/api/search")
def search_players(q: str = Query(..., min_length=2)):
    query_str = """
        SELECT player_id, name, nationality, age, photo
        FROM dim_players
        WHERE name ILIKE :q
        ORDER BY name
        LIMIT 15;
    """
    with engine.connect() as conn:
        result = conn.execute(text(query_str), {"q": f"%{q}%"})
        players = [dict(row._mapping) for row in result]
    return players

@app.get("/api/player/{player_id}")
def get_player_data(player_id: int):
    # 1. Lấy thông tin cá nhân cầu thủ & câu lạc bộ mới nhất của họ
    profile_query = """
        SELECT p.player_id, p.name, p.nationality, p.age, p.photo,
               t.name AS team_name, t.logo AS team_logo
        FROM dim_players p
        LEFT JOIN (
            SELECT DISTINCT ON (player_id) player_id, team_id
            FROM fact_player_statistics
            ORDER BY player_id, season DESC
        ) last_team ON p.player_id = last_team.player_id
        LEFT JOIN dim_teams t ON last_team.team_id = t.team_id
        WHERE p.player_id = :player_id;
    """
    
    # 2. Lấy chỉ số thống kê thi đấu của các mùa giải
    stats_query = """
        SELECT s.*, l.name AS league_name, l.logo AS league_logo, t.name AS team_name, t.logo AS team_logo
        FROM fact_player_statistics s
        LEFT JOIN dim_leagues l ON s.league_id = l.league_id
        LEFT JOIN dim_teams t ON s.team_id = t.team_id
        WHERE s.player_id = :player_id
        ORDER BY s.season DESC, s.games_appearances DESC;
    """
    
    with engine.connect() as conn:
        prof_res = conn.execute(text(profile_query), {"player_id": player_id}).first()
        if not prof_res:
            raise HTTPException(status_code=404, detail="Player not found")
            
        profile = dict(prof_res._mapping)
        
        stats_res = conn.execute(text(stats_query), {"player_id": player_id})
        stats = [dict(row._mapping) for row in stats_res]
        
    return {
        "profile": profile,
        "stats": stats
    }

@app.get("/api/player/{player_id}/predict")
def predict_value(player_id: int, season: int):
    if not model_artifact:
        return {"error": "Mô hình dự đoán giá trị chưa được huấn luyện hoặc không khả dụng."}
        
    query = """
    SELECT 
        p.player_id,
        p.name AS player_name,
        p.age,
        p.nationality,
        s.league_id AS stats_league_id,
        l.name AS league_name,
        s.games_position AS position,
        s.season,
        s.games_appearances,
        s.games_lineups,
        s.games_minutes,
        s.games_rating,
        s.goals_total,
        s.goals_assists,
        s.shots_total,
        s.shots_on,
        s.passes_total,
        s.passes_key,
        s.tackles_total,
        s.tackles_interceptions,
        s.duels_total,
        s.duels_won,
        s.dribbles_attempts,
        s.dribbles_success,
        s.fouls_drawn,
        s.fouls_committed,
        s.cards_yellow,
        s.cards_red,
        s.penalty_scored
    FROM dim_players p
    JOIN fact_player_statistics s ON p.player_id = s.player_id
    LEFT JOIN dim_leagues l ON s.league_id = l.league_id
    WHERE p.player_id = :player_id AND s.season = :season;
    """
    
    with engine.connect() as conn:
        df = pd.read_sql_query(text(query), conn, params={"player_id": player_id, "season": season})
        
    if df.empty:
        raise HTTPException(status_code=404, detail="Không tìm thấy chỉ số thi đấu của cầu thủ trong mùa giải được chọn.")
        
    df = preprocess_input(df)
    
    # Chuẩn bị dữ liệu đầu vào cho mô hình
    model = model_artifact["model"]
    feature_names = model_artifact["feature_names"]
    feature_cols = model_artifact["feature_cols"]
    categorical_features = model_artifact["categorical_features"]
    use_log = model_artifact.get("use_log", False)
    
    # Gom nhóm theo giải đấu và kiểm tra hiệu ứng World Cup
    results = []
    
    # Kiểm tra nếu có thi đấu World Cup
    wc_rows = df[df['stats_league_id'] == 1]
    is_wc = False
    wc_boost = 1.0
    
    main_row = df.iloc[0].copy()
    
    if not wc_rows.empty:
        is_wc = True
        wc_row = wc_rows.iloc[0]
        wc_rating = float(wc_row['games_rating'])
        wc_g90 = float(wc_row['goals_per_90'])
        if wc_rating > 7.0 or wc_g90 > 0.5:
            wc_boost = 1.3 + (wc_g90 * 0.25)
            main_row = wc_row.copy()
            
    input_data = pd.DataFrame([main_row])
    
    X_cat = pd.get_dummies(input_data[categorical_features], drop_first=False)
    X_num = input_data[feature_cols]
    
    X_input = pd.concat([X_num, X_cat], axis=1)
    
    # Đảm bảo đầy đủ các cột đặc trưng một-nóng (One-Hot Columns) như lúc train
    missing_cols = {col: 0 for col in feature_names if col not in X_input.columns}
    if missing_cols:
        X_input = pd.concat([X_input, pd.DataFrame([missing_cols], index=X_input.index)], axis=1)
        
    X_input = X_input[feature_names]
    
    pred_raw = model.predict(X_input)[0]
    if use_log:
        predicted_value = np.expm1(pred_raw)
    else:
        predicted_value = pred_raw
        
    predicted_value = predicted_value * wc_boost
    predicted_value = max(0.0, float(predicted_value))
    
    return {
        "player_id": int(main_row["player_id"]),
        "name": main_row["player_name"],
        "season": int(main_row["season"]),
        "wc_boost": round(wc_boost, 2),
        "is_wc": is_wc,
        "predicted_value_m_eur": round(predicted_value, 2)
    }

# Phục vụ Frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")
