# feature_selection.py

def apply_feature_selection(df, selected_features):
    """
    df: preprocessed dataframe
    selected_features: loaded from selected_features.json
    """

    # Add missing columns
    for col in selected_features:
        if col not in df.columns:
            df[col] = 0

    # Keep exact order
    df = df[selected_features]

    return df