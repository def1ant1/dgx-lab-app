from __future__ import annotations

from typing import List

import requests


class EmbeddingClient:
    def __init__(self, base_url: str, model: str, timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def embed(self, text: str) -> List[float]:
        """Get an embedding from Ollama.

        Tries Ollama native endpoint first (/api/embeddings), then OpenAI-compatible (/v1/embeddings).
        """
        # Ollama native
        url = f"{self.base_url}/api/embeddings"
        try:
            r = requests.post(url, json={"model": self.model, "prompt": text}, timeout=self.timeout)
            if r.ok:
                data = r.json()
                emb = data.get("embedding")
                if isinstance(emb, list):
                    return [float(x) for x in emb]
        except Exception:
            pass

        # OpenAI compatible
        url2 = f"{self.base_url}/v1/embeddings"
        r2 = requests.post(url2, json={"model": self.model, "input": text}, timeout=self.timeout)
        r2.raise_for_status()
        data2 = r2.json()
        # expected: {data:[{embedding:[...] }]} 
        emb2 = data2["data"][0]["embedding"]
        return [float(x) for x in emb2]

    def embed_many(self, texts: List[str]) -> List[List[float]]:
        return [self.embed(t) for t in texts]
