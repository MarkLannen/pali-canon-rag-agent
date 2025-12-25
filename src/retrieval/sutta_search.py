"""Sutta search engine for exhaustive semantic search with grouping by sutta."""

from dataclasses import dataclass, field
from typing import Optional

from ..indexing import VectorStoreManager


@dataclass
class SuttaSearchResult:
    """A single sutta's search results, aggregated from multiple chunks."""

    sutta_uid: str
    title: str
    nikaya: str
    best_score: float
    match_count: int  # number of matching chunks in this sutta
    snippets: list[dict] = field(default_factory=list)  # top snippets with metadata


@dataclass
class SearchResults:
    """Complete search results grouped by sutta."""

    query: str
    total_chunks: int  # total chunks retrieved
    sutta_count: int  # number of unique suttas
    results: list[SuttaSearchResult]  # sorted by best_score descending


class SuttaSearchEngine:
    """
    Search engine for exhaustive semantic search across the Sutta Pitaka.

    Unlike the RAG query engine, this performs high-volume retrieval (100-500 chunks)
    and groups results by sutta without LLM synthesis. Useful for finding all suttas
    that mention a topic.
    """

    def __init__(self, vector_store: Optional[VectorStoreManager] = None):
        """
        Initialize the search engine.

        Args:
            vector_store: VectorStoreManager instance. If None, creates a new one.
        """
        self.vector_store = vector_store or VectorStoreManager()

    def search(self, query: str, top_k: int = 200) -> SearchResults:
        """
        Perform exhaustive semantic search and group results by sutta.

        Args:
            query: Search query string
            top_k: Number of chunks to retrieve (default 200, max 500)

        Returns:
            SearchResults with suttas sorted by relevance
        """
        # Clamp top_k to reasonable bounds
        top_k = max(10, min(top_k, 500))

        # Retrieve chunks using vector similarity
        retriever = self.vector_store.index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(query)

        if not nodes:
            return SearchResults(
                query=query,
                total_chunks=0,
                sutta_count=0,
                results=[],
            )

        # Group nodes by sutta_uid
        sutta_groups: dict[str, list] = {}
        for node in nodes:
            uid = node.metadata.get("sutta_uid", "unknown")
            if uid not in sutta_groups:
                sutta_groups[uid] = []
            sutta_groups[uid].append(node)

        # Build results for each sutta
        results = []
        for uid, sutta_nodes in sutta_groups.items():
            # Find best scoring node for this sutta
            best_node = max(sutta_nodes, key=lambda n: n.score)

            # Get top 3 snippets sorted by score
            sorted_nodes = sorted(sutta_nodes, key=lambda n: -n.score)[:3]
            snippets = []
            for node in sorted_nodes:
                snippets.append({
                    "text": node.text[:300] + "..." if len(node.text) > 300 else node.text,
                    "segment_range": node.metadata.get("segment_range", ""),
                    "score": node.score,
                })

            results.append(SuttaSearchResult(
                sutta_uid=uid,
                title=best_node.metadata.get("title", "Unknown"),
                nikaya=best_node.metadata.get("nikaya", ""),
                best_score=best_node.score,
                match_count=len(sutta_nodes),
                snippets=snippets,
            ))

        # Sort by best score descending
        results.sort(key=lambda r: -r.best_score)

        return SearchResults(
            query=query,
            total_chunks=len(nodes),
            sutta_count=len(results),
            results=results,
        )
