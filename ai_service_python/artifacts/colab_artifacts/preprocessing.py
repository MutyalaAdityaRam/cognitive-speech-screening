# preprocessing.py

import pandas as pd
import numpy as np


def preprocess_features(df, scaler, imputer, feature_names):
    """
    df: DataFrame from feature_extraction
    scaler: loaded scaler.pkl
    imputer: loaded imputer.pkl (if used)
    feature_names: selected_features.json (ordered)
    """

    # ================= DROP USELESS COLUMNS =================
    drop_cols = []

    for col in df.columns:
        if col.lower() in ['file', 'path']:
            drop_cols.append(col)

    df = df.drop(columns=drop_cols, errors='ignore')

    # ================= CLEAN STRINGS =================
    for col in df.columns:
        df[col] = df[col].astype(str)\
                         .str.replace('[', '', regex=False)\
                         .str.replace(']', '', regex=False)
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # ================= REMOVE FULL NaN =================
    df = df.dropna(axis=1, how='all')

    # ================= ALIGN FEATURES =================
    for col in feature_names:
        if col not in df.columns:
            df[col] = 0

    df = df[feature_names]

    # ================= IMPUTE =================
    df = imputer.transform(df)

    # ================= SCALE =================
    df = scaler.transform(df)

    df = pd.DataFrame(df, columns=feature_names)

    return df