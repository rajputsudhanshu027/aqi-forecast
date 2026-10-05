import numpy as np

from aqi.features.build import build_features


def test_feature_shape(hourly_aqi_df):
    result = build_features(
        hourly_aqi_df,
        horizon_hours=24,
        lag_hours=[1, 3, 6, 12, 24],
        rolling_windows=[6, 12, 24],
    )

    expected_columns = {
        "pm25_lag_1h",
        "pm25_lag_24h",
        "pm25_rolling_mean_6h",
        "pm25_rolling_mean_24h",
        "target_pm25_24h",
    }

    assert expected_columns.issubset(result.columns)

    assert len(result) == len(hourly_aqi_df)


def test_lag_features_use_past_values(
    hourly_aqi_df,
):
    result = build_features(
        hourly_aqi_df,
        horizon_hours=24,
        lag_hours=[1],
        rolling_windows=[6],
    )

    current_row = result.iloc[10]

    previous_row = result.iloc[9]

    assert current_row["pm25_lag_1h"] == previous_row["pm25"]


def test_missing_pm25_does_not_crash(
    hourly_aqi_df,
):
    df = hourly_aqi_df.copy()

    df.loc[20, "pm25"] = np.nan

    result = build_features(
        df,
        horizon_hours=24,
        lag_hours=[1, 24],
        rolling_windows=[6, 24],
    )

    assert len(result) == len(df)
