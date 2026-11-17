from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from aqi.ingestion.clients.openaq import OpenAQClient

logger = logging.getLogger(__name__)


class OpenAQIngestionPipeline:
    """
    Discover PM2.5 sensors and download their hourly measurements.
    Save the API data as raw JSON files.
    """

    def __init__(
        self,
        client: OpenAQClient,
        output_dir: Path,
        latitude: float,
        longitude: float,
        radius_m: int = 25000,
        location_page_size: int = 100,
        measurement_page_size: int = 1000,
    ) -> None:

        self.client = client
        self.output_dir = Path(output_dir)
        self.latitude = latitude
        self.longitude = longitude
        self.radius_m = radius_m
        self.location_page_size = location_page_size
        self.measurement_page_size = measurement_page_size

    @staticmethod
    def is_pm25_sensor(sensor: dict[str, Any]) -> bool:
        """
        Return True when a sensor measures PM2.5.
        """

        parameter = sensor.get("parameter") or {}
        parameter_name = parameter.get("name", "")

        normalized_name = (
            parameter_name.lower()
            .replace(".", "")
            .replace("_", "")
            .replace("-", "")
            .replace(" ", "")
        )

        return normalized_name == "pm25"

    @staticmethod
    def validate_date_range(
        datetime_from: str,
        datetime_to: str,
    ) -> None:
        """
        Ensure both dates are timezone-aware and correctly ordered.
        """

        start = datetime.fromisoformat(datetime_from.replace("Z", "+00:00"))

        end = datetime.fromisoformat(datetime_to.replace("Z", "+00:00"))

        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError("Both dates must include a timezone.")

        if start >= end:
            raise ValueError("datetime_from must be earlier than datetime_to.")

    def discover_locations(self) -> list[dict[str, Any]]:
        """
        Find monitoring locations around the configured coordinates.
        Retrieve additional pages when necessary.
        """

        locations = []

        page = 1
        max_pages = 20

        while page <= max_pages:
            logger.info(
                "Discovering locations: page %s",
                page,
            )

            page_results = self.client.get_locations_near(
                latitude=self.latitude,
                longitude=self.longitude,
                radius_m=self.radius_m,
                limit=self.location_page_size,
                page=page,
            )

            locations.extend(page_results)

            if len(page_results) < self.location_page_size:
                break

            page += 1

        if page > max_pages:
            logger.warning("Reached the maximum location page limit.")

        logger.info(
            "Discovered %s monitoring locations.",
            len(locations),
        )

        return locations

    def discover_pm25_sensors(
        self,
        locations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Extract PM2.5 sensors from the discovered locations.
        """

        discovered_sensors = []
        seen_sensor_ids = set()

        for location in locations:
            sensors = location.get("sensors", [])

            for sensor in sensors:
                if not self.is_pm25_sensor(sensor):
                    continue

                sensor_id = sensor.get("id")

                if sensor_id is None:
                    logger.warning("Skipping a PM2.5 sensor without an ID.")
                    continue

                if sensor_id in seen_sensor_ids:
                    continue

                seen_sensor_ids.add(sensor_id)

                discovered_sensors.append(
                    {
                        "location": location,
                        "sensor": sensor,
                    }
                )

        logger.info(
            "Discovered %s unique PM2.5 sensors.",
            len(discovered_sensors),
        )

        return discovered_sensors

    def fetch_sensor_measurements(
        self,
        sensor_id: int,
        datetime_from: str,
        datetime_to: str,
    ) -> list[dict[str, Any]]:
        """
        Download all available hourly records for one sensor.
        """

        all_measurements = []

        page = 1
        max_pages = 100

        while page <= max_pages:
            logger.info(
                "Fetching sensor %s, page %s",
                sensor_id,
                page,
            )

            page_results = self.client.get_hourly_measurements(
                sensor_id=sensor_id,
                datetime_from=datetime_from,
                datetime_to=datetime_to,
                limit=self.measurement_page_size,
                page=page,
            )

            all_measurements.extend(page_results)

            if len(page_results) < self.measurement_page_size:
                break

            page += 1

        if page > max_pages:
            logger.warning(
                "Reached the maximum measurement page limit for sensor %s.",
                sensor_id,
            )

        return all_measurements

    @staticmethod
    def write_json(
        file_path: Path,
        data: dict[str, Any],
    ) -> None:
        """
        Write JSON safely using a temporary file.
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

    def run(
        self,
        datetime_from: str,
        datetime_to: str,
    ) -> dict[str, int]:
        """
        Execute the complete ingestion process.
        """

        self.validate_date_range(
            datetime_from,
            datetime_to,
        )

        run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

        run_dir = self.output_dir / f"run_id={run_id}"

        logger.info("Starting ingestion run: %s", run_id)

        # Step 1: Discover monitoring locations.
        locations = self.discover_locations()

        # Save the location responses before processing sensors.
        self.write_json(
            run_dir / "locations.json",
            {
                "source": "OpenAQ API v3",
                "retrieved_at_utc": datetime.now(UTC).isoformat(),
                "query": {
                    "latitude": self.latitude,
                    "longitude": self.longitude,
                    "radius_m": self.radius_m,
                },
                "results": locations,
            },
        )

        # Step 2: Find PM2.5 sensors.
        sensors = self.discover_pm25_sensors(locations)

        successful_sensors = 0
        failed_sensors = 0
        total_measurements = 0

        # Step 3: Fetch hourly measurements for every PM2.5 sensor.
        for item in sensors:
            location = item["location"]
            sensor = item["sensor"]

            sensor_id = sensor["id"]
            location_id = location["id"]

            try:
                measurements = self.fetch_sensor_measurements(
                    sensor_id=sensor_id,
                    datetime_from=datetime_from,
                    datetime_to=datetime_to,
                )

                # Step 4: Save the returned measurement records.
                output_file = (
                    run_dir
                    / f"location_{location_id}"
                    / f"sensor_{sensor_id}_hours.json"
                )

                self.write_json(
                    output_file,
                    {
                        "source": "OpenAQ API v3",
                        "endpoint": (f"/v3/sensors/{sensor_id}/hours"),
                        "retrieved_at_utc": datetime.now(UTC).isoformat(),
                        "query": {
                            "datetime_from": datetime_from,
                            "datetime_to": datetime_to,
                        },
                        "location": {
                            "id": location_id,
                            "name": location.get("name"),
                            "coordinates": location.get("coordinates"),
                        },
                        "sensor": sensor,
                        "results": measurements,
                    },
                )

                successful_sensors += 1
                total_measurements += len(measurements)

                logger.info(
                    "Saved %s records for sensor %s.",
                    len(measurements),
                    sensor_id,
                )

            except httpx.HTTPStatusError as error:
                status_code = error.response.status_code

                # Authentication failures affect the whole pipeline.
                if status_code in (401, 403):
                    raise

                failed_sensors += 1

                logger.exception(
                    "HTTP error for sensor %s: status %s",
                    sensor_id,
                    status_code,
                )

            except httpx.RequestError:
                failed_sensors += 1

                logger.exception(
                    "Network error while fetching sensor %s.",
                    sensor_id,
                )

        summary = {
            "locations_discovered": len(locations),
            "pm25_sensors_discovered": len(sensors),
            "successful_sensors": successful_sensors,
            "failed_sensors": failed_sensors,
            "total_measurements": total_measurements,
        }

        logger.info("Ingestion summary: %s", summary)

        return summary
