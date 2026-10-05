from pathlib import Path

import numpy as np
import pandas as pd

OUTPUT_PATH = Path("data/bootstrap_aqi.csv")

CITIES = {
    "Delhi": {
        "base_pm25": 140,
        "temperature": 25,
        "humidity": 55,
        "wind_speed": 7,
    },
    "Mumbai": {
        "base_pm25": 60,
        "temperature": 28,
        "humidity": 75,
        "wind_speed": 11,
    },
    "Bengaluru": {
        "base_pm25": 45,
        "temperature": 23,
        "humidity": 65,
        "wind_speed": 9,
    },
    "Chennai": {
        "base_pm25": 55,
        "temperature": 29,
        "humidity": 72,
        "wind_speed": 12,
    },
}


def generate_city_data(
    city: str,
    config: dict[str, float],
    timestamps: pd.DatetimeIndex,
    rng: np.random.Generator,
) -> pd.DataFrame:
    n = len(timestamps)

    hour = timestamps.hour.to_numpy()
    day_of_year = timestamps.dayofyear.to_numpy()

    daily_cycle = 15 * np.sin(2 * np.pi * hour / 24)

    seasonal_cycle = 20 * np.cos(2 * np.pi * day_of_year / 365)

    noise = rng.normal(
        loc=0,
        scale=8,
        size=n,
    )

    pm25 = config["base_pm25"] + daily_cycle + seasonal_cycle + noise

    pm25 = np.clip(
        pm25,
        a_min=1,
        a_max=None,
    )

    temperature = (
        config["temperature"]
        + 5 * np.sin(2 * np.pi * day_of_year / 365)
        + 3 * np.sin(2 * np.pi * hour / 24)
        + rng.normal(0, 1.5, n)
    )

    relative_humidity = (
        config["humidity"] - 10 * np.sin(2 * np.pi * hour / 24) + rng.normal(0, 4, n)
    )

    relative_humidity = np.clip(
        relative_humidity,
        10,
        100,
    )

    wind_speed = config["wind_speed"] + rng.normal(0, 2, n)

    wind_speed = np.clip(
        wind_speed,
        0,
        None,
    )

    return pd.DataFrame(
        {
            "city": city,
            "timestamp": timestamps,
            "pm25": pm25,
            "temperature": temperature,
            "relative_humidity": relative_humidity,
            "wind_speed": wind_speed,
        }
    )


def main() -> None:
    rng = np.random.default_rng(42)

    timestamps = pd.date_range(
        start="2025-01-01",
        end="2025-12-31 23:00:00",
        freq="h",
        tz="UTC",
    )

    city_frames = []

    for city, config in CITIES.items():
        city_df = generate_city_data(
            city=city,
            config=config,
            timestamps=timestamps,
            rng=rng,
        )

        city_frames.append(city_df)

    df = pd.concat(
        city_frames,
        ignore_index=True,
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(f"Generated {len(df):,} rows.")
    print(f"Saved to: {OUTPUT_PATH}")
    print()
    print(df.head())
    print()
    print("Rows per city:")
    print(df["city"].value_counts())


if __name__ == "__main__":
    main()
