from __future__ import annotations

import json
import logging
import unicodedata
from collections import Counter
from datetime import UTC, timedelta
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from aqi.ingestion.validation.models import (
    OpenAQHourlyMeasurement,
)

logger = logging.getLogger(__name__)


def normalize_parameter_name(name: str) -> str:
    """
    Normalize parameter names before comparison.
    """

    return (
        name.lower().replace(".", "").replace("_", "").replace("-", "").replace(" ", "")
    )


def normalize_unit(unit: str) -> str:
    """
    Normalize equivalent spellings of micrograms per cubic metre.
    """

    normalized = unicodedata.normalize(
        "NFKC",
        unit,
    ).lower()

    normalized = (
        normalized.replace("μ", "u")
        .replace("µ", "u")
        .replace(" ", "")
        .replace("³", "3")
    )

    return normalized


def validate_measurement_quality(
    measurement: OpenAQHourlyMeasurement,
) -> list[str]:
    """
    Apply semantic quality rules to a parsed measurement.
    """

    errors = []

    # Rule 1: The parameter must be PM2.5.
    parameter_name = normalize_parameter_name(measurement.parameter.name)

    if parameter_name != "pm25":
        errors.append("wrong_parameter")

    # Rule 2: The measurement unit must be µg/m³.
    unit = normalize_unit(measurement.parameter.units)

    if unit != "ug/m3":
        errors.append("unexpected_unit")

    # Rule 3: The measurement value must not be missing.
    if measurement.value is None:
        errors.append("missing_value")

    # Rule 4: Negative concentrations are rejected.
    elif measurement.value < 0:
        errors.append("negative_value")

    # Rule 5: A usable measurement needs a time period.
    if measurement.period is None:
        errors.append("missing_period")

    else:
        start = measurement.period.datetime_from.utc
        end = measurement.period.datetime_to.utc

        # Rule 6: Our dataset requires one-hour periods.
        duration = end - start

        if duration != timedelta(hours=1):
            errors.append("non_hourly_period")

    return errors


def pydantic_error_messages(
    error: ValidationError,
) -> list[str]:
    """
    Convert Pydantic errors into readable messages.
    """

    messages = []

    for item in error.errors():
        field = ".".join(str(part) for part in item["loc"])

        messages.append(f"{field}: {item['msg']}")

    return messages


def validate_records(
    records: list[dict[str, Any]],
    sensor_id: int,
    location_id: int,
) -> dict[str, Any]:
    """
    Validate all measurement records for one sensor.

    Valid records are retained.
    Invalid records are rejected with reasons.
    Flagged records generate warnings.
    Duplicate hourly timestamps are rejected.
    """

    accepted_records = []
    rejected_records = []
    warnings = []

    seen_timestamps = set()

    for index, raw_record in enumerate(records):
        # Step 1: Validate the record's structure.
        try:
            measurement = OpenAQHourlyMeasurement.model_validate(raw_record)

        except ValidationError as error:
            rejected_records.append(
                {
                    "record_index": index,
                    "reasons": ["schema_validation_failed"],
                    "details": pydantic_error_messages(error),
                    "raw_record": raw_record,
                }
            )

            continue

        # Step 2: Apply data-quality rules.
        quality_errors = validate_measurement_quality(measurement)

        if quality_errors:
            rejected_records.append(
                {
                    "record_index": index,
                    "reasons": quality_errors,
                    "raw_record": raw_record,
                }
            )

            continue

        # A valid measurement must have a period.
        period = measurement.period

        if period is None:
            raise RuntimeError("Unexpected missing period after validation.")

        # Use the period end as the canonical hourly timestamp.
        timestamp_utc = (
            period.datetime_to.utc.astimezone(UTC).isoformat().replace("+00:00", "Z")
        )

        # Step 3: Detect duplicate timestamps.
        if timestamp_utc in seen_timestamps:
            rejected_records.append(
                {
                    "record_index": index,
                    "reasons": ["duplicate_timestamp"],
                    "raw_record": raw_record,
                }
            )

            continue

        seen_timestamps.add(timestamp_utc)

        # Step 4: Record OpenAQ flags as warnings.
        has_flags = (
            measurement.flag_info.has_flags
            if measurement.flag_info is not None
            else False
        )

        if has_flags:
            warnings.append(
                {
                    "record_index": index,
                    "warning": "openaq_flagged_record",
                }
            )

        # Step 5: Keep the accepted measurement.
        accepted_records.append(
            {
                "record_index": index,
                "sensor_id": sensor_id,
                "location_id": location_id,
                "timestamp_utc": timestamp_utc,
                "value": measurement.value,
                "unit": measurement.parameter.units,
                "parameter": measurement.parameter.name,
                "period_start_utc": (period.datetime_from.utc.isoformat()),
                "period_end_utc": (period.datetime_to.utc.isoformat()),
                "has_flags": has_flags,
                "raw_record": raw_record,
            }
        )

    # Step 6: Count rejection reasons.
    rejection_reasons = Counter(
        reason for record in rejected_records for reason in record["reasons"]
    )

    return {
        "sensor_id": sensor_id,
        "location_id": location_id,
        "total_records": len(records),
        "accepted_count": len(accepted_records),
        "rejected_count": len(rejected_records),
        "warning_count": len(warnings),
        "rejection_reasons": dict(rejection_reasons),
        "accepted_records": accepted_records,
        "rejected_records": rejected_records,
        "warnings": warnings,
    }


def write_json_atomic(
    file_path: Path,
    data: dict[str, Any],
) -> None:
    """
    Write a JSON file through a temporary file.
    """

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = file_path.with_suffix(file_path.suffix + ".tmp")

    with temporary_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )

    temporary_path.replace(file_path)


def validate_raw_file(
    raw_file: Path,
    output_file: Path,
) -> dict[str, Any]:
    """
    Read one raw sensor file, validate its records,
    and save a separate validation result.
    """

    with raw_file.open(
        "r",
        encoding="utf-8",
    ) as file:
        payload = json.load(file)

    if not isinstance(payload, dict):
        raise ValueError(f"Invalid raw file structure: {raw_file}")

    records = payload.get("results")

    if not isinstance(records, list):
        raise ValueError(f"Missing results list in: {raw_file}")

    sensor = payload.get("sensor") or {}
    location = payload.get("location") or {}

    sensor_id = sensor.get("id")
    location_id = location.get("id")

    if sensor_id is None or location_id is None:
        raise ValueError(f"Missing sensor or location metadata: {raw_file}")

    result = validate_records(
        records=records,
        sensor_id=sensor_id,
        location_id=location_id,
    )

    report = {
        "source_file": str(raw_file),
        "source": payload.get("source"),
        "retrieved_at_utc": payload.get("retrieved_at_utc"),
        "validated_at_utc": (__import__("datetime").datetime.now(UTC).isoformat()),
        "query": payload.get("query"),
        **result,
    }

    write_json_atomic(
        output_file,
        report,
    )

    logger.info(
        "Validated sensor %s: accepted=%s rejected=%s warnings=%s",
        sensor_id,
        result["accepted_count"],
        result["rejected_count"],
        result["warning_count"],
    )

    return result
