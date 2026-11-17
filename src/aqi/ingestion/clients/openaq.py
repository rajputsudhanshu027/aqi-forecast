from __future__ import annotations

from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

BASE_URL = "https://api.openaq.org/v3"


def should_retry(error: BaseException) -> bool:
    """
    Decide whether a failed API request should be retried.
    """

    # Retry network errors and timeouts.
    if isinstance(error, (httpx.TimeoutException, httpx.NetworkError)):
        return True

    # Retry temporary server errors and rate limits.
    if isinstance(error, httpx.HTTPStatusError):
        status_code = error.response.status_code

        return status_code == 429 or 500 <= status_code <= 599

    # Do not retry other errors.
    return False


class OpenAQClient:
    def __init__(
        self,
        api_key: str,
        timeout_seconds: float = 20.0,
    ) -> None:

        if not api_key.strip():
            raise ValueError("OpenAQ API key is missing.")

        self.client = httpx.Client(
            base_url=BASE_URL,
            headers={
                "X-API-Key": api_key,
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(timeout_seconds),
        )

    @retry(
        retry=retry_if_exception(should_retry),
        wait=wait_exponential(
            multiplier=1,
            min=1,
            max=8,
        ),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        response = self.client.get(
            endpoint,
            params=params,
        )

        response.raise_for_status()

        return response.json()

    def get_location(
        self,
        location_id: int,
    ) -> dict[str, Any]:

        data = self._get(f"/locations/{location_id}")

        results = data.get("results", [])

        if not results:
            raise LookupError(f"No location found for ID {location_id}")

        return results[0]

    def get_locations(
        self,
        iso: str = "IN",
        limit: int = 100,
        page: int = 1,
    ) -> list[dict[str, Any]]:

        data = self._get(
            "/locations",
            params={
                "iso": iso,
                "limit": limit,
                "page": page,
            },
        )

        return data.get("results", [])

    def get_locations_near(
        self,
        latitude: float,
        longitude: float,
        radius_m: int = 25000,
        limit: int = 100,
        page: int = 1,
    ) -> list[dict[str, Any]]:

        if not 1 <= radius_m <= 25000:
            raise ValueError("Search radius must be between 1 and 25000 metres.")

        data = self._get(
            "/locations",
            params={
                "coordinates": f"{latitude},{longitude}",
                "radius": radius_m,
                "limit": limit,
                "page": page,
            },
        )

        return data.get("results", [])

    def get_hourly_measurements(
        self,
        sensor_id: int,
        datetime_from: str,
        datetime_to: str,
        limit: int = 1000,
        page: int = 1,
    ) -> list[dict[str, Any]]:

        data = self._get(
            f"/sensors/{sensor_id}/hours",
            params={
                "datetime_from": datetime_from,
                "datetime_to": datetime_to,
                "limit": limit,
                "page": page,
            },
        )

        return data.get("results", [])

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> OpenAQClient:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
