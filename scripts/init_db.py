from pathlib import Path

from aqi.storage.database import get_connection

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SCHEMA_PATH = PROJECT_ROOT / "src" / "aqi" / "storage" / "schema.sql"


def main() -> None:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Database schema not found: {SCHEMA_PATH}")

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

    statements = [
        statement.strip() for statement in schema_sql.split(";") if statement.strip()
    ]

    with get_connection() as connection:
        for statement in statements:
            connection.execute(statement)

    print("Database schema initialized successfully.")


if __name__ == "__main__":
    main()
