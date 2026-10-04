from dataclasses import dataclass

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from aqi.config import TrainConfig
from aqi.train.evaluate import regression_metrics


@dataclass
class TrainingResult:
    model: Pipeline
    metrics: dict[str, float]


NUMERIC_FEATURES = [
    "pm25",
    "temperature",
    "relative_humidity",
    "wind_speed",
    "pm25_lag_1h",
    "pm25_lag_3h",
    "pm25_lag_6h",
    "pm25_lag_12h",
    "pm25_lag_24h",
    "pm25_rolling_mean_6h",
    "pm25_rolling_std_6h",
    "pm25_rolling_mean_12h",
    "pm25_rolling_std_12h",
    "pm25_rolling_mean_24h",
    "pm25_rolling_std_24h",
    "hour",
    "day_of_week",
    "month",
]

CATEGORICAL_FEATURES = [
    "city",
]

TARGET = "target_pm25_24h"


def make_model(config: TrainConfig) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "city",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
                CATEGORICAL_FEATURES,
            ),
            (
                "numeric",
                "passthrough",
                NUMERIC_FEATURES,
            ),
        ]
    )

    regressor = HistGradientBoostingRegressor(
        learning_rate=config.model.learning_rate,
        max_iter=config.model.max_iter,
        max_leaf_nodes=config.model.max_leaf_nodes,
        min_samples_leaf=config.model.min_samples_leaf,
        random_state=config.model.random_state,
    )

    return Pipeline(
        steps=[
            ("preprocessing", preprocessor),
            ("model", regressor),
        ]
    )


def train_model(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    config: TrainConfig,
) -> TrainingResult:
    model = make_model(config)

    x_train = train_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]

    y_train = train_df[TARGET]

    x_test = test_df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]

    y_test = test_df[TARGET]

    model.fit(
        x_train,
        y_train,
    )

    predictions = model.predict(x_test)

    metrics = regression_metrics(
        y_test,
        predictions,
    )

    return TrainingResult(
        model=model,
        metrics=metrics,
    )
