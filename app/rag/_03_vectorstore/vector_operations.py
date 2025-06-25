"""
Vector Operations for Movie Embeddings

Handles uploading embeddings and performing similarity search.
"""

import os
import json
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from qdrant_client.http.models import PointStruct, Filter, FieldCondition, Match
from .qdrant_client import get_qdrant_manager

# Configure logging
logger = logging.getLogger(__name__)


class MovieVectorOperations:
    """
    Handles movie-specific vector operations in Qdrant.

    Manages uploading movie embeddings and performing semantic search
    for movie recommendations.
    """

    def __init__(self, collection_name: str = "movies"):
        """
        Initialize movie vector operations.

        Args:
            collection_name: Name of the Qdrant collection for movies
        """
        self.collection_name = collection_name
        self.qdrant_manager = get_qdrant_manager()

        # Ensure collection exists
        self._ensure_collection_exists()

    def _ensure_collection_exists(self) -> bool:
        """
        Ensure the movies collection exists in Qdrant.

        Returns:
            bool: True if collection exists or was created successfully
        """
        try:
            existing_collections = self.qdrant_manager.list_collections()

            if self.collection_name not in existing_collections:
                logger.info(f"Creating movies collection: {self.collection_name}")
                return self.qdrant_manager.create_collection(
                    collection_name=self.collection_name,
                    vector_size=384,  # all-MiniLM-L6-v2 size
                    recreate=False,
                )
            else:
                logger.info(f"Movies collection {self.collection_name} already exists")
                return True

        except Exception as e:
            logger.error(f"Error ensuring collection exists: {str(e)}")
            return False

    def upload_movie_embeddings(
        self, embeddings_path: str = None, batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Upload movie embeddings from the _02_embeddings output.

        Args:
            embeddings_path: Path to embeddings data (uses default if None)
            batch_size: Number of vectors to upload per batch

        Returns:
            dict: Upload results and statistics
        """
        if not self.qdrant_manager.is_connected:
            return {"error": "Not connected to Qdrant"}

        # Use default path if not provided
        if embeddings_path is None:
            embeddings_path = "data/processed/embeddings"

        try:
            # Load the CSV file with movie metadata
            csv_path = os.path.join(embeddings_path, "movies_with_embeddings.csv")
            parquet_path = os.path.join(embeddings_path, "movie_embeddings.parquet")

            if not os.path.exists(csv_path):
                return {"error": f"Metadata file not found: {csv_path}"}
            if not os.path.exists(parquet_path):
                return {"error": f"Embeddings file not found: {parquet_path}"}

            logger.info(f"Loading metadata from: {csv_path}")
            metadata_df = pd.read_csv(csv_path)

            logger.info(f"Loading embeddings from: {parquet_path}")
            embeddings_df = pd.read_parquet(parquet_path)

            # Merge on movieId
            logger.info("Merging metadata and embeddings...")
            merged_df = pd.merge(metadata_df, embeddings_df, on="movieId", how="inner")

            if merged_df.empty:
                return {
                    "error": "No matching movies found between metadata and embeddings"
                }

            logger.info(f"Successfully merged {len(merged_df)} movies")

            # Prepare points for Qdrant
            points = []
            total_movies = len(merged_df)

            logger.info(f"Preparing {total_movies} movie vectors for upload")

            for idx, row in merged_df.iterrows():
                try:
                    # Extract embedding columns (emb_0 to emb_383)
                    embedding_cols = [
                        col for col in merged_df.columns if col.startswith("emb_")
                    ]
                    embedding = row[embedding_cols].values.astype(float)

                    # Create metadata payload
                    payload = {
                        "movieId": int(row["movieId"]),
                        "title": str(row["title"]),
                        "genres": str(row["genres"]),
                        "year": int(row["year"]) if pd.notna(row["year"]) else None,
                        "clean_title": str(row.get("clean_title", "")),
                        "embedding_text": str(row.get("embedding_text", "")),
                        "text_length": (
                            int(row.get("text_length", 0))
                            if pd.notna(row.get("text_length"))
                            else 0
                        ),
                        "word_count": (
                            int(row.get("word_count", 0))
                            if pd.notna(row.get("word_count"))
                            else 0
                        ),
                        "num_genres": (
                            int(row.get("num_genres", 0))
                            if pd.notna(row.get("num_genres"))
                            else 0
                        ),
                    }

                    # Create point
                    point = PointStruct(
                        id=int(row["movieId"]),
                        vector=embedding.tolist(),
                        payload=payload,
                    )

                    points.append(point)

                except Exception as e:
                    logger.error(
                        f"Error processing movie {row.get('movieId', 'unknown')}: {str(e)}"
                    )
                    continue

            if not points:
                return {"error": "No valid movie vectors to upload"}

            # Upload in batches
            uploaded_count = 0
            failed_count = 0

            logger.info(f"Uploading {len(points)} vectors in batches of {batch_size}")

            for i in range(0, len(points), batch_size):
                batch = points[i : i + batch_size]

                try:
                    self.qdrant_manager.client.upsert(
                        collection_name=self.collection_name, points=batch
                    )
                    uploaded_count += len(batch)
                    logger.info(
                        f"Uploaded batch {i//batch_size + 1}: {len(batch)} vectors"
                    )

                except Exception as e:
                    logger.error(f"Error uploading batch {i//batch_size + 1}: {str(e)}")
                    failed_count += len(batch)

            # Get final collection stats
            collection_info = self.qdrant_manager.get_collection_info(
                self.collection_name
            )

            result = {
                "success": True,
                "total_processed": len(points),
                "uploaded_count": uploaded_count,
                "failed_count": failed_count,
                "collection_info": collection_info,
                "upload_summary": {
                    "collection_name": self.collection_name,
                    "total_vectors": collection_info.get("vectors_count", 0),
                    "batch_size": batch_size,
                },
            }

            logger.info(
                f"Upload completed: {uploaded_count} vectors uploaded successfully"
            )
            return result

        except Exception as e:
            logger.error(f"Error uploading movie embeddings: {str(e)}")
            return {"error": str(e)}

    def search_similar_movies(
        self,
        query_vector: np.ndarray,
        limit: int = 10,
        genre_filter: str = None,
        min_rating: float = None,
        score_threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        Search for movies similar to a query vector.

        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results to return
            genre_filter: Filter by genre (optional)
            min_rating: Minimum rating filter (optional)
            score_threshold: Minimum similarity score threshold

        Returns:
            list: List of similar movies with metadata and scores
        """
        if not self.qdrant_manager.is_connected:
            logger.error("Not connected to Qdrant")
            return []

        try:
            # Prepare filter conditions
            filter_conditions = []

            if genre_filter:
                filter_conditions.append(
                    FieldCondition(key="genres", match=Match(value=genre_filter))
                )

            if min_rating is not None:
                filter_conditions.append(
                    FieldCondition(key="rating", range={"gte": min_rating})
                )

            # Create filter object if we have conditions
            query_filter = None
            if filter_conditions:
                query_filter = Filter(must=filter_conditions)

            # Perform similarity search
            search_result = self.qdrant_manager.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector.tolist(),
                query_filter=query_filter,
                limit=limit,
                score_threshold=score_threshold,
            )

            # Format results
            results = []
            for hit in search_result:
                result = {
                    "movieId": hit.payload.get("movieId"),
                    "title": hit.payload.get("title"),
                    "genres": hit.payload.get("genres"),
                    "year": hit.payload.get("year"),
                    "rating": hit.payload.get("rating"),
                    "popularity": hit.payload.get("popularity"),
                    "similarity_score": float(hit.score),
                    "metadata": hit.payload,
                }
                results.append(result)

            logger.info(f"Found {len(results)} similar movies")
            return results

        except Exception as e:
            logger.error(f"Error searching similar movies: {str(e)}")
            return []

    def search_by_movie_id(
        self, movie_id: int, limit: int = 10, exclude_self: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Find movies similar to a specific movie by its ID.

        Args:
            movie_id: ID of the reference movie
            limit: Maximum number of results
            exclude_self: Whether to exclude the reference movie from results

        Returns:
            list: List of similar movies
        """
        try:
            # Get the reference movie vector
            search_result = self.qdrant_manager.client.retrieve(
                collection_name=self.collection_name, ids=[movie_id], with_vectors=True
            )

            if not search_result:
                logger.error(f"Movie with ID {movie_id} not found")
                return []

            reference_movie = search_result[0]
            query_vector = np.array(reference_movie.vector)

            # Search for similar movies
            similar_movies = self.search_similar_movies(
                query_vector=query_vector,
                limit=limit + (1 if exclude_self else 0),  # Get extra if excluding self
            )

            # Remove the reference movie if requested
            if exclude_self:
                similar_movies = [
                    movie for movie in similar_movies if movie["movieId"] != movie_id
                ][:limit]

            return similar_movies

        except Exception as e:
            logger.error(f"Error searching by movie ID {movie_id}: {str(e)}")
            return []

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the movie collection.

        Returns:
            dict: Collection statistics and sample data
        """
        try:
            # Get basic collection info
            collection_info = self.qdrant_manager.get_collection_info(
                self.collection_name
            )

            # Get a sample of movies
            sample_result = self.qdrant_manager.client.scroll(
                collection_name=self.collection_name,
                limit=5,
                with_payload=True,
                with_vectors=False,
            )

            sample_movies = []
            if sample_result and sample_result[0]:
                for point in sample_result[0]:
                    sample_movies.append(
                        {
                            "movieId": point.payload.get("movieId"),
                            "title": point.payload.get("title"),
                            "genres": point.payload.get("genres"),
                        }
                    )

            return {
                "collection_info": collection_info,
                "sample_movies": sample_movies,
                "total_movies": collection_info.get("vectors_count", 0),
            }

        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {"error": str(e)}


# Global instance for easy access
movie_vector_ops = None


def get_movie_vector_operations(
    collection_name: str = "movies",
) -> MovieVectorOperations:
    """
    Get or create global movie vector operations instance.

    Args:
        collection_name: Name of the Qdrant collection

    Returns:
        MovieVectorOperations: Global instance
    """
    global movie_vector_ops

    if movie_vector_ops is None:
        movie_vector_ops = MovieVectorOperations(collection_name)

    return movie_vector_ops
