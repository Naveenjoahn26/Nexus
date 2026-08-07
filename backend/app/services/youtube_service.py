"""
NEXUS EDU — YouTube Service.

Isolated YouTube RAG Pipeline.

Design (ChatGPT-style):
- Upload: User pastes a URL. Backend extracts transcript, chunks, embeds, stores in
          ChromaDB + PostgreSQL, tied to the user's course workspace.
- Chat:   User asks any question. Backend automatically uses the most recently uploaded
          YouTube video in the workspace — no video_id required from the user.
"""

from __future__ import annotations

import logging
import re
import urllib.parse
import urllib.request
from typing import Any
import uuid

from youtube_transcript_api import YouTubeTranscriptApi
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm.llm_service import LLMService
from app.ai.llm.router import LLMTaskType
from app.ai.rag.chunking.recursive_chunker import RecursiveChunker, Chunk
from app.ai.rag.embeddings.embedding_service import EmbeddingService
from app.ai.rag.indexing.vector_store import VectorStore
from app.core.config import Settings
from app.crud.youtube import (
    create_youtube_video,
    get_youtube_video_by_video_id,
    get_latest_youtube_video,
)

logger = logging.getLogger(__name__)

YOUTUBE_COLLECTION = "nexus_youtube_rag"


class YouTubeService:
    """
    Dedicated service for YouTube video processing & RAG chat.
    Reuses existing EmbeddingService, VectorStore, and LLMService.
    """

    def __init__(
        self,
        settings: Settings,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        llm_service: LLMService,
    ) -> None:
        self._settings = settings
        self._embedder = embedding_service
        self._vector_store = vector_store
        self._llm = llm_service
        self._chunker = RecursiveChunker(
            child_chunk_size=settings.child_chunk_size,
            child_chunk_overlap=settings.child_chunk_overlap,
            parent_chunk_size=settings.parent_chunk_size,
            parent_chunk_overlap=settings.parent_chunk_overlap,
        )

    @staticmethod
    def extract_video_id(url: str) -> str:
        """Extract YouTube video ID from various URL formats."""
        parsed = urllib.parse.urlparse(url)
        if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
            if parsed.path == "/watch":
                qs = urllib.parse.parse_qs(parsed.query)
                if "v" in qs and qs["v"]:
                    return qs["v"][0]
            elif parsed.path.startswith(("/embed/", "/v/", "/shorts/")):
                parts = parsed.path.split("/")
                if len(parts) >= 3:
                    return parts[2]
        elif parsed.hostname == "youtu.be":
            return parsed.path.lstrip("/").split("?")[0]

        # Regex fallback
        match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
        if match:
            return match.group(1)

        return url

    @staticmethod
    def fetch_video_title(video_id: str) -> str:
        """Fetch video title via oEmbed endpoint."""
        try:
            oembed_url = (
                f"https://www.youtube.com/oembed"
                f"?url=https://www.youtube.com/watch?v={video_id}&format=json"
            )
            req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                import json
                data = json.loads(response.read().decode("utf-8"))
                return data.get("title", f"YouTube Video {video_id}")
        except Exception as err:
            logger.warning("oEmbed title fetch failed for %s: %s", video_id, err)
            return f"YouTube Video {video_id}"

    @staticmethod
    def fetch_transcript(video_id: str) -> str:
        """Extract full transcript text from a YouTube video."""
        try:
            transcript_obj = YouTubeTranscriptApi().fetch(video_id)
            snippets = (
                transcript_obj.snippets
                if hasattr(transcript_obj, "snippets")
                else transcript_obj
            )
            texts = [
                getattr(item, "text", item.get("text", "") if isinstance(item, dict) else str(item))
                for item in snippets
            ]
            return " ".join(texts)
        except AttributeError:
            # Fallback for older API versions
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join([item.get("text", "") for item in transcript_list])
        except Exception as exc:
            logger.error("Transcript fetch failed for %s: %s", video_id, exc)
            raise ValueError(
                f"Could not retrieve transcript for YouTube video '{video_id}'. "
                f"The video may not have captions enabled. Error: {exc}"
            ) from exc

    async def process_youtube_video(
        self, url: str, course_id: uuid.UUID, db: AsyncSession
    ) -> dict[str, Any]:
        """
        Process a YouTube URL end-to-end and tie it to the user's workspace.
        1. Extract video_id & title
        2. Fetch transcript
        3. Store metadata in PostgreSQL (scoped to course_id)
        4. Chunk, embed, and store in ChromaDB (tagged with course_id + video_id)
        """
        video_id = self.extract_video_id(url)
        title = self.fetch_video_title(video_id)
        transcript = self.fetch_transcript(video_id)

        # Persist to DB if not already stored for this workspace
        existing = await get_youtube_video_by_video_id(db, video_id, course_id)
        if not existing:
            await create_youtube_video(
                db=db,
                course_id=course_id,
                video_id=video_id,
                title=title,
                url=url,
                transcript=transcript,
            )

        # Chunk transcript
        raw_doc = Chunk(
            chunk_id=f"yt_{video_id}_raw",
            content=transcript,
            metadata={
                "source": "youtube",
                "video_id": video_id,
                "title": title,
                "url": url,
                "course_id": str(course_id),
            },
        )
        child_chunks, parent_chunks = self._chunker.chunk_documents(
            [raw_doc], document_id=f"yt_{video_id}"
        )

        all_chunks = child_chunks + parent_chunks
        for c in all_chunks:
            c.metadata.update({
                "source": "youtube",
                "video_id": video_id,
                "title": title,
                "url": url,
                "course_id": str(course_id),
            })

        # Embed and store in the shared YouTube collection
        embeddings = await self._embedder.embed_texts([c.content for c in all_chunks])
        await self._vector_store.add_chunks(
            chunks=all_chunks,
            embeddings=embeddings,
            course_id=YOUTUBE_COLLECTION,
        )

        return {
            "message": "YouTube video processed successfully",
            "video_id": video_id,
            "title": title,
            "source": "youtube",
        }

    async def chat(
        self, question: str, course_id: uuid.UUID, db: AsyncSession
    ) -> dict[str, Any]:
        """
        Answer a question using the most recently uploaded YouTube video in the workspace.
        The user only sends a question — video context is resolved automatically.
        """
        # 1. Resolve the latest uploaded video for this workspace
        video_rec = await get_latest_youtube_video(db, course_id)
        if not video_rec:
            raise ValueError(
                "No YouTube video has been uploaded yet. "
                "Please upload a YouTube video first using POST /youtube/upload."
            )

        video_id = video_rec.video_id
        title = video_rec.title
        url = video_rec.url

        # 2. Embed the query
        query_embedding = await self._embedder.embed_query(question)

        # 3. Query ChromaDB filtered strictly by course_id + video_id
        where_filter = {
            "$and": [
                {"source": {"$eq": "youtube"}},
                {"video_id": {"$eq": video_id}},
                {"course_id": {"$eq": str(course_id)}},
            ]
        }

        results = await self._vector_store.query(
            embedding=query_embedding,
            course_id=YOUTUBE_COLLECTION,
            top_k=5,
            where=where_filter,
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not documents:
            # Fallback to raw transcript from DB if vector results are empty
            context_text = video_rec.transcript[:4000]
            logger.info(
                "No vector results found for video '%s', using raw transcript fallback.", video_id
            )
        else:
            context_text = "\n\n".join(
                [f"--- Segment ---\n{doc}" for doc in documents]
            )

        # 4. Generate answer
        system_prompt = (
            "You are an expert AI assistant helping users understand YouTube videos. "
            f"The user is asking about the video: '{title}'. "
            "Answer using only the provided transcript context. "
            "If the information is not in the transcript, say so clearly."
        )
        user_prompt = f"Transcript Context:\n{context_text}\n\nQuestion:\n{question}"

        answer = await self._llm.generate_text(
            service_name="YouTubeService",
            operation="youtube_chat",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            task_type=LLMTaskType.CONTENT_GENERATION,
            temperature=0.3,
        )

        # De-duplicate sources
        seen = set()
        sources = []
        for meta in metadatas:
            if meta and meta.get("video_id") and meta["video_id"] not in seen:
                seen.add(meta["video_id"])
                sources.append({
                    "video_id": meta.get("video_id"),
                    "title": meta.get("title", ""),
                    "url": meta.get("url", ""),
                })

        return {
            "answer": answer,
            "video_title": title,
            "video_url": url,
            "sources": sources,
        }
