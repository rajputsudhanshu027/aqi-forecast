import argparse
import logging
from datetime import UTC, datetime
from pathlib import Path

from aqi.ingestion.validation.validator import (
    validate_raw_file,
    write_json_atomic,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def find_latest_run(raw_root: Path) -> Path:

    run_directories = sorted(
        path for path in raw_root.glob("run_id=*") if path.is_dir()
    )

    if not run_directories:
        raise FileNotFoundError(f"No ingestion runs found in {raw_root}")

    return run_directories[-1]


def main() -> None:

    parser = argparse.ArgumentParser(description="Validate OpenAQ ingestion data.")

    parser.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help="Specific raw ingestion run directory.",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format=("%(asctime)s | %(levelname)s | %(name)s | %(message)s"),
    )

    logger = logging.getLogger(__name__)

    raw_root = PROJECT_ROOT / "data" / "raw" / "openaq"

    output_root = PROJECT_ROOT / "data" / "validated" / "openaq"

    # Select the requested run or automatically use the latest.
    raw_run_dir = (
        args.run_dir if args.run_dir is not None else find_latest_run(raw_root)
    )

    if not raw_run_dir.is_absolute():
        raw_run_dir = PROJECT_ROOT / raw_run_dir

    if not raw_run_dir.is_dir():
        raise FileNotFoundError(f"Run directory does not exist: {raw_run_dir}")

    # Keep the validation output separate from raw data.
    output_run_dir = output_root / raw_run_dir.name

    sensor_files = sorted(raw_run_dir.glob("location_*/sensor_*_hours.json"))

    if not sensor_files:
        raise FileNotFoundError(f"No sensor measurement files found in {raw_run_dir}")

    total_records = 0
    accepted_records = 0
    rejected_records = 0
    warning_count = 0

    file_summaries = []

    for raw_file in sensor_files:
        relative_path = raw_file.relative_to(raw_run_dir)

        output_file = (
            output_run_dir / relative_path.parent / f"{raw_file.stem}_validation.json"
        )

        result = validate_raw_file(
            raw_file=raw_file,
            output_file=output_file,
        )

        total_records += result["total_records"]
        accepted_records += result["accepted_count"]
        rejected_records += result["rejected_count"]
        warning_count += result["warning_count"]

        file_summaries.append(
            {
                "source_file": str(relative_path),
                "total_records": result["total_records"],
                "accepted_records": result["accepted_count"],
                "rejected_records": result["rejected_count"],
                "warnings": result["warning_count"],
                "rejection_reasons": result["rejection_reasons"],
            }
        )

    # Create a summary for the entire ingestion run.
    quality_report = {
        "run_id": raw_run_dir.name,
        "validated_at_utc": datetime.now(UTC).isoformat(),
        "sensor_files_processed": len(sensor_files),
        "total_records": total_records,
        "accepted_records": accepted_records,
        "rejected_records": rejected_records,
        "warning_count": warning_count,
        "acceptance_rate": (
            round(accepted_records / total_records, 4) if total_records else 0
        ),
        "files": file_summaries,
    }

    report_path = output_run_dir / "quality_report.json"

    write_json_atomic(
        report_path,
        quality_report,
    )

    logger.info(
        "Validation complete: total=%s accepted=%s rejected=%s warnings=%s",
        total_records,
        accepted_records,
        rejected_records,
        warning_count,
    )

    logger.info(
        "Quality report saved to %s",
        report_path,
    )

    if accepted_records == 0:
        raise SystemExit(
            "No valid measurements were found. Do not continue to database ingestion."
        )


if __name__ == "__main__":
    main()
