import pandas as pd


def time_split(
    df: pd.DataFrame,
    holdout_days: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        raise ValueError("Cannot split empty dataframe.")

    cutoff = df["timestamp"].max() - pd.Timedelta(days=holdout_days)

    train_df = df[df["timestamp"] < cutoff].copy()

    test_df = df[df["timestamp"] >= cutoff].copy()

    if train_df.empty:
        raise ValueError("Training split is empty.")

    if test_df.empty:
        raise ValueError("Test split is empty.")

    return train_df, test_df
