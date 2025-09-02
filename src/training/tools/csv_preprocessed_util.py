import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler

# IQR 이상치 제거
def remove_outliers_iqr(df, columns):
    df_clean = df.copy()

    for col in columns:
        Q1 = df_clean[col].quantile(0.25)
        Q3 = df_clean[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        
        df_clean = df_clean[(df_clean[col] >= lower) & (df_clean[col] <= upper)]

    return df_clean

# Z-Score 이상치 제거
def remove_outliers_zscore(df: pd.DataFrame, cols: list, threshold: float = 3.0) -> pd.DataFrame:
    df_copy = df.copy()
    mask = pd.Series(True, index=df_copy.index)

    for col in cols:
        col_mean = df_copy[col].mean()
        col_std = df_copy[col].std()
        z_scores = (df_copy[col] - col_mean) / col_std
        mask &= z_scores.abs() <= threshold

    return df_copy[mask].reset_index(drop=True)

# 라벨 인코더
def label_encode_df(df: pd.DataFrame, cols: list):
    df_copy = df.copy()
    encoders = {}
    for col in cols:
        le = LabelEncoder()
        df_copy[col] = le.fit_transform(df_copy[col].astype(str))  # NaN 방지를 위해 str 처리
        encoders[col] = le
    return df_copy, encoders

# 원핫 인코더
def onehot_encode_df(df: pd.DataFrame, cols: list, drop_first=False):
    df_copy = df.copy()
    df_copy = pd.get_dummies(df_copy, columns=cols, drop_first=drop_first)
    return df_copy

# 스케일링
def scale_df(df: pd.DataFrame, cols: list, method: str = "standard"):
    df_copy = df.copy()
    
    if method == "standard":
        scaler = StandardScaler()
    elif method == "minmax":
        scaler = MinMaxScaler()
    elif method == "robust":
        scaler = RobustScaler()
    else:
        raise ValueError("method must be 'standard', 'minmax', or 'robust'")
    
    df_copy[cols] = scaler.fit_transform(df_copy[cols])
    
    return df_copy, scaler

# 결측치 처리
def fill_missing(df, strategy="mean", cols=None, fill_value=None):
    df_copy = df.copy()
    cols = cols or df_copy.columns
    for col in cols:
        if strategy == "mean":
            df_copy[col] = df_copy[col].fillna(df_copy[col].mean())
        elif strategy == "median":
            df_copy[col] = df_copy[col].fillna(df_copy[col].median())
        elif strategy == "mode":
            df_copy[col] = df_copy[col].fillna(df_copy[col].mode()[0])
        elif strategy == "constant":
            df_copy[col] = df_copy[col].fillna(fill_value)
    return df_copy

# 칼럼 필터링
def filter_columns(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    df_copy = df.copy()
    df_copy = df_copy[cols].copy()
    return df_copy

# 최종 전처리 파이프라인
def preprocess_pipeline(
    df: pd.DataFrame,
    mode: str = "fit",                   # "fit" or "transform"
    artifacts: dict | None = None,       # fit 규칙 저장/transform 재사용
    config: dict | None = None
):
    """
    헬퍼 함수들만 호출해 구성한 전처리 파이프라인.
    - mode="fit"       : 규칙 학습 + 적용 → (df_processed, artifacts)
    - mode="transform" : 저장된 규칙만 적용 → (df_processed, artifacts)

    config 예시
    ----------
    config = {
        "select_cols": ["id","condition","is_completed","location","model","model_type","price"],

        # 결측치
        # "impute": {"strategy":"constant","cols":["model","model_type"],"fill_value":"__NA__"},

        # 이상치 제거(fit에서만)
        # "outlier": {"method":"zscore","cols":["price"],"threshold":3.0}
        # "outlier": {"method":"iqr","cols":["price"]}

        # 라벨 인코딩
        # "label_encode": {"cols":["condition","is_completed","location","model","model_type"]},

        # 원핫 인코딩
        # "onehot": {"cols":["is_completed"],"drop_first":False},

        # 스케일링
        # "scale": {"cols":["price"],"method":"standard"},

        # 최종 칼럼 순서
        # "final_cols": ["id","condition","is_completed","location","model","model_type","price"]
    }
    """
    assert mode in ("fit", "transform")
    cfg = config or {}
    df_out = df.copy()
    artifacts = artifacts or {}

    # 1) 칼럼 선택
    if cfg.get("select_cols"):
        df_out = filter_columns(df_out, cfg["select_cols"])

    # 2) 결측치 처리 (헬퍼 사용)
    if "impute" in cfg:
        im = cfg["impute"]
        cols_impute = [c for c in im.get("cols", []) if c in df_out.columns]
        if cols_impute:
            df_out[cols_impute] = fill_missing(
                df_out[cols_impute],
                strategy=im.get("strategy", "mean"),
                cols=cols_impute,
                fill_value=im.get("fill_value", None)
            )

    # 3) 이상치 제거 (fit에서만)
    if mode == "fit" and "outlier" in cfg:
        oc = cfg["outlier"]
        cols_out = [c for c in oc.get("cols", []) if c in df_out.columns]
        if cols_out:
            if oc.get("method", "zscore") == "zscore":
                thr = float(oc.get("threshold", 3.0))
                df_out = remove_outliers_zscore(df_out, cols_out, threshold=thr)
                artifacts["outlier"] = {"method": "zscore", "cols": cols_out, "threshold": thr}
            else:
                df_out = remove_outliers_iqr(df_out, cols_out)
                artifacts["outlier"] = {"method": "iqr", "cols": cols_out}

    # 4) 라벨 인코딩 (헬퍼 사용)
    if "label_encode" in cfg:
        le_cols = [c for c in cfg["label_encode"].get("cols", []) if c in df_out.columns]
        if le_cols:
            if mode == "fit":
                df_out, encoders = label_encode_df(df_out, le_cols)
                artifacts["label_encoders"] = encoders  # {col: LabelEncoder}
            else:
                encoders = artifacts.get("label_encoders", {})
                for col in le_cols:
                    le = encoders.get(col)
                    if le is None:
                        continue

    # 5) 원핫 인코딩 (헬퍼 사용)
    if "onehot" in cfg:
        oh_cols = [c for c in cfg["onehot"].get("cols", []) if c in df_out.columns]
        drop_first = bool(cfg["onehot"].get("drop_first", False))
        if oh_cols:
            if mode == "fit":
                df_out = onehot_encode_df(df_out, oh_cols, drop_first=drop_first)
                artifacts["onehot_info"] = {"cols": oh_cols, "drop_first": drop_first}
                artifacts["onehot_columns"] = list(df_out.columns)
            else:
                info = artifacts.get("onehot_info", {})
                oh_cols_fit = info.get("cols", oh_cols)
                drop_first_fit = info.get("drop_first", drop_first)
                df_out = onehot_encode_df(df_out, oh_cols_fit, drop_first=drop_first_fit)
                cols_fit = artifacts.get("onehot_columns")
                if cols_fit:
                    missing = [c for c in cols_fit if c not in df_out.columns]
                    for c in missing:
                        df_out[c] = 0
                    df_out = df_out[cols_fit]

    # 6) 스케일링 (헬퍼 사용)
    if "scale" in cfg:
        sc = cfg["scale"]
        sc_cols = [c for c in sc.get("cols", []) if c in df_out.columns]
        if sc_cols:
            if mode == "fit":
                df_out, scaler = scale_df(df_out, sc_cols, method=sc.get("method", "standard"))
                artifacts["scaler"] = scaler
                artifacts["scale_info"] = {"cols": sc_cols, "method": sc.get("method", "standard")}
            else:
                scaler = artifacts.get("scaler")
                sc_info = artifacts.get("scale_info", {})
                sc_cols_fit = sc_info.get("cols", sc_cols)
                if scaler is not None and sc_cols_fit:
                    for c in sc_cols_fit:
                        if c not in df_out.columns:
                            df_out[c] = 0.0
                    df_out[sc_cols_fit] = scaler.transform(df_out[sc_cols_fit])

    # 7) 최종 칼럼 순서
    if cfg.get("final_cols"):
        final_cols = [c for c in cfg["final_cols"] if c in df_out.columns]
        df_out = df_out[final_cols]

    return df_out.reset_index(drop=True), artifacts