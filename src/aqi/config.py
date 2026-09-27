from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class DataConfig(BaseModel):
    path: Path


class ForecastConfig(BaseModel):
    horizon_hours: int = Field(gt=0)
    holdout_days: int = Field(gt=0)


class FeatureConfig(BaseModel):
    lag_hours: list[int]
    rolling_windows: list[int]


class ModelConfig(BaseModel):
    learning_rate: float = Field(gt=0)
    max_iter: int = Field(gt=0)
    max_leaf_nodes: int = Field(gt=1)
    min_samples_leaf: int = Field(gt=0)
    random_state: int


class OutputConfig(BaseModel):
    model_path: Path


class TrainConfig(BaseModel):
    data: DataConfig
    forecast: ForecastConfig
    features: FeatureConfig
    model: ModelConfig
    output: OutputConfig


def load_config(path: str | Path) -> TrainConfig:
    path = Path(path)

    with path.open() as file:
        raw_config = yaml.safe_load(file)

    return TrainConfig.model_validate(raw_config)
