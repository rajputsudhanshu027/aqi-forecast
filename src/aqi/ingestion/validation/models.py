from __future__ import annotations

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class OpenAQBaseModel(BaseModel):
    """
    Common configuration for OpenAQ response models.
    """

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
    )


class OpenAQDateTime(OpenAQBaseModel):
    """
    Represents OpenAQ's UTC and local timestamps.
    """

    utc: datetime
    local: datetime

    @field_validator("utc", "local")
    @classmethod
    def require_timezone(
        cls,
        value: datetime,
    ) -> datetime:

        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Datetime must include timezone information.")

        return value


class OpenAQParameter(OpenAQBaseModel):
    """
    Describes the pollutant or parameter being measured.
    """

    id: int
    name: str
    units: str

    display_name: str | None = Field(
        default=None,
        alias="displayName",
    )


class OpenAQPeriod(OpenAQBaseModel):
    """
    Describes the time period represented by a measurement.
    """

    label: str
    interval: str

    datetime_from: OpenAQDateTime = Field(alias="datetimeFrom")

    datetime_to: OpenAQDateTime = Field(alias="datetimeTo")

    @model_validator(mode="after")
    def validate_period_order(self) -> OpenAQPeriod:

        if self.datetime_from.utc >= self.datetime_to.utc:
            raise ValueError("Period start must be earlier than period end.")

        return self


class OpenAQFlagInfo(OpenAQBaseModel):
    """
    Contains OpenAQ's measurement flag information.
    """

    has_flags: bool = Field(alias="hasFlags")


class OpenAQCoordinates(OpenAQBaseModel):
    """
    Represents optional measurement coordinates.
    """

    latitude: float | None = None
    longitude: float | None = None

    @model_validator(mode="after")
    def validate_coordinate_ranges(
        self,
    ) -> OpenAQCoordinates:

        if self.latitude is not None and not -90 <= self.latitude <= 90:
            raise ValueError("Invalid latitude.")

        if self.longitude is not None and not -180 <= self.longitude <= 180:
            raise ValueError("Invalid longitude.")

        return self


class OpenAQHourlyMeasurement(OpenAQBaseModel):
    """
    Represents one OpenAQ hourly measurement.
    """

    value: float | None = Field(allow_inf_nan=False)

    parameter: OpenAQParameter

    period: OpenAQPeriod | None = None

    flag_info: OpenAQFlagInfo | None = Field(
        default=None,
        alias="flagInfo",
    )

    coordinates: OpenAQCoordinates | None = None

    @field_validator("value", mode="before")
    @classmethod
    def reject_boolean_values(cls, value):

        if isinstance(value, bool):
            raise ValueError("Boolean values are not valid measurements.")

        return value
