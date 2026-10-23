import os
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger
from app.ai.embeddings.service import EmbeddingService


class VectorStoreService:
    """
    Manages semantic document chunk storage and retrieval.
    Enforces strict patient-isolated metadata boundaries.
    """

    def __init__(self):
        self.collection_name = f"{settings.CHROMA_COLLECTION_PREFIX}clinical_docs"
        self._in_memory_docs: List[Dict[str, Any]] = []
        self._chroma_client = None
        self._init_chroma()

    def _init_chroma(self):
        """Attempts to initialize remote ChromaDB client; falls back to in-memory store if unreachable."""
        try:
            import chromadb
            # If running in Docker or host with ChromaDB HTTP server
            if settings.CHROMA_HOST:
                self._chroma_client = chromadb.HttpClient(
                    host=settings.CHROMA_HOST,
                    port=settings.CHROMA_PORT
                )
                self._collection = self._chroma_client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"description": "Digital Doctor Clinical Knowledge and Patient Encounter Index"}
                )
                logger.info(f"Connected to ChromaDB at {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
        except Exception as e:
            logger.info(f"ChromaDB service not available ({str(e)}). Utilizing resilient in-memory vector store.")
            self._chroma_client = None

    def index_document(
        self,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Indexes a document chunk with strict metadata.
        metadata must include:
            - patient_id (int or None for public guidelines)
            - is_public (bool)
            - doc_type (e.g. EncounterNote, LabReport, Guideline)
            - title (str)
            - author (str)
        """
        embedding = EmbeddingService.get_embedding(content)
        entry = {
            "id": doc_id,
            "content": content,
            "metadata": metadata,
            "embedding": embedding
        }
        self._in_memory_docs.append(entry)

        if self._chroma_client:
            try:
                # Chroma requires strings, bools, ints, floats for metadata values
                sanitized_meta = {k: v for k, v in metadata.items() if v is not None}
                self._collection.upsert(
                    ids=[doc_id],
                    documents=[content],
                    metadatas=[sanitized_meta],
                    embeddings=[embedding]
                )
            except Exception as e:
                logger.warning(f"Failed to index to ChromaDB: {str(e)}")

        return True

    def search_authorized(
        self,
        query: str,
        patient_id: int,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic vector search with strict patient boundary authorization.
        Only chunks where `patient_id == patient_id` OR `is_public == True` are returned.
        """
        query_embedding = EmbeddingService.get_embedding(query)
        results = []

        # Use in-memory retrieval (or ChromaDB results filtered by patient boundary)
        candidates = []
        for doc in self._in_memory_docs:
            doc_patient = doc["metadata"].get("patient_id")
            is_public = doc["metadata"].get("is_public", False)

            # Mandatory Authorization Boundary Filter
            if doc_patient == patient_id or is_public:
                # Cosine similarity score calculation
                dot_prod = sum(a * b for a, b in zip(query_embedding, doc["embedding"]))
                candidates.append((dot_prod, doc))

        candidates.sort(key=lambda x: x[0], reverse=True)

        for score, doc in candidates[:limit]:
            results.append({
                "id": doc["id"],
                "score": float(score),
                "title": doc["metadata"].get("title", "Clinical Record"),
                "date": doc["metadata"].get("date", "2026-01-01"),
                "author": doc["metadata"].get("author", "Attending Clinician"),
                "type": doc["metadata"].get("doc_type", "Clinical Note"),
                "source": doc["metadata"].get("source", "CLINICIAN"),
                "snippet": doc["content"][:300],
                "metadata": doc["metadata"]
            })

        logger.info(
            f"[VECTOR SEARCH] Query='{query[:30]}...' PatientId={patient_id} "
            f"Returned {len(results)} authorized documents."
        )
        return results


vector_store = VectorStoreService()
