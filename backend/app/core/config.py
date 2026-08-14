"""
NEXUS EDU — Application Configuration.

Centralized settings loaded from environment variables and .env file.
Uses pydantic-settings for validation and type coercion.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── Application ──────────────────────────────────────────────
    app_name: str = "NEXUS_EDU"
    app_env: str = "development"
    debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # ── CORS ────────────────────────────────────────────────────
    cors_origins: str | list[str] = [
        "https://nexus-ai-1-cmi1.onrender.com",
        "https://nexus-ai-a1-cmi1.onrender.com",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    def get_cors_origins(self) -> list[str]:
        defaults = [
            "https://nexus-ai-1-cmi1.onrender.com",
            "https://nexus-ai-a1-cmi1.onrender.com",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
        if isinstance(self.cors_origins, str):
            extra = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
            for item in extra:
                if item not in defaults:
                    defaults.append(item)
            return defaults
        elif isinstance(self.cors_origins, list):
            for item in self.cors_origins:
                if item not in defaults:
                    defaults.append(item)
            return defaults
        return defaults

    # ── LLM Providers ───────────────────────────────────────────
    groq_api_key: str = ""

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
    llm_model_metadata: str = "llama-3.3-70b-versatile"
    llm_model_json: str = "llama-3.3-70b-versatile"
    llm_model_content: str = "llama-3.3-70b-versatile"
    
    # Instructor retry limit for malformed Pydantic responses
    llm_max_retries: int = 3

    # ── Storage ─────────────────────────────────────────────────
    chroma_persist_dir: str = "app/storage/chromadb"
    upload_dir: str = "app/storage/uploads"
    generated_dir: str = "app/storage/generated"
    temp_dir: str = "app/storage/temp"

    # ── Database ────────────────────────────────────────────────
    # Async URL — used by SQLAlchemy async engine (FastAPI, services)
    database_url: str = "postgresql+asyncpg://postgres:nimal@localhost:5432/NexusAI"
    # Sync URL — used only by Alembic for schema migrations
    database_url_sync: str = "postgresql+psycopg2://postgres:nimal@localhost:5432/NexusAI"
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
