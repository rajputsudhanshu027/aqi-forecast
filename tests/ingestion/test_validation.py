from aqi.ingestion.validation.validator import (
    validate_records,
)


def make_record(
    value=42.5,
    parameter="pm25",
    unit="µg/m³",
    has_flags=False,
    start="2026-11-17T10:00:00Z",
    end="2026-11-17T11:00:00Z",
):

    return {
        "value": value,
        "flagInfo": {
            "hasFlags": has_flags,
        },
        "parameter": {
            "id": 2,
            "name": parameter,
            "units": unit,
            "displayName": "PM2.5",
        },
        "period": {
            "label": "raw",
            "interval": "01:00:00",
            "datetimeFrom": {
                "utc": start,
                "local": "2026-11-17T15:30:00+05:30",
            },
            "datetimeTo": {
                "utc": end,
                "local": "2026-11-17T16:30:00+05:30",
            },
        },
    }


def test_valid_pm25_record_is_accepted():

    result = validate_records(
        records=[make_record()],
        sensor_id=2001,
        location_id=1001,
    )

    assert result["accepted_count"] == 1
    assert result["rejected_count"] == 0


def test_null_value_is_rejected():

    result = validate_records(
        records=[make_record(value=None)],
        sensor_id=2001,
        location_id=1001,
    )

    assert result["accepted_count"] == 0
    assert result["rejected_count"] == 1

    assert "missing_value" in result["rejected_records"][0]["reasons"]


def test_negative_value_is_rejected():

    result = validate_records(
        records=[make_record(value=-5)],
        sensor_id=2001,
        location_id=1001,
    )

    assert result["rejected_count"] == 1

    assert "negative_value" in result["rejected_records"][0]["reasons"]


def test_wrong_parameter_is_rejected():

    result = validate_records(
        records=[make_record(parameter="pm10")],
        sensor_id=2001,
        location_id=1001,
    )

    assert result["rejected_count"] == 1

    assert "wrong_parameter" in result["rejected_records"][0]["reasons"]


def test_wrong_unit_is_rejected():

    result = validate_records(
        records=[make_record(unit="ppm")],
        sensor_id=2001,
        location_id=1001,
    )

    assert result["rejected_count"] == 1

    assert "unexpected_unit" in result["rejected_records"][0]["reasons"]


def test_duplicate_timestamp_is_rejected():

    record = make_record()

    result = validate_records(
        records=[record, record],
        sensor_id=2001,
        location_id=1001,
    )

    assert result["accepted_count"] == 1
    assert result["rejected_count"] == 1

    assert "duplicate_timestamp" in result["rejected_records"][0]["reasons"]


def test_flagged_record_is_accepted_with_warning():

    result = validate_records(
        records=[make_record(has_flags=True)],
        sensor_id=2001,
        location_id=1001,
    )

    assert result["accepted_count"] == 1
    assert result["warning_count"] == 1


def test_non_hourly_period_is_rejected():

    result = validate_records(
        records=[
            make_record(
                start="2026-11-17T10:00:00Z",
                end="2026-11-17T10:30:00Z",
            )
        ],
        sensor_id=2001,
        location_id=1001,
    )

    assert result["rejected_count"] == 1

    assert "non_hourly_period" in result["rejected_records"][0]["reasons"]


def test_missing_period_is_rejected():

    record = make_record()
    record["period"] = None

    result = validate_records(
        records=[record],
        sensor_id=2001,
        location_id=1001,
    )

    assert result["rejected_count"] == 1

    assert "missing_period" in result["rejected_records"][0]["reasons"]
