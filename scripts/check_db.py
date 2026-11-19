from aqi.storage.database import get_connection


def main() -> None:
    with get_connection() as connection:
        database_info = connection.execute(
            """
            SELECT
                current_database(),
                current_user,
                version();
            """
        ).fetchone()

        table_info = connection.execute(
            """
            SELECT to_regclass(
                'public.air_quality_observations'
            );
            """
        ).fetchone()

    if table_info[0] is None:
        raise RuntimeError(
            "air_quality_observations table does not exist. "
            "Run scripts/init_db.py first."
        )

    print("Database connection successful.")
    print(f"Database: {database_info[0]}")
    print(f"User: {database_info[1]}")
    print(f"PostgreSQL: {database_info[2].split(',')[0]}")
    print(f"Table: {table_info[0]}")


if __name__ == "__main__":
    main()
