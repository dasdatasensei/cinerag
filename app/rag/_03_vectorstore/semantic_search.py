"""
Semantic Search Interface

Converts text queries to embeddings and performs vector similarity search
for movie recommendations.
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional
from sentence_transformers import SentenceTransformer
from .vector_operations import get_movie_vector_operations

# Configure logging
logger = logging.getLogger(__name__)


class MovieSemanticSearch:
    """
    Semantic search interface for movie recommendations.

    Handles text query encoding and vector similarity search to find
    relevant movies based on semantic meaning.
    """

    def __init__(
        self, model_name: str = "all-MiniLM-L6-v2", collection_name: str = "movies"
    ):
        """
        Initialize semantic search.

        Args:
            model_name: SentenceTransformer model name
            collection_name: Qdrant collection name
        """
        self.model_name = model_name
        self.collection_name = collection_name

        # Initialize components
        self.encoder = None
        self.vector_ops = get_movie_vector_operations(collection_name)

        # Load the embedding model
        self._load_model()

    def _load_model(self) -> bool:
        """
        Load the SentenceTransformer model.

        Returns:
            bool: True if model loaded successfully
        """
        try:
            logger.info(f"Loading SentenceTransformer model: {self.model_name}")
            self.encoder = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Error loading model {self.model_name}: {str(e)}")
            return False

    def encode_query(self, query: str) -> Optional[np.ndarray]:
        """
        Convert text query to embedding vector.

        Args:
            query: Text query to encode

        Returns:
            numpy.ndarray: Query embedding vector, or None if encoding fails
        """
        if not self.encoder:
            logger.error("Model not loaded")
            return None

        try:
            # Encode the query
            embedding = self.encoder.encode(query, convert_to_numpy=True)

            # Normalize the embedding (L2 normalization)
            embedding = embedding / np.linalg.norm(embedding)

            return embedding

        except Exception as e:
            logger.error(f"Error encoding query '{query}': {str(e)}")
            return None

    def search_movies(
        self,
        query: str,
        limit: int = 10,
        genre_filter: str = None,
        min_rating: float = None,
        score_threshold: float = 0.5,
        include_metadata: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Search for movies using semantic similarity.

        Args:
            query: Text query describing desired movies
            limit: Maximum number of results to return
            genre_filter: Filter by specific genre (optional)
            min_rating: Minimum rating threshold (optional)
            score_threshold: Minimum similarity score threshold
            include_metadata: Whether to include full movie metadata

        Returns:
            list: List of matching movies with similarity scores
        """
        # Encode the query
        query_vector = self.encode_query(query)
        if query_vector is None:
            logger.error(f"Failed to encode query: {query}")
            return []

        # Perform vector search
        results = self.vector_ops.search_similar_movies(
            query_vector=query_vector,
            limit=limit,
            genre_filter=genre_filter,
            min_rating=min_rating,
            score_threshold=score_threshold,
        )

        # Format results
        formatted_results = []
        for result in results:
            formatted_result = {
                "movieId": result["movieId"],
                "title": result["title"],
                "genres": result["genres"],
                "similarity_score": result["similarity_score"],
                "query": query,
            }

            # Add optional fields
            if result.get("year"):
                formatted_result["year"] = result["year"]
            if result.get("rating"):
                formatted_result["rating"] = result["rating"]
            if result.get("popularity"):
                formatted_result["popularity"] = result["popularity"]

            # Include full metadata if requested
            if include_metadata:
                formatted_result["metadata"] = result.get("metadata", {})

            formatted_results.append(formatted_result)

        logger.info(
            f"Semantic search for '{query}' returned {len(formatted_results)} results"
        )
        return formatted_results

    def find_similar_movies(
        self, movie_id: int, limit: int = 10, exclude_self: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Find movies similar to a specific movie.

        Args:
            movie_id: ID of the reference movie
            limit: Maximum number of results
            exclude_self: Whether to exclude the reference movie

        Returns:
            list: List of similar movies
        """
        try:
            results = self.vector_ops.search_by_movie_id(
                movie_id=movie_id, limit=limit, exclude_self=exclude_self
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_result = {
                    "movieId": result["movieId"],
                    "title": result["title"],
                    "genres": result["genres"],
                    "similarity_score": result["similarity_score"],
                    "reference_movie_id": movie_id,
                }

                # Add optional fields
                if result.get("year"):
                    formatted_result["year"] = result["year"]
                if result.get("rating"):
                    formatted_result["rating"] = result["rating"]
                if result.get("popularity"):
                    formatted_result["popularity"] = result["popularity"]

                formatted_results.append(formatted_result)

            logger.info(
                f"Found {len(formatted_results)} movies similar to movie {movie_id}"
            )
            return formatted_results

        except Exception as e:
            logger.error(f"Error finding similar movies for {movie_id}: {str(e)}")
            return []

    def get_recommendations(
        self, user_preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Get personalized movie recommendations based on user preferences.

        Args:
            user_preferences: Dictionary containing user preferences
                - query: Text description of preferences (optional)
                - genres: List of preferred genres (optional)
                - min_rating: Minimum rating preference (optional)
                - limit: Number of recommendations (default: 10)

        Returns:
            list: List of recommended movies
        """
        # Extract preferences
        query = user_preferences.get("query", "")
        genres = user_preferences.get("genres", [])
        min_rating = user_preferences.get("min_rating")
        limit = user_preferences.get("limit", 10)

        # Build search query from preferences
        if not query and genres:
            # Create query from genres if no explicit query provided
            genre_text = " and ".join(genres)
            query = f"movies in {genre_text} genre"
        elif not query:
            query = "popular highly rated movies"

        # Get genre filter (use first genre if multiple provided)
        genre_filter = genres[0] if genres else None

        # Perform semantic search
        recommendations = self.search_movies(
            query=query,
            limit=limit,
            genre_filter=genre_filter,
            min_rating=min_rating,
            score_threshold=0.3,  # Lower threshold for recommendations
        )

        logger.info(
            f"Generated {len(recommendations)} recommendations based on preferences"
        )
        return recommendations

    def search_with_examples(
        self, query: str, example_movies: List[int] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Enhanced search using both text query and example movies.

        Args:
            query: Text description of desired movies
            example_movies: List of movie IDs that user likes (optional)
            limit: Maximum number of results

        Returns:
            list: List of recommended movies
        """
        results = []

        # Get results from text query
        text_results = self.search_movies(
            query, limit=limit // 2 if example_movies else limit
        )
        results.extend(text_results)

        # Get results from example movies
        if example_movies:
            for movie_id in example_movies[:3]:  # Limit to 3 examples
                similar_movies = self.find_similar_movies(
                    movie_id=movie_id, limit=limit // len(example_movies[:3])
                )
                results.extend(similar_movies)

        # Remove duplicates and sort by similarity score
        seen_ids = set()
        unique_results = []

        for result in sorted(
            results, key=lambda x: x["similarity_score"], reverse=True
        ):
            movie_id = result["movieId"]
            if movie_id not in seen_ids:
                seen_ids.add(movie_id)
                unique_results.append(result)

        return unique_results[:limit]

    def get_search_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the search system.

        Returns:
            dict: Search system statistics
        """
        try:
            # Get collection stats
            collection_stats = self.vector_ops.get_collection_stats()

            # Get model info
            model_info = {
                "model_name": self.model_name,
                "embedding_dimension": (
                    self.encoder.get_sentence_embedding_dimension()
                    if self.encoder
                    else None
                ),
                "model_loaded": self.encoder is not None,
            }

            return {
                "model_info": model_info,
                "collection_stats": collection_stats,
                "search_capabilities": {
                    "semantic_search": True,
                    "similarity_search": True,
                    "filtered_search": True,
                    "recommendation_system": True,
                },
            }

        except Exception as e:
            logger.error(f"Error getting search stats: {str(e)}")
            return {"error": str(e)}


# Global instance for easy access
semantic_search_instance = None


def get_semantic_search(
    model_name: str = "all-MiniLM-L6-v2", collection_name: str = "movies"
) -> MovieSemanticSearch:
    """
    Get or create global semantic search instance.

    Args:
        model_name: SentenceTransformer model name
        collection_name: Qdrant collection name

    Returns:
        MovieSemanticSearch: Global semantic search instance
    """
    global semantic_search_instance

    if semantic_search_instance is None:
        semantic_search_instance = MovieSemanticSearch(model_name, collection_name)

    return semantic_search_instance
