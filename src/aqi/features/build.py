import pandas as pd

REQUIRED_COLUMNS = {
    "city",
    "timestamp",
    "pm25",
    "temperature",
    "relative_humidity",
    "wind_speed",
}


def validate_columns(df: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS - set(df.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")


def build_features(
    df: pd.DataFrame,
    *,
    horizon_hours: int,
    lag_hours: list[int],
    rolling_windows: list[int],
) -> pd.DataFrame:
    validate_columns(df)

    data = df.copy()

    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True)

    data = data.sort_values(["city", "timestamp"]).reset_index(drop=True)

    grouped_pm25 = data.groupby("city")["pm25"]

    for lag in lag_hours:
        data[f"pm25_lag_{lag}h"] = grouped_pm25.shift(lag)

    for window in rolling_windows:
        data[f"pm25_rolling_mean_{window}h"] = grouped_pm25.transform(
            lambda values, window=window: values.rolling(
                window=window,
                min_periods=window,
            ).mean()
        )

        data[f"pm25_rolling_std_{window}h"] = grouped_pm25.transform(
            lambda values, window=window: values.rolling(
                window=window,
                min_periods=window,
            ).std()
        )

    data["hour"] = data["timestamp"].dt.hour
    data["day_of_week"] = data["timestamp"].dt.dayofweek
    data["month"] = data["timestamp"].dt.month

    data["target_pm25_24h"] = data.groupby("city")["pm25"].shift(-horizon_hours)

    return data
