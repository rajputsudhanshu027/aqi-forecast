import pandas as pd

from aqi.train.evaluate import regression_metrics


def evaluate_persistence_baseline(
    df: pd.DataFrame,
) -> dict[str, float]:
    y_true = df["target_pm25_24h"]

    y_pred = df["pm25"]

    return regression_metrics(
        y_true,
        y_pred,
    )
