import hashlib
import math
from typing import List
from app.core.config import settings
from app.core.logging import logger


class EmbeddingService:
    """Configurable embedding generator supporting synthetic deterministic hashes and OpenAI."""

    @staticmethod
    def get_embedding(text: str) -> List[float]:
        """Returns normalized 128-dimensional embedding vector."""
        if settings.EMBEDDING_PROVIDER.lower() == "openai" and settings.OPENAI_API_KEY:
            try:
                import httpx
                headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
                payload = {"input": text, "model": settings.OPENAI_EMBEDDING_MODEL}
                with httpx.Client(timeout=10.0) as client:
                    res = client.post("https://api.openai.com/v1/embeddings", json=payload, headers=headers)
                    if res.status_code == 200:
                        return res.json()["data"][0]["embedding"]
            except Exception as e:
                logger.warning(f"OpenAI embedding generation failed ({str(e)}). Using deterministic mock.")

        # Synthetic Deterministic 128-dim vector from SHA-256 for offline test consistency
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vec = []
        for i in range(128):
            byte_val = h[i % len(h)]
            # normalize around 0.0 with unit length
            val = ((byte_val / 255.0) - 0.5) * 2.0
            vec.append(val)
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]
