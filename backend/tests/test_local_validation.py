import os
from pathlib import Path

from fastapi.testclient import TestClient

from app.ai.rag.loaders.text_loader import TextLoader
from app.core.config import Settings


def test_settings_debug_flag_parses_release() -> None:
    original = os.environ.get("DEBUG")
    os.environ["DEBUG"] = "release"
    try:
        settings = Settings()
        assert settings.debug is False
    finally:
        if original is None:
            os.environ.pop("DEBUG", None)
        else:
            os.environ["DEBUG"] = original


def test_text_loader_loads_sample_markdown() -> None:
    file_path = Path(__file__).parent / "data" / "sample_course_notes.md"
    result = __import__("asyncio").run(TextLoader().load(str(file_path)))

    assert len(result) == 1
    assert "Artificial intelligence" in result[0].content
    assert "Machine learning" in result[0].content


def test_health_endpoint_smoke() -> None:
    os.environ.setdefault("GROQ_API_KEY", "mock-groq-key-for-local-tests")
    from app.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
