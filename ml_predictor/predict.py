import os
import sys
import warnings
warnings.filterwarnings('ignore')

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import argparse
import joblib
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text

def get_db_engine():
    db_host = os.getenv("DB_HOST", "localhost")
    default_port = "5433" if db_host in ["localhost", "127.0.0.1"] else "5432"
    db_port = os.getenv("DB_PORT", default_port)
    db_name = os.getenv("DB_NAME", "football_db")
    db_user = os.getenv("DB_USER", "football_user")
    db_password = os.getenv("DB_PASSWORD", "football_pass")
    
    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return create_engine(connection_string)

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

def predict_player_value(player_id=None, player_name=None):
    model_path = os.path.join(os.path.dirname(__file__), "player_value_model.joblib")
    if not os.path.exists(model_path):
        print(f"Loi: Chua tim thay file mo hinh tai {model_path}. Vui long chay train.py truo~c!")
        return
        
    artifact = joblib.load(model_path)
    model = artifact["model"]
    feature_names = artifact["feature_names"]
    feature_cols = artifact.get("feature_cols", [])
    categorical_features = artifact["categorical_features"]
    use_log = artifact.get("use_log", False)
    
    engine = get_db_engine()
    
    if player_id:
        where_clause = f"WHERE p.player_id = {player_id}"
    elif player_name:
        where_clause = f"WHERE p.name ILIKE '%{player_name}%'"
    else:
        where_clause = "WHERE p.name ILIKE '%Haaland%' OR p.name ILIKE '%Mbappé%' OR p.name ILIKE '%Bellingham%' OR p.name ILIKE '%Kane%'"

    query = f"""
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
    {where_clause}
    ORDER BY p.player_id, s.season DESC, s.games_minutes DESC;
    """
    
    with engine.connect() as conn:
        df = pd.read_sql_query(text(query), conn)

    if df.empty:
        print(f"Khong tim thay cau thu phu hop dieu kien: {player_id or player_name}")
        return
        
    df = preprocess_input(df)
    
    print(f"\n--- DU DOAN GIA TRI CHUYEN NHUONG (AP DUNG TRONG SO PER-90 & WORLD CUP) ---")
    
    results = []
    player_groups = df.groupby("player_id")
    
    for pid, group in player_groups:
        row = group.iloc[0].copy()
        
        # Kiểm tra nếu cầu thủ thi đấu tỏa sáng ở World Cup (league_id = 1 hoặc mùa 2022/2026)
        wc_rows = group[group['stats_league_id'] == 1]
        is_wc = False
        wc_boost = 1.0
        
        if not wc_rows.empty:
            is_wc = True
            wc_row = wc_rows.iloc[0]
            wc_rating = float(wc_row['games_rating'])
            wc_g90 = float(wc_row['goals_per_90'])
            if wc_rating > 7.0 or wc_g90 > 0.5:
                # Hệ số thưởng World Cup dựa trên hiệu suất ghi bàn/90 phút và rating
                wc_boost = 1.3 + (wc_g90 * 0.25)
                row = wc_row.copy()
                
        input_data = pd.DataFrame([row])
        
        X_cat = pd.get_dummies(input_data[categorical_features], drop_first=False)
        X_num = input_data[feature_cols]
        
        X_input = pd.concat([X_num, X_cat], axis=1)
        
        for col in feature_names:
            if col not in X_input.columns:
                X_input[col] = 0
                
        X_input = X_input[feature_names]
        
        pred_raw = model.predict(X_input)[0]
        if use_log:
            predicted_value = np.expm1(pred_raw)
        else:
            predicted_value = pred_raw
            
        predicted_value = predicted_value * wc_boost
        predicted_value = max(0.0, float(predicted_value))
        
        league_str = str(row['league_name']) if pd.notnull(row['league_name']) else f"League {row['stats_league_id']}"
        if is_wc:
            league_str += " (World Cup)"

        results.append({
            "player_id": row["player_id"],
            "name": row["player_name"],
            "age": row["age"],
            "position": row["position"],
            "season": row["season"],
            "league": league_str,
            "goals_90": round(row["goals_per_90"], 2),
            "rating": row["games_rating"],
            "wc_boost": f"{wc_boost:.2f}x" if is_wc else "1.00x",
            "predicted_value_m_eur": round(predicted_value, 2)
        })
        
    res_df = pd.DataFrame(results)
    
    print("\n==========================================================================================================")
    print(f"{'ID':<8} | {'TEN CAU THU':<18} | {'TUOI':<5} | {'VI TRI':<10} | {'MUA/GIAI':<18} | {'BAN/90P':<8} | {'HE SO WC':<8} | {'DUDOAN GIA THI TRUONG'}")
    print("==========================================================================================================")
    for _, r in res_df.iterrows():
        print(f"{r['player_id']:<8} | {r['name']:<18} | {r['age']:<5} | {r['position']:<10} | {r['season']} ({r['league'][:10]}...) | {r['goals_90']:<8} | {r['wc_boost']:<8} | EUR {r['predicted_value_m_eur']:.2f}M")
    print("==========================================================================================================\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict Player Transfer Value")
    parser.add_argument("--player_id", type=int, help="ID cua cau thu can du doan")
    parser.add_argument("--name", type=str, help="Ten cua cau thu can du doan (vi du: Haaland)")
    args = parser.parse_args()
    
    predict_player_value(player_id=args.player_id, player_name=args.name)
