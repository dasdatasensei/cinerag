"""
Recommendation Service - RAG-based Movie Recommendations

This service provides movie recommendations using the RAG pipeline,
integrating multiple data sources and retrieval methods.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ...models import Movie
from .._01_ingestion.data_loader import MovieLensDataLoader
from .._03_vectorstore.vector_service import VectorService
from .._01_ingestion.tmdb_service import TMDBService

logger = logging.getLogger(__name__)


class RecommendationService:
    """Service for generating movie recommendations using various strategies."""

    def __init__(self):
        self.data_loader = MovieLensDataLoader()
        self.vector_service = VectorService()
        self.tmdb_service = TMDBService()

        # Mood to genre mapping (duplicated to avoid circular dependency)
        self.mood_to_genre = {
            "sad": ["Drama", "Romance"],
            "funny": ["Comedy"],
            "laugh": ["Comedy"],
            "romantic": ["Romance"],
            "scared": ["Horror", "Thriller"],
            "action": ["Action", "Adventure"],
            "light": ["Comedy", "Romance", "Animation"],
            "mind": ["Sci-Fi", "Thriller", "Mystery"],
        }

    async def get_recommendations(
        self,
        query: Optional[str] = None,
        genre: Optional[str] = None,
        min_rating: Optional[float] = None,
        limit: int = 20,
    ) -> List[Movie]:
        """
        Get movie recommendations based on various parameters.

        Args:
            query: Natural language query for semantic search
            genre: Specific genre filter
            min_rating: Minimum TMDB rating
            limit: Number of recommendations to return

        Returns:
            List of recommended movies
        """
        try:
            if query:
                # Use vector search for semantic recommendations
                return await self._get_semantic_recommendations(
                    query, genre, min_rating, limit
                )
            elif genre:
                # Genre-based recommendations
                return await self._get_genre_recommendations(genre, min_rating, limit)
            else:
                # Popular/trending recommendations
                return await self._get_popular_recommendations(min_rating, limit)

        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return []

    async def _get_semantic_recommendations(
        self,
        query: str,
        genre: Optional[str] = None,
        min_rating: Optional[float] = None,
        limit: int = 20,
    ) -> List[Movie]:
        """Get recommendations using semantic vector search."""
        try:
            # Use vector service for semantic search
            movie_data = self.vector_service.search_similar_movies(
                query=query,
                limit=limit * 2,  # Get more results for filtering
                genre_filter=genre,
                min_rating=min_rating,
            )

            # Convert to Movie objects
            movies = []
            for data in movie_data[:limit]:
                movie = Movie(
                    id=data.get("id"),
                    title=data.get("title", ""),
                    overview=data.get("overview", ""),
                    poster_path=data.get("poster_path"),
                    backdrop_path=data.get("backdrop_path"),
                    release_date=data.get("release_date", ""),
                    vote_average=data.get("vote_average", 0.0),
                    vote_count=data.get("vote_count", 0),
                    genres=data.get("genres", []),
                    runtime=data.get("runtime"),
                )
                movies.append(movie)

            logger.info(
                f"Generated {len(movies)} semantic recommendations for query: '{query}'"
            )
            return movies

        except Exception as e:
            logger.error(f"Error in semantic recommendations: {e}")
            return []

    async def _get_genre_recommendations(
        self, genre: str, min_rating: Optional[float] = None, limit: int = 20
    ) -> List[Movie]:
        """Get recommendations for a specific genre."""
        try:
            # Get movies from data loader
            movies_data = self.data_loader.get_movies_by_genre(genre, limit * 2)

            # Filter by rating if specified
            if min_rating:
                movies_data = [m for m in movies_data if m.vote_average >= min_rating]

            # Enrich with TMDB data
            titles = [movie.title for movie in movies_data[:limit]]
            enriched_movies = await self.tmdb_service.batch_enrich_movies(
                movies_data[:limit], titles
            )

            logger.info(
                f"Generated {len(enriched_movies)} genre recommendations for: {genre}"
            )
            return enriched_movies

        except Exception as e:
            logger.error(f"Error in genre recommendations: {e}")
            return []

    async def _get_popular_recommendations(
        self, min_rating: Optional[float] = None, limit: int = 20
    ) -> List[Movie]:
        """Get popular/trending movie recommendations."""
        try:
            # Get popular movies from data loader
            movies_data = self.data_loader.get_popular_movies(limit * 2)

            # Filter by rating if specified
            if min_rating:
                movies_data = [m for m in movies_data if m.vote_average >= min_rating]

            # Enrich with TMDB data
            titles = [movie.title for movie in movies_data[:limit]]
            enriched_movies = await self.tmdb_service.batch_enrich_movies(
                movies_data[:limit], titles
            )

            logger.info(f"Generated {len(enriched_movies)} popular recommendations")
            return enriched_movies

        except Exception as e:
            logger.error(f"Error in popular recommendations: {e}")
            return []

    async def get_similar_movies(self, movie_id: int, limit: int = 10) -> List[Movie]:
        """Get movies similar to a specific movie."""
        try:
            # Get the source movie
            source_movie = self.vector_service.get_movie_by_id(movie_id)
            if not source_movie:
                logger.warning(f"Movie with ID {movie_id} not found")
                return []

            # Create search query from movie metadata
            search_query = (
                f"{source_movie['title']} {' '.join(source_movie.get('genres', []))}"
            )

            # Get similar movies using vector search
            similar_movies_data = self.vector_service.search_similar_movies(
                query=search_query,
                limit=limit + 1,  # +1 to account for the source movie
            )

            # Filter out the source movie and convert to Movie objects
            movies = []
            for data in similar_movies_data:
                if data.get("id") != movie_id:  # Skip the source movie
                    movie = Movie(
                        id=data.get("id"),
                        title=data.get("title", ""),
                        overview=data.get("overview", ""),
                        poster_path=data.get("poster_path"),
                        backdrop_path=data.get("backdrop_path"),
                        release_date=data.get("release_date", ""),
                        vote_average=data.get("vote_average", 0.0),
                        vote_count=data.get("vote_count", 0),
                        genres=data.get("genres", []),
                        runtime=data.get("runtime"),
                    )
                    movies.append(movie)

            logger.info(
                f"Found {len(movies)} similar movies to '{source_movie['title']}'"
            )
            return movies[:limit]

        except Exception as e:
            logger.error(f"Error getting similar movies: {e}")
            return []

    async def get_recommendations_by_mood(
        self, mood: str, limit: int = 20
    ) -> List[Movie]:
        """Get recommendations based on user mood."""
        try:
            # Extract mood-based genres
            mood_genres = []
            mood_lower = mood.lower()
            for mood_key, genres in self.mood_to_genre.items():
                if mood_key in mood_lower:
                    mood_genres.extend(genres)

            mood_genres = list(set(mood_genres))  # Remove duplicates

            if not mood_genres:
                logger.warning(f"No genres found for mood: {mood}")
                return await self._get_popular_recommendations(limit=limit)

            # Get recommendations for the first mood genre
            primary_genre = mood_genres[0]
            movies = await self._get_genre_recommendations(primary_genre, limit=limit)

            logger.info(
                f"Generated {len(movies)} mood-based recommendations for: {mood}"
            )
            return movies

        except Exception as e:
            logger.error(f"Error in mood-based recommendations: {e}")
            return []

    def get_available_genres(self) -> List[str]:
        """Get list of available genres."""
        try:
            return self.data_loader.get_genres()
        except Exception as e:
            logger.error(f"Error getting genres: {e}")
            return []

    async def search_movies(self, query: str, limit: int = 20) -> List[Movie]:
        """Search for movies by title or keywords."""
        try:
            # First try exact title search with data loader
            movies_data = self.data_loader.search_movies(query, limit)

            if movies_data:
                # Enrich with TMDB data
                titles = [movie.title for movie in movies_data]
                enriched_movies = await self.tmdb_service.batch_enrich_movies(
                    movies_data, titles
                )
                return enriched_movies

            # If no exact matches, use semantic search
            similar_movies_data = self.vector_service.search_similar_movies(
                query, limit
            )
            movies = []
            for data in similar_movies_data:
                movie = Movie(
                    id=data.get("id"),
                    title=data.get("title", ""),
                    overview=data.get("overview", ""),
                    poster_path=data.get("poster_path"),
                    backdrop_path=data.get("backdrop_path"),
                    release_date=data.get("release_date", ""),
                    vote_average=data.get("vote_average", 0.0),
                    vote_count=data.get("vote_count", 0),
                    genres=data.get("genres", []),
                    runtime=data.get("runtime"),
                )
                movies.append(movie)

            logger.info(f"Found {len(movies)} movies for search query: '{query}'")
            return movies

        except Exception as e:
            logger.error(f"Error searching movies: {e}")
            return []

    def get_recommendation_stats(self) -> Dict[str, Any]:
        """Get statistics about the recommendation system."""
        try:
            # Get vector service stats
            vector_stats = self.vector_service.get_collection_info()

            # Get data loader stats
            data_stats = self.data_loader.get_data_summary()

            return {
                "vector_database": vector_stats,
                "data_loader": data_stats,
                "available_genres": len(self.get_available_genres()),
                "system_status": (
                    "healthy" if vector_stats.get("status") == "healthy" else "degraded"
                ),
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting recommendation stats: {e}")
            return {"error": str(e), "system_status": "error"}
