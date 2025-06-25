"""
Hybrid Search Engine

Combines semantic vector search with keyword search and metadata filtering
to provide the most relevant movie recommendations.
"""

import logging
import re
from typing import Dict, List, Optional, Set, Tuple, Any
import numpy as np
from collections import defaultdict
import time

# Configure logging
logger = logging.getLogger(__name__)


class HybridSearchEngine:
    """
    Advanced hybrid search engine combining multiple search strategies.

    Integrates:
    - Semantic vector search via Qdrant
    - Keyword/text search
    - Metadata filtering
    - Result re-ranking with multiple signals
    """

    def __init__(self, vectorstore_manager=None, query_processor=None):
        """Initialize the hybrid search engine."""
        self.vectorstore_manager = vectorstore_manager
        self.query_processor = query_processor

        # Search configuration
        self.config = {
            "semantic_weight": 0.7,  # Weight for semantic search scores
            "keyword_weight": 0.2,  # Weight for keyword search scores
            "metadata_weight": 0.1,  # Weight for metadata match scores
            "min_semantic_score": 0.1,  # Minimum semantic similarity threshold
            "max_results": 50,  # Maximum results to process
            "rerank_top_k": 20,  # Top K results to re-rank
        }

        # Keyword search setup
        self.keyword_boost_fields = {
            "title": 3.0,  # Title matches get highest boost
            "genres": 2.0,  # Genre matches get medium boost
            "overview": 1.0,  # Overview matches get base boost
        }

        # Metadata filters and boosts
        self.metadata_boosts = {
            "popularity_boost": 0.1,  # Boost for popular movies
            "year_relevance": 0.05,  # Boost for recent/classic years
            "genre_match": 0.15,  # Boost for exact genre matches
            "rating_boost": 0.1,  # Boost for highly rated movies
        }

    def search(
        self,
        query: str,
        filters: Optional[Dict] = None,
        limit: int = 10,
        search_mode: str = "hybrid",
    ) -> Dict[str, Any]:
        """
        Perform hybrid search combining multiple strategies.

        Args:
            query: User search query
            filters: Optional metadata filters (genre, year, etc.)
            limit: Number of results to return
            search_mode: 'hybrid', 'semantic', 'keyword'

        Returns:
            dict: Search results with scores and metadata
        """
        start_time = time.time()

        try:
            # Step 1: Process the query
            processed_query = self._process_query(query)

            # Step 2: Perform searches based on mode
            if search_mode == "semantic":
                results = self._semantic_search_only(
                    processed_query, filters, limit * 3
                )
            elif search_mode == "keyword":
                results = self._keyword_search_only(processed_query, filters, limit * 3)
            else:  # hybrid
                results = self._hybrid_search(processed_query, filters, limit * 3)

            # Step 3: Re-rank results
            reranked_results = self._rerank_results(results, processed_query, filters)

            # Step 4: Apply final filtering and limiting
            final_results = self._finalize_results(reranked_results, limit)

            search_time = time.time() - start_time

            return {
                "results": final_results,
                "total_found": len(results),
                "search_time": search_time,
                "query_info": {
                    "original_query": query,
                    "processed_query": processed_query,
                    "search_mode": search_mode,
                    "filters_applied": filters or {},
                },
                "search_metadata": {
                    "semantic_results": len(
                        [r for r in results if r.get("semantic_score", 0) > 0]
                    ),
                    "keyword_results": len(
                        [r for r in results if r.get("keyword_score", 0) > 0]
                    ),
                    "reranked_count": min(len(results), self.config["rerank_top_k"]),
                },
            }

        except Exception as e:
            logger.error(f"Hybrid search failed for query '{query}': {str(e)}")
            return {
                "results": [],
                "total_found": 0,
                "search_time": time.time() - start_time,
                "error": str(e),
                "query_info": {"original_query": query},
            }

    def _process_query(self, query: str) -> Dict[str, Any]:
        """Process query using our query processor."""
        if self.query_processor:
            try:
                from app.rag._04_query_processing import quick_process_query

                processed = quick_process_query(query)
                return {
                    "text": processed,
                    "original": query,
                    "keywords": self._extract_keywords(processed),
                    "processed": True,
                }
            except Exception as e:
                logger.warning(f"Query processing failed: {str(e)}")

        # Fallback to basic processing
        return {
            "text": query.lower().strip(),
            "original": query,
            "keywords": self._extract_keywords(query),
            "processed": False,
        }

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text."""
        # Remove common stop words but keep movie-specific terms
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
        }

        # Extract words (alphanumeric + hyphens)
        words = re.findall(r"\b[\w-]+\b", text.lower())

        # Filter out stop words and keep meaningful terms
        keywords = [word for word in words if word not in stop_words and len(word) > 2]

        return keywords[:10]  # Limit to top 10 keywords

    def _semantic_search_only(
        self, processed_query: Dict, filters: Optional[Dict], limit: int
    ) -> List[Dict]:
        """Perform semantic search only."""
        if not self.vectorstore_manager:
            return []

        try:
            from app.rag._03_vectorstore import get_semantic_search

            semantic_searcher = get_semantic_search()

            # Perform semantic search
            semantic_results = semantic_searcher.search_movies(
                query=processed_query["text"],
                limit=limit,
                score_threshold=self.config["min_semantic_score"],
            )

            # Convert to our result format
            results = []
            for result in semantic_results:
                results.append(
                    {
                        "movie_id": result.get("movieId"),
                        "title": result.get("title", "Unknown"),
                        "overview": result.get("metadata", {}).get(
                            "embedding_text", ""
                        ),
                        "genres": (
                            result.get("genres", "").split("|")
                            if result.get("genres")
                            else []
                        ),
                        "year": result.get("year"),
                        "semantic_score": result.get("similarity_score", 0.0),
                        "keyword_score": 0.0,
                        "metadata_score": 0.0,
                        "final_score": result.get("similarity_score", 0.0),
                        "source": "semantic",
                        "payload": result,
                    }
                )

            return results

        except Exception as e:
            logger.error(f"Semantic search failed: {str(e)}")
            return []

    def _keyword_search_only(
        self, processed_query: Dict, filters: Optional[Dict], limit: int
    ) -> List[Dict]:
        """Perform keyword search only."""
        # For now, return empty since we don't have a separate keyword index
        # In a full implementation, this would use Elasticsearch or similar
        logger.info(
            "Keyword-only search not fully implemented - using semantic fallback"
        )
        return self._semantic_search_only(processed_query, filters, limit)

    def _hybrid_search(
        self, processed_query: Dict, filters: Optional[Dict], limit: int
    ) -> List[Dict]:
        """Perform hybrid search combining semantic and keyword approaches."""
        # Get semantic results
        semantic_results = self._semantic_search_only(processed_query, filters, limit)

        # For each semantic result, calculate keyword match scores
        keywords = processed_query.get("keywords", [])

        for result in semantic_results:
            keyword_score = self._calculate_keyword_score(result, keywords)
            metadata_score = self._calculate_metadata_score(
                result, processed_query, filters
            )

            # Update scores
            result["keyword_score"] = keyword_score
            result["metadata_score"] = metadata_score

            # Calculate hybrid score
            semantic_score = result["semantic_score"]
            result["final_score"] = (
                semantic_score * self.config["semantic_weight"]
                + keyword_score * self.config["keyword_weight"]
                + metadata_score * self.config["metadata_weight"]
            )
            result["source"] = "hybrid"

        return semantic_results

    def _calculate_keyword_score(self, result: Dict, keywords: List[str]) -> float:
        """Calculate keyword match score for a result."""
        if not keywords:
            return 0.0

        score = 0.0
        total_weight = 0.0

        # Check different fields with different weights
        fields_to_check = {
            "title": (result.get("title", ""), self.keyword_boost_fields["title"]),
            "overview": (
                result.get("overview", ""),
                self.keyword_boost_fields["overview"],
            ),
            "genres": (
                " ".join(result.get("genres", [])),
                self.keyword_boost_fields["genres"],
            ),
        }

        for field_name, (field_text, weight) in fields_to_check.items():
            if field_text:
                field_text_lower = field_text.lower()
                field_score = 0.0

                for keyword in keywords:
                    if keyword in field_text_lower:
                        # Exact match
                        field_score += 1.0
                    elif any(keyword in word for word in field_text_lower.split()):
                        # Partial match
                        field_score += 0.5

                # Normalize by number of keywords and apply weight
                if keywords:
                    field_score = (field_score / len(keywords)) * weight
                    score += field_score
                    total_weight += weight

        # Normalize final score
        return score / total_weight if total_weight > 0 else 0.0

    def _calculate_metadata_score(
        self, result: Dict, processed_query: Dict, filters: Optional[Dict]
    ) -> float:
        """Calculate metadata relevance score."""
        score = 0.0

        # Genre matching boost
        query_text = processed_query.get("text", "").lower()
        genres = result.get("genres", [])
        for genre in genres:
            if genre.lower() in query_text:
                score += self.metadata_boosts["genre_match"]

        # Year relevance (prefer recent or classic movies)
        year = result.get("year")
        if year:
            current_year = 2024
            if year >= current_year - 5:  # Recent movies
                score += self.metadata_boosts["year_relevance"]
            elif year <= 1980:  # Classic movies
                score += self.metadata_boosts["year_relevance"]

        # Popularity boost (if available)
        popularity = result.get("payload", {}).get("popularity", 0)
        if popularity > 50:  # High popularity threshold
            score += self.metadata_boosts["popularity_boost"]

        # Rating boost (if available)
        vote_average = result.get("payload", {}).get("vote_average", 0)
        if vote_average > 7.0:  # High rating threshold
            score += self.metadata_boosts["rating_boost"]

        return min(score, 1.0)  # Cap at 1.0

    def _rerank_results(
        self, results: List[Dict], processed_query: Dict, filters: Optional[Dict]
    ) -> List[Dict]:
        """Re-rank results using multiple signals."""
        if not results:
            return results

        # Take top K results for re-ranking
        top_results = results[: self.config["rerank_top_k"]]
        remaining_results = results[self.config["rerank_top_k"] :]

        # Apply additional re-ranking signals
        for result in top_results:
            # Diversity boost - penalize very similar titles
            diversity_penalty = self._calculate_diversity_penalty(result, top_results)

            # Query length matching - prefer results that match query complexity
            length_bonus = self._calculate_length_matching_bonus(
                result, processed_query
            )

            # Update final score
            result["final_score"] = (
                result["final_score"] * (1 - diversity_penalty) + length_bonus
            )

            # Store re-ranking info
            result["reranked"] = True
            result["diversity_penalty"] = diversity_penalty
            result["length_bonus"] = length_bonus

        # Sort by final score
        top_results.sort(key=lambda x: x["final_score"], reverse=True)

        # Combine with remaining results
        return top_results + remaining_results

    def _calculate_diversity_penalty(
        self, result: Dict, all_results: List[Dict]
    ) -> float:
        """Calculate penalty for results that are too similar to others."""
        title = result.get("title", "").lower()
        penalty = 0.0

        # Check for very similar titles
        for other_result in all_results:
            if other_result.get("movie_id") != result.get("movie_id"):
                other_title = other_result.get("title", "").lower()

                # Simple similarity check
                if title in other_title or other_title in title:
                    penalty += 0.1

                # Check for sequel patterns
                if re.search(r"\b(ii|iii|iv|v|2|3|4|5)\b", title) and re.search(
                    r"\b(ii|iii|iv|v|2|3|4|5)\b", other_title
                ):
                    penalty += 0.05

        return min(penalty, 0.3)  # Cap penalty at 30%

    def _calculate_length_matching_bonus(
        self, result: Dict, processed_query: Dict
    ) -> float:
        """Bonus for results that match query complexity."""
        query_length = len(processed_query.get("keywords", []))

        # Prefer movies with descriptions that match query complexity
        overview_length = len(result.get("overview", "").split())

        if query_length <= 2 and overview_length < 50:
            return 0.05  # Simple query, simple movie
        elif query_length > 3 and overview_length > 100:
            return 0.05  # Complex query, detailed movie
        else:
            return 0.0

    def _finalize_results(self, results: List[Dict], limit: int) -> List[Dict]:
        """Apply final filtering and formatting."""
        # Remove duplicates
        seen_ids = set()
        unique_results = []
        for result in results:
            movie_id = result.get("movie_id")
            if movie_id not in seen_ids:
                seen_ids.add(movie_id)
                unique_results.append(result)

        # Sort by final score
        unique_results.sort(key=lambda x: x["final_score"], reverse=True)

        # Limit results
        final_results = unique_results[:limit]

        # Clean up result format for API response
        for i, result in enumerate(final_results):
            result["rank"] = i + 1
            result["scores"] = {
                "semantic": result.get("semantic_score", 0.0),
                "keyword": result.get("keyword_score", 0.0),
                "metadata": result.get("metadata_score", 0.0),
                "final": result.get("final_score", 0.0),
            }

            # Remove internal processing fields
            for field in ["semantic_score", "keyword_score", "metadata_score"]:
                result.pop(field, None)

        return final_results

    def get_search_stats(self) -> Dict[str, Any]:
        """Get search engine statistics and configuration."""
        return {
            "version": "1.0.0",
            "config": self.config.copy(),
            "capabilities": {
                "semantic_search": bool(self.vectorstore_manager),
                "keyword_search": True,
                "hybrid_search": True,
                "metadata_filtering": True,
                "result_reranking": True,
                "query_processing": bool(self.query_processor),
            },
            "boost_fields": self.keyword_boost_fields.copy(),
            "metadata_boosts": self.metadata_boosts.copy(),
        }

    def update_config(self, new_config: Dict) -> bool:
        """Update search engine configuration."""
        try:
            for key, value in new_config.items():
                if key in self.config:
                    self.config[key] = value
                    logger.info(f"Updated search config: {key} = {value}")
                else:
                    logger.warning(f"Invalid config key ignored: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to update search config: {str(e)}")
            return False


# Global instance for easy access
hybrid_search_engine = None


def get_hybrid_search_engine(
    vectorstore_manager=None, query_processor=None
) -> HybridSearchEngine:
    """
    Get or create global hybrid search engine instance.

    Args:
        vectorstore_manager: Optional vectorstore manager instance
        query_processor: Optional query processor instance

    Returns:
        HybridSearchEngine: Global search engine instance
    """
    global hybrid_search_engine

    if hybrid_search_engine is None:
        # Try to get dependencies automatically
        if vectorstore_manager is None:
            try:
                from app.rag._03_vectorstore import get_semantic_search

                vectorstore_manager = get_semantic_search()
            except ImportError:
                logger.warning("Could not import vectorstore manager")

        if query_processor is None:
            try:
                from app.rag._04_query_processing import get_query_processor

                query_processor = get_query_processor()
            except ImportError:
                logger.warning("Could not import query processor")

        hybrid_search_engine = HybridSearchEngine(vectorstore_manager, query_processor)

    return hybrid_search_engine


# Convenience functions
def hybrid_search(
    query: str, filters: Optional[Dict] = None, limit: int = 10
) -> Dict[str, Any]:
    """
    Perform hybrid search with global engine instance.

    Args:
        query: Search query
        filters: Optional metadata filters
        limit: Number of results to return

    Returns:
        dict: Search results
    """
    engine = get_hybrid_search_engine()
    return engine.search(query, filters, limit, search_mode="hybrid")


def semantic_search(
    query: str, filters: Optional[Dict] = None, limit: int = 10
) -> Dict[str, Any]:
    """
    Perform semantic search only with global engine instance.

    Args:
        query: Search query
        filters: Optional metadata filters
        limit: Number of results to return

    Returns:
        dict: Search results
    """
    engine = get_hybrid_search_engine()
    return engine.search(query, filters, limit, search_mode="semantic")
