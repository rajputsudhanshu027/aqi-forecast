import pytest

from aqi.storage.database import get_database_url


def test_get_database_url_reads_environment(monkeypatch):
    expected_url = "postgresql://test_user:test_password@localhost:5432/test_db"

    monkeypatch.setattr(
        "aqi.storage.database.load_dotenv",
        lambda: None,
    )

    monkeypatch.setenv("DATABASE_URL", expected_url)

    assert get_database_url() == expected_url


def test_get_database_url_requires_configuration(monkeypatch):
    monkeypatch.setattr(
        "aqi.storage.database.load_dotenv",
        lambda: None,
    )

    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        get_database_url()
