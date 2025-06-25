"""
Vector Service - Qdrant Implementation for Semantic Movie Search

This service handles vector embeddings for movies using Qdrant vector database
and sentence transformers for generating embeddings from movie metadata.
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, CollectionStatus
from qdrant_client.http.exceptions import UnexpectedResponse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorService:
    """Qdrant-based vector service for semantic movie search."""

    def __init__(self):
        # Qdrant configuration
        self.qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        self.qdrant_port = int(os.getenv("QDRANT_PORT", 6333))
        self.collection_name = "movies"

        # Embedding model configuration
        self.model_name = "all-MiniLM-L6-v2"  # Fast and efficient for similarity search
        self.vector_size = 384  # Dimension of all-MiniLM-L6-v2 embeddings

        # Initialize components
        self.client = None
        self.embedding_model = None
        self._initialize_client()
        self._initialize_embedding_model()
        self._ensure_collection_exists()

    def _initialize_client(self):
        """Initialize Qdrant client with retry logic."""
        try:
            self.client = QdrantClient(
                host=self.qdrant_host, port=self.qdrant_port, timeout=30
            )
            logger.info(f"Connected to Qdrant at {self.qdrant_host}:{self.qdrant_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            self.client = None

    def _initialize_embedding_model(self):
        """Initialize sentence transformer model."""
        try:
            self.embedding_model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.embedding_model = None

    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist."""
        if not self.client:
            return

        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]

            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size, distance=Distance.COSINE
                    ),
                )
                logger.info(f"Collection '{self.collection_name}' created successfully")
            else:
                logger.info(f"Collection '{self.collection_name}' already exists")

        except Exception as e:
            logger.error(f"Error managing collection: {e}")

    def _create_movie_text(self, movie_data: Dict[str, Any]) -> str:
        """Create searchable text from movie metadata."""
        parts = []

        # Title (most important)
        if movie_data.get("title"):
            parts.append(f"Title: {movie_data['title']}")

        # Genres
        if movie_data.get("genres"):
            if isinstance(movie_data["genres"], list):
                genres_str = ", ".join(movie_data["genres"])
            else:
                genres_str = str(movie_data["genres"]).replace("|", ", ")
            parts.append(f"Genres: {genres_str}")

        # Overview/Description
        if movie_data.get("overview"):
            parts.append(f"Plot: {movie_data['overview']}")

        # Release year
        if movie_data.get("release_date"):
            year = (
                movie_data["release_date"][:4]
                if len(movie_data["release_date"]) >= 4
                else movie_data["release_date"]
            )
            parts.append(f"Year: {year}")

        return " | ".join(parts)

    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for given text."""
        if not self.embedding_model:
            logger.warning("Embedding model not available")
            return None

        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    def store_movie_embeddings(self, movies: List[Dict[str, Any]]) -> bool:
        """Store movie embeddings in Qdrant."""
        if not self.client or not self.embedding_model:
            logger.warning("Client or embedding model not available")
            return False

        try:
            points = []

            for movie in movies:
                # Create searchable text
                movie_text = self._create_movie_text(movie)

                # Generate embedding
                embedding = self._generate_embedding(movie_text)
                if not embedding:
                    continue

                # Create point for Qdrant
                point = models.PointStruct(
                    id=movie.get("id", hash(movie_text) % (10**9)),
                    vector=embedding,
                    payload={
                        "id": movie.get("id"),
                        "title": movie.get("title", ""),
                        "overview": movie.get("overview", ""),
                        "genres": movie.get("genres", []),
                        "release_date": movie.get("release_date", ""),
                        "vote_average": movie.get("vote_average", 0.0),
                        "vote_count": movie.get("vote_count", 0),
                        "poster_path": movie.get("poster_path"),
                        "backdrop_path": movie.get("backdrop_path"),
                        "runtime": movie.get("runtime"),
                        "searchable_text": movie_text,
                    },
                )
                points.append(point)

            if points:
                # Batch insert
                self.client.upsert(collection_name=self.collection_name, points=points)
                logger.info(f"Stored {len(points)} movie embeddings")
                return True

        except Exception as e:
            logger.error(f"Error storing embeddings: {e}")

        return False

    def search_similar_movies(
        self,
        query: str,
        limit: int = 10,
        genre_filter: Optional[str] = None,
        min_rating: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar movies using semantic vector search."""
        if not self.client or not self.embedding_model:
            logger.warning("Client or embedding model not available")
            return []

        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            if not query_embedding:
                return []

            # Build filter conditions
            filter_conditions = []

            if genre_filter and genre_filter.lower() != "all":
                filter_conditions.append(
                    models.FieldCondition(
                        key="genres", match=models.MatchText(text=genre_filter)
                    )
                )

            if min_rating is not None:
                filter_conditions.append(
                    models.FieldCondition(
                        key="vote_average", range=models.Range(gte=min_rating)
                    )
                )

            # Create filter
            search_filter = None
            if filter_conditions:
                search_filter = models.Filter(must=filter_conditions)

            # Perform search
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=limit,
                with_payload=True,
            )

            # Convert results to movie format
            movies = []
            for result in search_results:
                payload = result.payload
                movie = {
                    "id": payload.get("id"),
                    "title": payload.get("title", ""),
                    "overview": payload.get("overview", ""),
                    "poster_path": payload.get("poster_path"),
                    "backdrop_path": payload.get("backdrop_path"),
                    "release_date": payload.get("release_date", ""),
                    "vote_average": payload.get("vote_average", 0.0),
                    "vote_count": payload.get("vote_count", 0),
                    "genres": payload.get("genres", []),
                    "runtime": payload.get("runtime"),
                    "similarity_score": result.score,
                }
                movies.append(movie)

            logger.info(f"Found {len(movies)} similar movies for query: '{query}'")
            return movies

        except Exception as e:
            logger.error(f"Error searching similar movies: {e}")
            return []

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the vector collection."""
        if not self.client:
            return {"error": "Client not available", "points_count": 0}

        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "status": "healthy",
                "collection_name": self.collection_name,
                "points_count": collection_info.points_count,
                "vectors_count": collection_info.vectors_count or 0,
                "indexed_vectors_count": collection_info.indexed_vectors_count or 0,
                "config": {
                    "vector_size": self.vector_size,
                    "distance": "cosine",
                    "model": self.model_name,
                },
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {"error": str(e), "points_count": 0, "status": "error"}

    def delete_collection(self) -> bool:
        """Delete the entire collection (use with caution)."""
        if not self.client:
            return False

        try:
            self.client.delete_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' deleted")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False

    def get_movie_by_id(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific movie by ID from the vector database."""
        if not self.client:
            return None

        try:
            # Search by movie ID in payload
            search_results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="id", match=models.MatchValue(value=movie_id)
                        )
                    ]
                ),
                limit=1,
                with_payload=True,
            )

            if search_results[
                0
            ]:  # search_results is a tuple (points, next_page_offset)
                payload = search_results[0][0].payload
                return {
                    "id": payload.get("id"),
                    "title": payload.get("title", ""),
                    "overview": payload.get("overview", ""),
                    "poster_path": payload.get("poster_path"),
                    "backdrop_path": payload.get("backdrop_path"),
                    "release_date": payload.get("release_date", ""),
                    "vote_average": payload.get("vote_average", 0.0),
                    "vote_count": payload.get("vote_count", 0),
                    "genres": payload.get("genres", []),
                    "runtime": payload.get("runtime"),
                }

        except Exception as e:
            logger.error(f"Error getting movie by ID: {e}")

        return None

    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check of the vector service."""
        health_status = {"vector_service": "healthy", "components": {}}

        # Check Qdrant connection
        try:
            if self.client:
                collections = self.client.get_collections()
                health_status["components"]["qdrant"] = "connected"
                health_status["components"]["collections_count"] = len(
                    collections.collections
                )
            else:
                health_status["components"]["qdrant"] = "disconnected"
                health_status["vector_service"] = "unhealthy"
        except Exception as e:
            health_status["components"]["qdrant"] = f"error: {str(e)}"
            health_status["vector_service"] = "unhealthy"

        # Check embedding model
        try:
            if self.embedding_model:
                health_status["components"]["embedding_model"] = "loaded"
                health_status["components"]["model_name"] = self.model_name
            else:
                health_status["components"]["embedding_model"] = "not_loaded"
                health_status["vector_service"] = "unhealthy"
        except Exception as e:
            health_status["components"]["embedding_model"] = f"error: {str(e)}"
            health_status["vector_service"] = "unhealthy"

        # Check collection
        collection_info = self.get_collection_info()
        if "error" in collection_info:
            health_status["components"][
                "collection"
            ] = f"error: {collection_info['error']}"
            health_status["vector_service"] = "unhealthy"
        else:
            health_status["components"]["collection"] = "available"
            health_status["components"]["points_count"] = collection_info[
                "points_count"
            ]

        return health_status
