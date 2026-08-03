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
    
    # 1. ÁNH XẠ VỊ TRÍ CẦU THỦ THÀNH 4 NHÓM CHÍNH
    def get_pos_group(pos):
        if pos in ['Attacker', 'Forward']:
            return 'Attacker'
        elif pos == 'Midfielder':
            return 'Midfielder'
        elif pos == 'Defender':
            return 'Defender'
        elif pos == 'Goalkeeper':
            return 'Goalkeeper'
        return 'Attacker' # Mặc định dự phòng
        
    df['pos_group'] = df['position'].apply(get_pos_group)
    
    position_groups = ['Attacker', 'Midfielder', 'Defender', 'Goalkeeper']
    models_dict = {}
    feature_names_dict = {}
    
    feature_cols = [
        'age', 'games_rating', 'is_world_cup', 'is_wc_year',
        'goals_per_90', 'assists_per_90', 'shots_per_90', 'passes_per_90',
        'key_passes_per_90', 'dribbles_per_90', 'tackles_per_90',
        'games_appearances', 'games_minutes', 'goals_total', 'goals_assists'
    ]
    categorical_features = ['nationality']
    
    print("\n==============================================")
    print("    HUAN LUYEN CHI TIET THEO NHOM VI TRI      ")
    print("==============================================")
    
    for group in position_groups:
        df_g = df[df['pos_group'] == group].copy()
        if len(df_g) < 10:
            print(f"\nBo qua nhom {group} do co qua it du lieu ({len(df_g)} mau).")
            continue
            
        print(f"\n>>> HUAN LUYEN NHOM: {group.upper()} ({len(df_g)} mau) <<<")
        
        y_g = df_g['target_transfer_fee_m_eur']
        y_g_log = np.log1p(y_g)
        
        X_g_cat = pd.get_dummies(df_g[categorical_features], drop_first=True)
        X_g_num = df_g[feature_cols]
        X_g = pd.concat([X_g_num, X_g_cat], axis=1)
        
        feature_names = X_g.columns.tolist()
        feature_names_dict[group] = feature_names
        
        X_train, X_test, y_train_log, y_test_log, y_train_orig, y_test_orig = train_test_split(
            X_g, y_g_log, y_g, test_size=0.2, random_state=42
        )
        
        # Điều chỉnh siêu tham số (Hyperparameters) phù hợp với kích thước mẫu từng vị trí
        n_est = 150 if group == 'Goalkeeper' else 250
        depth = 4 if group == 'Goalkeeper' else 5
        
        model = GradientBoostingRegressor(
            n_estimators=n_est,
            learning_rate=0.03,
            max_depth=depth,
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
        
        print(f" * Sai so tuyet doi trung binh (MAE) : +/- {mae:.2f} Trieu Euro")
        print(f" * Can sai so binh phuong (RMSE)     : {rmse:.2f} Trieu Euro")
        print(f" * He so xac dinh (R2 Score)         : {r2:.4f}")
        
        # Hiển thị độ quan trọng tính năng
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1][:5]
        print(" TOP 5 CHỈ SỐ QUYẾT ĐỊNH GIÁ:")
        for rank, idx in enumerate(indices, 1):
            print(f"   {rank}. {feature_names[idx]:<25} : {importances[idx]*100:.2f}%")
            
        models_dict[group] = model
        
    model_dir = os.path.dirname(__file__)
    model_path = os.path.join(model_dir, "player_value_model.joblib")
    
    model_artifact = {
        "models": models_dict,
        "feature_names": feature_names_dict,
        "feature_cols": feature_cols,
        "categorical_features": categorical_features,
        "use_log": True
    }
    
    joblib.dump(model_artifact, model_path)
    print(f"\nDa luu dong goi ca 4 mo hinh thanh cong tai: {model_path}")

if __name__ == "__main__":
    train_model()
