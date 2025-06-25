"""
Data Ingestion Service for Vector Database

This service handles the ingestion of movie data into the vector database,
converting movie metadata to embeddings for semantic search.
"""

import asyncio
from typing import List, Dict, Any
from .data_loader import MovieLensDataLoader
from .._03_vectorstore.vector_service import VectorService
from .tmdb_service import TMDBService
import logging

logger = logging.getLogger(__name__)


class DataIngestionService:
    """Service for ingesting movie data into the vector database."""

    def __init__(self):
        self.data_loader = MovieLensDataLoader()
        self.vector_service = VectorService()
        self.tmdb_service = TMDBService()

    def convert_movie_to_vector_format(self, movie) -> Dict[str, Any]:
        """Convert a Movie object to vector database format."""
        return {
            "id": movie.id,
            "title": movie.title,
            "overview": movie.overview,
            "genres": movie.genres,  # List format
            "release_date": movie.release_date,
            "vote_average": movie.vote_average,
            "vote_count": movie.vote_count,
            "poster_path": movie.poster_path,
            "backdrop_path": movie.backdrop_path,
            "runtime": movie.runtime,
        }

    async def ingest_popular_movies(self, limit: int = 1000) -> Dict[str, Any]:
        """Ingest popular movies into the vector database."""
        try:
            logger.info(f"Starting ingestion of {limit} popular movies...")

            # Get popular movies from data loader
            movies = self.data_loader.get_popular_movies(limit)
            logger.info(f"Retrieved {len(movies)} movies from data loader")

            if not movies:
                return {"success": False, "message": "No movies retrieved"}

            # Enrich with TMDB data
            titles = [movie.title for movie in movies]
            enriched_movies = await self.tmdb_service.batch_enrich_movies(
                movies, titles
            )
            logger.info(f"Enriched {len(enriched_movies)} movies with TMDB data")

            # Convert to vector format
            vector_movies = [
                self.convert_movie_to_vector_format(movie) for movie in enriched_movies
            ]

            # Store in vector database
            success = self.vector_service.store_movie_embeddings(vector_movies)

            if success:
                collection_info = self.vector_service.get_collection_info()
                return {
                    "success": True,
                    "message": f"Successfully ingested {len(vector_movies)} movies",
                    "movies_processed": len(vector_movies),
                    "collection_info": collection_info,
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to store movies in vector database",
                }

        except Exception as e:
            logger.error(f"Error during ingestion: {e}")
            return {"success": False, "message": f"Ingestion failed: {str(e)}"}

    async def ingest_movies_by_genre(
        self, genre: str, limit: int = 500
    ) -> Dict[str, Any]:
        """Ingest movies of a specific genre."""
        try:
            logger.info(f"Ingesting {limit} {genre} movies...")

            movies = self.data_loader.get_movies_by_genre(genre, limit)
            if not movies:
                return {"success": False, "message": f"No {genre} movies found"}

            # Enrich and store
            titles = [movie.title for movie in movies]
            enriched_movies = await self.tmdb_service.batch_enrich_movies(
                movies, titles
            )

            vector_movies = [
                self.convert_movie_to_vector_format(movie) for movie in enriched_movies
            ]

            success = self.vector_service.store_movie_embeddings(vector_movies)

            return {
                "success": success,
                "message": f"Processed {len(vector_movies)} {genre} movies",
                "movies_processed": len(vector_movies),
            }

        except Exception as e:
            logger.error(f"Error ingesting {genre} movies: {e}")
            return {
                "success": False,
                "message": f"Failed to ingest {genre} movies: {str(e)}",
            }

    async def ingest_all_genres(self, limit_per_genre: int = 200) -> Dict[str, Any]:
        """Ingest movies from all available genres."""
        try:
            genres = self.data_loader.get_genres()
            results = {}
            total_processed = 0

            for genre in genres:
                if genre.lower() in ["(no genres listed)", "children"]:
                    continue  # Skip problematic genres

                result = await self.ingest_movies_by_genre(genre, limit_per_genre)
                results[genre] = result
                if result["success"]:
                    total_processed += result["movies_processed"]

                # Small delay between genres to prevent overwhelming the system
                await asyncio.sleep(1)

            collection_info = self.vector_service.get_collection_info()

            return {
                "success": True,
                "message": f"Ingested movies from {len(genres)} genres",
                "total_movies_processed": total_processed,
                "genre_results": results,
                "collection_info": collection_info,
            }

        except Exception as e:
            logger.error(f"Error during full ingestion: {e}")
            return {"success": False, "message": f"Full ingestion failed: {str(e)}"}

    def get_ingestion_status(self) -> Dict[str, Any]:
        """Get the current status of the vector database."""
        try:
            collection_info = self.vector_service.get_collection_info()
            health_status = self.vector_service.health_check()

            return {
                "collection_info": collection_info,
                "health_status": health_status,
                "is_ready": collection_info.get("points_count", 0) > 0,
            }

        except Exception as e:
            logger.error(f"Error getting ingestion status: {e}")
            return {"error": str(e), "is_ready": False}

    async def reingest_database(self) -> Dict[str, Any]:
        """Completely reingest the entire database (use with caution)."""
        try:
            logger.info("Starting complete database reingestion...")

            # Delete existing collection
            self.vector_service.delete_collection()

            # Recreate collection
            self.vector_service._ensure_collection_exists()

            # Ingest all data
            result = await self.ingest_all_genres(limit_per_genre=100)

            return {
                "success": True,
                "message": "Database reingestion completed",
                "result": result,
            }

        except Exception as e:
            logger.error(f"Error during reingestion: {e}")
            return {"success": False, "message": f"Reingestion failed: {str(e)}"}
