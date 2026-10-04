from pathlib import Path

import joblib
import pandas as pd

from aqi.config import load_config
from aqi.features.build import build_features
from aqi.train.baseline import evaluate_persistence_baseline
from aqi.train.split import time_split
from aqi.train.train import train_model


def main() -> None:
    config = load_config("configs/train.yaml")

    raw_df = pd.read_csv(config.data.path)

    features = build_features(
        raw_df,
        horizon_hours=config.forecast.horizon_hours,
        lag_hours=config.features.lag_hours,
        rolling_windows=config.features.rolling_windows,
    )

    features = features.dropna().reset_index(drop=True)

    train_df, test_df = time_split(
        features,
        holdout_days=config.forecast.holdout_days,
    )

    baseline_metrics = evaluate_persistence_baseline(test_df)

    result = train_model(
        train_df=train_df,
        test_df=test_df,
        config=config,
    )

    print("Persistence baseline:")
    print(baseline_metrics)

    print()

    print("ML model:")
    print(result.metrics)

    model_path = Path(config.output.model_path)

    model_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        result.model,
        model_path,
    )

    print()
    print(f"Saved model to {model_path}")


if __name__ == "__main__":
    main()
