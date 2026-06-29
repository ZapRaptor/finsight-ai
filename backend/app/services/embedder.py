"""
FinSight AI — Vector store and embeddings service.

Wraps Qdrant and sentence-transformers for local, fast semantic search.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Load the embedding model (cached globally after first load)
# all-MiniLM-L6-v2 produces 384-dimensional embeddings
try:
    _model = SentenceTransformer(settings.embedding_model)
    _EMBEDDING_DIM = _model.get_sentence_embedding_dimension() or 384
except Exception as e:
    logger.error("Failed to load SentenceTransformer: %s", e)
    _model = None
    _EMBEDDING_DIM = 384


class EmbedderService:
    def __init__(self):
        kwargs: dict = {"url": settings.qdrant_url}
        if settings.qdrant_api_key:
            kwargs["api_key"] = settings.qdrant_api_key
        self.client = AsyncQdrantClient(**kwargs)

    async def ensure_collection(self, collection_name: str) -> None:
        """Create the Qdrant collection if it doesn't exist."""
        try:
            await self.client.get_collection(collection_name)
        except UnexpectedResponse as e:
            if e.status_code == 404:
                logger.info("Creating Qdrant collection: %s", collection_name)
                await self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=_EMBEDDING_DIM,
                        distance=Distance.COSINE
                    )
                )
            else:
                raise

    async def embed_and_store(self, chunks: list[str], metadatas: list[dict[str, Any]], collection_name: str) -> int:
        """Generate embeddings and store them in Qdrant."""
        if not _model:
            raise RuntimeError("Embedding model not loaded")
            
        if not chunks:
            return 0

        await self.ensure_collection(collection_name)

        # Generate embeddings in a thread to not block the event loop
        import asyncio
        loop = asyncio.get_running_loop()
        embeddings = await loop.run_in_executor(None, _model.encode, chunks)

        points = []
        for chunk, metadata, vector in zip(chunks, metadatas, embeddings):
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector.tolist(),
                    payload={"text": chunk, **metadata}
                )
            )

        # Upsert in batches of 100
        batch_size = 100
        for i in range(0, len(points), batch_size):
            await self.client.upsert(
                collection_name=collection_name,
                points=points[i : i + batch_size]
            )
            
        logger.info("Embedded and stored %d chunks in %s", len(chunks), collection_name)
        return len(chunks)

    async def semantic_search(self, query: str, collection_name: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Search Qdrant for the most relevant chunks."""
        if not _model:
            raise RuntimeError("Embedding model not loaded")

        try:
            # Check if collection exists first
            await self.client.get_collection(collection_name)
        except UnexpectedResponse as e:
            if e.status_code == 404:
                logger.warning("Collection %s does not exist yet.", collection_name)
                return []
            raise

        import asyncio
        loop = asyncio.get_running_loop()
        query_vector = await loop.run_in_executor(None, _model.encode, query)

        search_result = await self.client.search(
            collection_name=collection_name,
            query_vector=query_vector.tolist(),
            limit=top_k
        )

        results = []
        for hit in search_result:
            if hit.payload:
                results.append(hit.payload)
                
        return results

# Singleton instance
embedder = EmbedderService()
