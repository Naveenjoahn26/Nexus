"""
NEXUS EDU — Application Configuration.

Centralized settings loaded from environment variables and .env file.
Uses pydantic-settings for validation and type coercion.
"""

from __future__ import annotations

from functools import lru_cache

from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = str(Path(__file__).resolve().parents[2] / ".env")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(_ENV_FILE, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("debug", mode="before")
    @classmethod
    def _coerce_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "prod"}:
                return False
        return value

    # ── Application ──────────────────────────────────────────────
    app_name: str = "NEXUS_EDU"
    app_env: str = "development"
    debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # ── CORS ────────────────────────────────────────────────────
    cors_origins: str | list[str] = [
        "https://nexus-ai-b1gb.onrender.com",
        "https://nexus-ai-1-b1gb.onrender.com",
        "https://nexus-ai-1-cmi1.onrender.com",
        "https://nexus-ai-a1-cmi1.onrender.com",
        "https://nexus-ai-silk-ten.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://[::1]:5173",
        "http://[::1]:3000",
    ]
    cors_origin_regex: str = r"^https?://([a-zA-Z0-9-]+\.)*(localhost|127\.0\.0\.1|\[::1\]|onrender\.com|vercel\.app)(:\d+)?$"

    def get_cors_origins(self) -> list[str]:
        defaults = [
            "https://nexus-ai-b1gb.onrender.com",
            "https://nexus-ai-1-b1gb.onrender.com",
            "https://nexus-ai-1-cmi1.onrender.com",
            "https://nexus-ai-a1-cmi1.onrender.com",
            "https://nexus-ai-silk-ten.vercel.app",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://[::1]:5173",
            "http://[::1]:3000",
        ]
        origins = list(defaults)
        raw_list: list[str] = []
        if isinstance(self.cors_origins, str):
            raw_list = [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip()]
        elif isinstance(self.cors_origins, list):
            raw_list = [o.strip().rstrip("/") if isinstance(o, str) else str(o) for o in self.cors_origins]

        for item in raw_list:
            if item and item not in origins:
                origins.append(item)
        return origins

    # ── LLM Providers ───────────────────────────────────────────
    groq_api_key: str = ""
    hf_token: str = ""

    # ── Embedding Model ─────────────────────────────────────────
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    embedding_dimension: int = 384
    embedding_batch_size: int = 64

    # ── Reranker Model ──────────────────────────────────────────
    reranker_model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # ── RAG Pipeline ─────────────────────────────────────────────
    child_chunk_size: int = 512
    child_chunk_overlap: int = 50
    parent_chunk_size: int = 1500
    parent_chunk_overlap: int = 100
    rrf_k_constant: int = 60
    dense_top_k: int = 20
    sparse_top_k: int = 20
    rerank_top_k: int = 5
    mmr_lambda: float = 0.7

    # ── LLM Core (AI Router & Groq) ──────────────────────────────
    # Models mapped to specific AI Router roles
    llm_model_metadata: str = "qwen/qwen3.8-27b"
    llm_model_json: str = "qwen/qwen3.8-27b"
    llm_model_content: str = "qwen/qwen3.8-27b"
    
    # Instructor retry limit for malformed Pydantic responses
    llm_max_retries: int = 3

    # ── Storage ─────────────────────────────────────────────────
    chroma_persist_dir: str = "app/storage/chromadb"
    upload_dir: str = "app/storage/uploads"
    generated_dir: str = "app/storage/generated"
    temp_dir: str = "app/storage/temp"

    # ── Database ────────────────────────────────────────────────
    # Async URL — used by SQLAlchemy async engine (FastAPI, services)
    database_url: str = "postgresql+asyncpg://postgres:12345@localhost:5432/nexus"
    # Sync URL — used only by Alembic for schema migrations
    database_url_sync: str = "postgresql+psycopg2://postgres:12345@localhost:5432/nexus"
    # Connection pool settings
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800  # recycle connections after 30 min

    # ── Security ────────────────────────────────────────────────
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
