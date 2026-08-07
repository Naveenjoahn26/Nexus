"""
NEXUS EDU — RAG Pipeline Orchestrator.

Single entry point for all RAG operations. All downstream services
(chat, lecture, question paper, PPT, analysis) call this pipeline.

    pipeline = RAGPipeline()

    # Ingest a document
    result = await pipeline.ingest("doc_123", "/path/to/file.pdf", "course_456")

    # Retrieve relevant context
    chunks = await pipeline.retrieve("What is polymorphism?", "course_456")

    # Delete a document
    await pipeline.delete_document("doc_123", "course_456")

The pipeline composes all RAG components — it does not implement
retrieval logic itself. Each component is independently testable.
"""

from __future__ import annotations

import logging

from app.ai.rag.chunking.recursive_chunker import RecursiveChunker
from app.ai.rag.embeddings.embedding_service import EmbeddingService
from app.ai.rag.indexing.bm25_index import BM25Index
from app.ai.rag.indexing.vector_store import VectorStore
from app.ai.rag.loaders.factory import get_loader
from app.ai.rag.rerankers.reranker import Reranker
from app.ai.rag.retrieval.dense_retriever import DenseRetriever
from app.ai.rag.retrieval.hybrid_retriever import HybridRetriever
from app.ai.rag.retrieval.sparse_retriever import SparseRetriever
from app.core.config import Settings, get_settings
from app.core.exceptions import IngestionError, RetrievalError
from app.schemas.common import IngestResult, RetrievedChunk

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Production RAG pipeline for NEXUS EDU.

    Orchestrates ingestion (load → chunk → embed → index) and
    retrieval (hybrid search → rerank → MMR → parent expansion).

    Designed to be instantiated once at application startup and
    shared across all request handlers via dependency injection.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

        # ── Component initialization ─────────────────────────────
        self._embedder = EmbeddingService(self._settings)
        self._vector_store = VectorStore(self._settings)
        self._bm25_index = BM25Index(self._vector_store)
        self._chunker = RecursiveChunker(
            child_chunk_size=self._settings.child_chunk_size,
            child_chunk_overlap=self._settings.child_chunk_overlap,
            parent_chunk_size=self._settings.parent_chunk_size,
            parent_chunk_overlap=self._settings.parent_chunk_overlap,
        )
        self._reranker = Reranker(self._settings)

        # ── Retriever chain ──────────────────────────────────────
        dense = DenseRetriever(self._embedder, self._vector_store)
        sparse = SparseRetriever(self._bm25_index)
        self._hybrid = HybridRetriever(
            dense_retriever=dense,
            sparse_retriever=sparse,
            rrf_k=self._settings.rrf_k_constant,
        )

        logger.info("RAG pipeline initialized.")

    # ══════════════════════════════════════════════════════════════
    # INGESTION
    # ══════════════════════════════════════════════════════════════

    async def ingest(
        self,
        document_id: str,
        file_path: str,
        course_id: str,
        metadata: dict | None = None,
    ) -> IngestResult:
        """
        Ingest a document into the RAG pipeline.

        Flow: Load → Chunk (parent + child) → Embed → Store → Invalidate BM25.

        Args:
            document_id: Unique identifier for the document.
            file_path: Absolute path to the file on disk.
            course_id: Course this document belongs to.
            metadata: Optional extra metadata to attach to all chunks.

        Returns:
            IngestResult with chunk counts and status.

        Raises:
            IngestionError: If any stage of the pipeline fails.
        """
        extra_meta = metadata or {}
        logger.info(
            "Ingesting document '%s' into course '%s' from '%s'.",
            document_id,
            course_id,
            file_path,
        )

        try:
            # 1. LOAD — auto-detect format and extract text.
            loader = get_loader(file_path)
            raw_documents = await loader.load(file_path)
            logger.debug(
                "Loaded %d raw document(s) from '%s'.",
                len(raw_documents),
                file_path,
            )

            # 2. CHUNK — create parent and child chunks.
            child_chunks, parent_chunks = self._chunker.chunk_documents(
                raw_documents, document_id
            )

            # Inject course_id and any extra metadata.
            for chunk in child_chunks + parent_chunks:
                chunk.metadata["course_id"] = course_id
                chunk.metadata.update(extra_meta)

            # 3. EMBED — generate vectors for both child and parent chunks.
            child_embeddings = await self._embedder.embed_texts(
                [c.content for c in child_chunks]
            )
            parent_embeddings = await self._embedder.embed_texts(
                [p.content for p in parent_chunks]
            )

            # 4. STORE — upsert into ChromaDB.
            await self._vector_store.add_chunks(
                child_chunks, child_embeddings, course_id
            )
            await self._vector_store.add_chunks(
                parent_chunks, parent_embeddings, course_id
            )

            # 5. INVALIDATE — force BM25 rebuild on next query.
            self._bm25_index.invalidate(course_id)

            result = IngestResult(
                document_id=document_id,
                chunk_count=len(child_chunks) + len(parent_chunks),
                child_chunk_count=len(child_chunks),
                parent_chunk_count=len(parent_chunks),
            )
            logger.info(
                "Ingestion complete for '%s': %d child + %d parent chunks.",
                document_id,
                len(child_chunks),
                len(parent_chunks),
            )
            return result

        except IngestionError:
            raise
        except Exception as exc:
            logger.error(
                "Ingestion failed for document '%s': %s", document_id, exc
            )
            raise IngestionError(document_id, str(exc)) from exc

    # ══════════════════════════════════════════════════════════════
    # RETRIEVAL
    # ══════════════════════════════════════════════════════════════

    async def retrieve(
        self,
        query: str,
        course_id: str,
        top_k: int | None = None,
        use_parent: bool = False,
        use_mmr: bool = True,
    ) -> list[RetrievedChunk]:
        """
        Retrieve relevant chunks for a query.

        Flow: Hybrid (Dense + BM25) → Rerank → MMR → Parent Expansion.

        Args:
            query: The search query.
            course_id: Course to search within.
            top_k: Final number of results (defaults to settings.rerank_top_k).
            use_parent: If True, expand child chunks to parent chunks
                        for richer context.
            use_mmr: If True, apply MMR diversity selection after reranking.

        Returns:
            List of RetrievedChunks, sorted by relevance.

        Raises:
            RetrievalError: If any stage fails.
        """
        top_k = top_k or self._settings.rerank_top_k

        try:
            # 1. HYBRID RETRIEVAL — dense + sparse with RRF fusion.
            candidates = await self._hybrid.retrieve(
                query=query,
                course_id=course_id,
                dense_top_k=self._settings.dense_top_k,
                sparse_top_k=self._settings.sparse_top_k,
                final_top_k=self._settings.dense_top_k,
            )

            if not candidates:
                logger.info("No results for query in course '%s'.", course_id)
                return []

            # 2. RERANK — cross-encoder scoring, optionally with MMR.
            if use_mmr and len(candidates) > top_k:
                # Fetch embeddings directly from vector store to avoid re-computation overhead.
                cached_data = await self._vector_store.get_embeddings_by_ids(
                    [c.chunk_id for c in candidates], course_id
                )
                
                # Map chunk_id -> embedding
                embedding_map = {}
                for idx, cid in enumerate(cached_data.get("ids", [])):
                    cached_emb = cached_data.get("embeddings")
                    if cached_emb is not None and idx < len(cached_emb):
                        embedding_map[cid] = cached_emb[idx]
                
                # Retrieve embeddings in the same order as candidates.
                candidate_embeddings = []
                missing_chunks = []
                for c in candidates:
                    if c.chunk_id in embedding_map:
                        candidate_embeddings.append(embedding_map[c.chunk_id])
                    else:
                        missing_chunks.append(c)
                
                # Fallback: compute for any chunks missing embeddings (rare)
                if missing_chunks:
                    logger.debug("Generating embeddings for %d candidates missing from cache.", len(missing_chunks))
                    missing_embeddings = await self._embedder.embed_texts([c.content for c in missing_chunks])
                    
                    final_embeddings = []
                    missing_idx = 0
                    for c in candidates:
                        if c.chunk_id in embedding_map:
                            final_embeddings.append(embedding_map[c.chunk_id])
                        else:
                            final_embeddings.append(missing_embeddings[missing_idx])
                            missing_idx += 1
                    candidate_embeddings = final_embeddings
                results = await self._reranker.rerank_with_mmr(
                    query=query,
                    chunks=candidates,
                    embeddings=candidate_embeddings,
                    top_k=top_k,
                    mmr_lambda=self._settings.mmr_lambda,
                )
            else:
                results = await self._reranker.rerank(
                    query=query,
                    chunks=candidates,
                    top_k=top_k,
                )

            # 3. PARENT EXPANSION — replace children with broader parent context.
            if use_parent and results:
                results = await self._expand_to_parents(results, course_id)

            logger.info(
                "Retrieved %d chunks for query in course '%s'.",
                len(results),
                course_id,
            )
            return results

        except RetrievalError:
            raise
        except Exception as exc:
            logger.error("Retrieval failed: %s", exc)
            raise RetrievalError(str(exc)) from exc

    async def _expand_to_parents(
        self,
        chunks: list[RetrievedChunk],
        course_id: str,
    ) -> list[RetrievedChunk]:
        """
        Replace child chunks with their parent chunks.

        Deduplicates parents — if multiple children share the same parent,
        only one copy of the parent is returned (preserving the highest-
        scoring child's score).
        """
        # Collect unique parent IDs in order.
        parent_ids: list[str] = []
        seen_parents: set[str] = set()
        child_scores: dict[str, float] = {}  # parent_id → best child score

        for chunk in chunks:
            pid = chunk.metadata.get("parent_id")
            if pid and pid not in seen_parents:
                parent_ids.append(pid)
                seen_parents.add(pid)
                child_scores[pid] = chunk.score
            elif pid and pid in seen_parents:
                # Keep the highest child score for this parent.
                child_scores[pid] = max(child_scores[pid], chunk.score)

        if not parent_ids:
            return chunks  # No parent links — return children as-is.

        # Fetch parent content from ChromaDB.
        parent_data = await self._vector_store.get_by_ids(parent_ids, course_id)

        parent_texts: dict[str, str] = {}
        parent_metas: dict[str, dict] = {}
        for pid, text, meta in zip(
            parent_data.get("ids", []),
            parent_data.get("documents", []),
            parent_data.get("metadatas", []),
        ):
            parent_texts[pid] = text or ""
            parent_metas[pid] = meta or {}

        # Build expanded result list.
        expanded: list[RetrievedChunk] = []
        for pid in parent_ids:
            if pid in parent_texts:
                expanded.append(
                    RetrievedChunk(
                        chunk_id=pid,
                        content=parent_texts[pid],
                        score=child_scores.get(pid, 0.0),
                        metadata={
                            **parent_metas.get(pid, {}),
                            "chunk_type": "parent",
                            "expanded": True,
                        },
                    )
                )

        # Append any child chunks that had no parent link (true orphans).
        for chunk in chunks:
            pid = chunk.metadata.get("parent_id")
            if not pid:  # child with no parent link is an orphan
                expanded.append(chunk)

        # Fallback: if expansion found nothing, return original child chunks.
        if not expanded:
            logger.warning(
                "Parent expansion returned no results for course '%s'. "
                "Falling back to child chunks.",
                course_id,
            )
            return chunks

        return expanded

    # ══════════════════════════════════════════════════════════════
    # DELETION
    # ══════════════════════════════════════════════════════════════

    async def delete_document(self, document_id: str, course_id: str) -> int:
        """
        Remove a document and all its chunks from the pipeline.

        Args:
            document_id: ID of the document to remove.
            course_id: Course the document belongs to.

        Returns:
            Number of chunks deleted.
        """
        count = await self._vector_store.delete_document(document_id, course_id)
        self._bm25_index.invalidate(course_id)
        logger.info(
            "Deleted document '%s' (%d chunks) from course '%s'.",
            document_id,
            count,
            course_id,
        )
        return count

    async def delete_course(self, course_id: str) -> None:
        """Remove all data for a course (all documents, all chunks)."""
        await self._vector_store.delete_course(course_id)
        self._bm25_index.invalidate(course_id)
        logger.info("Deleted all data for course '%s'.", course_id)
