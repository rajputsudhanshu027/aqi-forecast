import numpy as np

from aqi.config import load_config
from aqi.features.build import build_features
from aqi.train.split import time_split
from aqi.train.train import train_model


def test_model_can_predict(
    hourly_aqi_df,
):
    config = load_config("configs/train.yaml")

    features = build_features(
        hourly_aqi_df,
        horizon_hours=24,
        lag_hours=[1, 3, 6, 12, 24],
        rolling_windows=[6, 12, 24],
    )

    features = features.dropna()

    train_df, test_df = time_split(
        features,
        holdout_days=20,
    )

    result = train_model(
        train_df,
        test_df,
        config,
    )

    assert np.isfinite(result.metrics["mae"])

    assert np.isfinite(result.metrics["rmse"])
