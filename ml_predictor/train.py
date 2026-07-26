import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import joblib
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.ensemble import GradientBoostingRegressor

def get_db_engine():
    db_host = os.getenv("DB_HOST", "localhost")
    default_port = "5433" if db_host in ["localhost", "127.0.0.1"] else "5432"
    db_port = os.getenv("DB_PORT", default_port)
    db_name = os.getenv("DB_NAME", "football_db")
    db_user = os.getenv("DB_USER", "football_user")
    db_password = os.getenv("DB_PASSWORD", "football_pass")
    
    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return create_engine(connection_string)

def preprocess_features(df):
    # Ép kiểu dữ liệu số
    numeric_cols = [
        'age', 'games_appearances', 'games_lineups', 'games_minutes', 'games_rating',
        'goals_total', 'goals_assists', 'shots_total', 'shots_on', 'passes_total',
        'passes_key', 'tackles_total', 'tackles_interceptions', 'duels_total',
        'duels_won', 'dribbles_attempts', 'dribbles_success', 'fouls_drawn',
        'fouls_committed', 'cards_yellow', 'cards_red', 'penalty_scored'
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 1. TÍNH CHỈ SỐ HẠNG MỤC THEO MỖI 90 PHÚT (PER 90 METRICS)
    # Giúp so sánh công bằng giữa World Cup (ít trận) và giải VĐQG (nhiều trận)
    minutes = np.maximum(df['games_minutes'], 90) # Tránh chia cho 0
    df['goals_per_90'] = (df['goals_total'] / minutes) * 90
    df['assists_per_90'] = (df['goals_assists'] / minutes) * 90
    df['shots_per_90'] = (df['shots_total'] / minutes) * 90
    df['passes_per_90'] = (df['passes_total'] / minutes) * 90
    df['key_passes_per_90'] = (df['passes_key'] / minutes) * 90
    df['dribbles_per_90'] = (df['dribbles_success'] / minutes) * 90
    df['tackles_per_90'] = (df['tackles_total'] / minutes) * 90

    # 2. CỜ ĐÁNH DẤU VÀ HỆ SỐ TRỌNG SỐ CHO NĂM WORLD CUP (2022, 2026, League ID = 1)
    # df['is_world_cup'] đã được tải trực tiếp từ view cơ sở dữ liệu
    df['is_wc_year'] = df['stats_season'].apply(lambda x: 1 if x in [2022, 2026] else 0)

    return df

def train_model():
    print("--- 1. DOC DU LIEU HUAN LUYEN TU POSTGRESQL (ml_training_set) ---")
    engine = get_db_engine()
    query = "SELECT * FROM ml_training_set WHERE games_minutes >= 180;" # Tối thiểu 2 trận đấu
    df = pd.read_sql(query, engine)
    
    print(f"Da tai {len(df)} dong du lieu giao dich lich su kem chi so thi dau.")
    
    if df.empty:
        print("Loi: Khong tim thay du lieu trong ml_training_set!")
        return

    df = preprocess_features(df)
    
    df['target_transfer_fee_m_eur'] = pd.to_numeric(df['target_transfer_fee_m_eur'], errors='coerce').fillna(0)
    
    # Biến đổi Logarit cho giá trị giao dịch
    y = df['target_transfer_fee_m_eur']
    y_log = np.log1p(y)
    
    feature_cols = [
        'age', 'games_rating', 'is_world_cup', 'is_wc_year',
        'goals_per_90', 'assists_per_90', 'shots_per_90', 'passes_per_90',
        'key_passes_per_90', 'dribbles_per_90', 'tackles_per_90',
        'games_appearances', 'games_minutes', 'goals_total', 'goals_assists'
    ]
    
    categorical_features = ['position', 'nationality']
    
    X_cat = pd.get_dummies(df[categorical_features], drop_first=True)
    X_num = df[feature_cols]
    
    X = pd.concat([X_num, X_cat], axis=1)
    feature_names = X.columns.tolist()
    
    X_train, X_test, y_train_log, y_test_log, y_train_orig, y_test_orig = train_test_split(
        X, y_log, y, test_size=0.2, random_state=42
    )
    print(f"Kich thuoc tap Train: {len(X_train)} mau | Tap Test: {len(X_test)} mau.")
    
    print("\n--- 2. HUAN LUYEN MO HINH GRADIENT BOOSTING VOI CHỈ SỐ WORLD CUP & PER-90 ---")
    model = GradientBoostingRegressor(
        n_estimators=250,
        learning_rate=0.03,
        max_depth=5,
        subsample=0.8,
        random_state=42
    )
    
    model.fit(X_train, y_train_log)
    
    y_pred_log = model.predict(X_test)
    y_pred = np.expm1(y_pred_log)
    y_pred = np.maximum(y_pred, 0)
    
    mae = mean_absolute_error(y_test_orig, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test_orig, y_pred))
    r2 = r2_score(y_test_orig, y_pred)
    
    print("\n==============================================")
    print("      KET QUA DANH GIA MO HINH (METRICS)     ")
    print("==============================================")
    print(f" * Sai so tuyet doi trung binh (MAE) : +/- {mae:.2f} Trieu Euro")
    print(f" * Can sai so binh phuong (RMSE)     : {rmse:.2f} Trieu Euro")
    print(f" * He so xac dinh (R2 Score)         : {r2:.4f}")
    print("==============================================")
    
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1][:10]
    
    print("\nTOP 10 CHI SO ANH HUONG LON NHAT DEN GIA TRI CAU THU:")
    for rank, idx in enumerate(indices, 1):
        print(f" {rank:2d}. {feature_names[idx]:<25} : {importances[idx]*100:.2f}%")
        
    model_dir = os.path.dirname(__file__)
    model_path = os.path.join(model_dir, "player_value_model.joblib")
    
    model_artifact = {
        "model": model,
        "feature_names": feature_names,
        "feature_cols": feature_cols,
        "categorical_features": categorical_features,
        "use_log": True
    }
    
    joblib.dump(model_artifact, model_path)
    print(f"\nDa luu dong goi mo hinh thanh cong tai: {model_path}")

if __name__ == "__main__":
    train_model()
