import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def hourly_aqi_df() -> pd.DataFrame:
    rows = 24 * 90

    timestamps = pd.date_range(
        start="2025-01-01",
        periods=rows,
        freq="h",
        tz="UTC",
    )

    rng = np.random.default_rng(42)

    pm25 = 100 + 25 * np.sin(np.arange(rows) / 24) + rng.normal(0, 5, rows)

    return pd.DataFrame(
        {
            "city": ["Delhi"] * rows,
            "timestamp": timestamps,
            "pm25": pm25,
            "temperature": 20 + rng.normal(0, 4, rows),
            "relative_humidity": 60 + rng.normal(0, 10, rows),
            "wind_speed": 8 + rng.normal(0, 2, rows),
        }
    )
