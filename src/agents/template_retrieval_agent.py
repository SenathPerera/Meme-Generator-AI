import requests
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np

# OpenAI + fallback embeddings
from src.utils.openai_client import openai_embed, openai_plan_search
from src.agents.utils_fallbacks import embed_texts as fallback_embed


@dataclass
class TemplateItem:
    id: str
    name: str
    url: str
    source: str


class TemplateRetrievalAgent:
    """
    Retrieves meme templates from multiple APIs, merges, ranks, and returns top-k.

    Planning:
      - openai_plan_search(context) -> {"search_prompt": "...", "tags": [...]}

    Embeddings:
      - Primary: OpenAI (paid) via openai_embed
      - Fallback: Sentence-Transformer / TF-IDF via utils_fallbacks.embed_texts

    Sources:
      - Imgflip: https://api.imgflip.com/get_memes
      - Memegen: https://api.memegen.link/templates/
      - Reddit : https://meme-api.com/gimme/50
    """

    # ---------- Template Fetchers ----------
    def fetch_imgflip(self) -> List[TemplateItem]:
        try:
            r = requests.get("https://api.imgflip.com/get_memes", timeout=10)
            r.raise_for_status()
            data = r.json().get("data", {}).get("memes", [])
            return [TemplateItem(str(d["id"]), d["name"], d["url"], "imgflip") for d in data]
        except Exception as e:
            print("⚠️ Imgflip fetch failed:", e)
            return []

    def fetch_memegen(self) -> List[TemplateItem]:
        try:
            r = requests.get("https://api.memegen.link/templates/", timeout=10)
            r.raise_for_status()
            data = r.json()
            # "id" is slug; "blank" is the empty image URL
            return [
                TemplateItem(d["id"], d.get("name", d["id"]), d["blank"], "memegen")
                for d in data
                if "id" in d and "blank" in d
            ]
        except Exception as e:
            print("⚠️ Memegen fetch failed:", e)
            return []

    def fetch_reddit(self) -> List[TemplateItem]:
        try:
            r = requests.get("https://meme-api.com/gimme/50", timeout=10)
            r.raise_for_status()
            data = r.json().get("memes", [])
            return [
                TemplateItem(str(i), d.get("title", "meme"), d.get("url", ""), "reddit")
                for i, d in enumerate(data)
                if d.get("url")
            ]
        except Exception as e:
            print("⚠️ Reddit fetch failed:", e)
            return []

    def _fetch_pool(self) -> List[TemplateItem]:
        pool: List[TemplateItem] = []
        pool += self.fetch_imgflip()
        pool += self.fetch_memegen()
        pool += self.fetch_reddit()
        # filter invalid
        return [p for p in pool if p.url and p.name]

    # ---------- Retrieval Core ----------
    def retrieve(
        self,
        search_prompt: str,
        top_k: int = 10,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Rank templates most semantically similar to the search prompt.
        Adds a small keyword/tag-overlap bonus to the embedding score.
        """
        pool = self._fetch_pool()
        if not pool or not (search_prompt or "").strip():
            return []

        names = [t.name for t in pool]
        all_texts = names + [search_prompt]

        # Embeddings with fallback
        try:
            vecs_all = openai_embed(all_texts)
        except Exception as e:
            print("⚠️ OpenAI embedding error, falling back:", e)
            vecs_all = fallback_embed(all_texts)

        vecs = vecs_all[:-1]
        q = vecs_all[-1]

        # cosine similarity
        denom = (np.linalg.norm(vecs, axis=1) * (np.linalg.norm(q) + 1e-10)) + 1e-10
        sims = np.dot(vecs, q) / denom

        # Tag overlap bonus (very small, bounded)
        tags = [t.lower() for t in (tags or []) if t]
        bonus = np.zeros_like(sims)
        if tags:
            for i, nm in enumerate(names):
                lo = " " + nm.lower() + " "
                hits = sum(1 for t in tags if t in lo)
                if hits:
                    bonus[i] = 0.05 * min(3, hits)  # up to +0.15

        score = sims + bonus
        idxs = np.argsort(-score)[:top_k]

        out: List[Dict[str, Any]] = []
        for i in idxs:
            t = pool[int(i)]
            out.append(
                {
                    "id": t.id,
                    "name": t.name,
                    "url": t.url,
                    "source": t.source,
                    "score": float(score[int(i)]),
                }
            )
        return out

    # ---------- Context-first convenience ----------
    def retrieve_from_context(self, context: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Uses OpenAI to plan search terms/tags from raw user context,
        then calls retrieve(search_prompt, tags).
        """
        plan = openai_plan_search(context or "")
        search_prompt = (plan.get("search_prompt") or context or "").strip()
        tags = plan.get("tags") or []
        return self.retrieve(search_prompt=search_prompt, top_k=top_k, tags=tags)
