from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    city: str

    pm25: float = Field(
        ge=0,
        le=1000,
    )

    temperature: float

    relative_humidity: float = Field(
        ge=0,
        le=100,
    )

    wind_speed: float = Field(
        ge=0,
    )

    pm25_lag_1h: float
    pm25_lag_3h: float
    pm25_lag_6h: float
    pm25_lag_12h: float
    pm25_lag_24h: float

    pm25_rolling_mean_6h: float
    pm25_rolling_std_6h: float

    pm25_rolling_mean_12h: float
    pm25_rolling_std_12h: float

    pm25_rolling_mean_24h: float
    pm25_rolling_std_24h: float

    hour: int = Field(
        ge=0,
        le=23,
    )

    day_of_week: int = Field(
        ge=0,
        le=6,
    )

    month: int = Field(
        ge=1,
        le=12,
    )


class PredictionResponse(BaseModel):
    predicted_pm25: float
    model_version: str
