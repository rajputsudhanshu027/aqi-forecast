import argparse
import logging
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

from aqi.ingestion.clients.openaq import OpenAQClient
from aqi.ingestion.pipeline import OpenAQIngestionPipeline

# Find the project root directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:

    parser = argparse.ArgumentParser(description="Run OpenAQ PM2.5 data ingestion.")

    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of past days to download.",
    )

    parser.add_argument(
        "--radius-m",
        type=int,
        default=25000,
        help="Search radius around Delhi, in metres.",
    )

    args = parser.parse_args()

    if args.days < 1:
        parser.error("--days must be at least 1.")

    if not 1 <= args.radius_m <= 25000:
        parser.error("--radius-m must be between 1 and 25000.")

    # Configure logging.
    logging.basicConfig(
        level=logging.INFO,
        format=("%(asctime)s | %(levelname)s | %(name)s | %(message)s"),
    )

    logger = logging.getLogger(__name__)

    # Load environment variables.
    load_dotenv(PROJECT_ROOT / ".env")

    api_key = os.getenv("OPENAQ_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAQ_API_KEY is missing from the .env file.")

    # Calculate the date range in UTC.
    datetime_to = datetime.now(UTC)

    datetime_from = datetime_to - timedelta(days=args.days)

    start = datetime_from.isoformat().replace("+00:00", "Z")
    end = datetime_to.isoformat().replace("+00:00", "Z")

    logger.info("Ingestion date range: %s to %s", start, end)

    # Create the API client and execute the pipeline.
    with OpenAQClient(api_key=api_key) as client:
        pipeline = OpenAQIngestionPipeline(
            client=client,
            output_dir=PROJECT_ROOT / "data" / "raw" / "openaq",
            latitude=28.6139,
            longitude=77.2090,
            radius_m=args.radius_m,
        )

        summary = pipeline.run(
            datetime_from=start,
            datetime_to=end,
        )

    logger.info("Final ingestion summary: %s", summary)

    if summary["failed_sensors"] > 0:
        raise SystemExit("Ingestion completed with sensor failures. Check the logs.")


if __name__ == "__main__":
    main()
