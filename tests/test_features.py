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
