"""
TMDB Service for RAG Data Ingestion

This service enriches movie data during the ingestion process by fetching
rich metadata from The Movie Database (TMDB) API including descriptions,
posters, ratings, and other enhanced movie information.
"""

import os
import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import time

from ...models import Movie

logger = logging.getLogger(__name__)


class TMDBService:
    """Service for enriching movie data with TMDB API information."""

    def __init__(self):
        self.api_key = os.getenv("TMDB_API_KEY")
        self.base_url = "https://api.themoviedb.org/3"
        self.image_base_url = "https://image.tmdb.org/t/p"

        # Rate limiting
        self.rate_limit_delay = 0.25  # 4 requests per second (TMDB limit is 40/10s)
        self.last_request_time = 0

        # Cache for API responses
        self.cache = {}
        self.cache_duration = timedelta(hours=24)  # Cache for 24 hours

        # Session for connection pooling
        self.session = None

        # Configuration for image sizes
        self.poster_size = (
            "w500"  # Options: w92, w154, w185, w342, w500, w780, original
        )
        self.backdrop_size = "w1280"  # Options: w300, w780, w1280, original

    async def _init_session(self):
        """Initialize aiohttp session if not already done."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def _close_session(self):
        """Close the aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None

    async def _rate_limit(self):
        """Implement rate limiting to respect TMDB API limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            await asyncio.sleep(sleep_time)

        self.last_request_time = time.time()

    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate cache key for API request."""
        return f"{endpoint}_{hash(frozenset(params.items()))}"

    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid."""
        if not cache_entry:
            return False

        timestamp = cache_entry.get("timestamp")
        if not timestamp:
            return False

        return datetime.now() - timestamp < self.cache_duration

    async def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make an API request to TMDB with caching and rate limiting."""
        if not self.api_key:
            logger.warning("TMDB API key not configured")
            return None

        # Check cache first
        cache_key = self._get_cache_key(endpoint, params or {})
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            logger.debug(f"Cache hit for {endpoint}")
            return self.cache[cache_key]["data"]

        await self._init_session()
        await self._rate_limit()

        if params is None:
            params = {}

        params["api_key"] = self.api_key

        url = f"{self.base_url}/{endpoint}"

        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    # Cache the response
                    self.cache[cache_key] = {"data": data, "timestamp": datetime.now()}

                    logger.debug(f"API success for {endpoint}")
                    return data
                elif response.status == 429:  # Rate limit exceeded
                    logger.warning("TMDB rate limit exceeded, waiting...")
                    await asyncio.sleep(2)
                    return await self._make_request(endpoint, params)  # Retry
                else:
                    logger.warning(f"TMDB API error {response.status} for {endpoint}")
                    return None

        except Exception as e:
            logger.error(f"Error making TMDB request to {endpoint}: {e}")
            return None

    async def search_movie(
        self, title: str, year: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Search for a movie on TMDB by title and optionally year.

        Args:
            title: Movie title to search for
            year: Optional release year to improve matching

        Returns:
            Movie data from TMDB or None if not found
        """
        params = {"query": title}
        if year:
            params["year"] = year

        response = await self._make_request("search/movie", params)

        if not response or not response.get("results"):
            return None

        # Get the first (most relevant) result
        results = response["results"]

        # If year provided, try to find exact year match first
        if year:
            for result in results:
                release_date = result.get("release_date", "")
                if release_date and release_date.startswith(str(year)):
                    return result

        # Otherwise return the first result
        return results[0] if results else None

    async def get_movie_details(self, tmdb_id: int) -> Optional[Dict]:
        """
        Get detailed movie information from TMDB.

        Args:
            tmdb_id: TMDB movie ID

        Returns:
            Detailed movie data or None if not found
        """
        params = {"append_to_response": "credits,keywords,videos,similar"}
        return await self._make_request(f"movie/{tmdb_id}", params)

    def _extract_year_from_title(self, title: str) -> Tuple[str, Optional[int]]:
        """Extract year from movie title if present."""
        import re

        # Look for year in parentheses at the end
        match = re.search(r"\((\d{4})\)$", title.strip())
        if match:
            year = int(match.group(1))
            clean_title = title[: match.start()].strip()
            return clean_title, year

        return title, None

    def _format_poster_url(self, poster_path: Optional[str]) -> Optional[str]:
        """Format poster URL with proper base URL and size."""
        if not poster_path:
            return None
        return f"{self.image_base_url}/{self.poster_size}{poster_path}"

    def _format_backdrop_url(self, backdrop_path: Optional[str]) -> Optional[str]:
        """Format backdrop URL with proper base URL and size."""
        if not backdrop_path:
            return None
        return f"{self.image_base_url}/{self.backdrop_size}{backdrop_path}"

    def _extract_genres(self, genres_data: List[Dict]) -> List[str]:
        """Extract genre names from TMDB genre data."""
        if not genres_data:
            return []
        return [genre.get("name", "") for genre in genres_data if genre.get("name")]

    async def enrich_movie_with_tmdb_data(
        self, movie: Movie, title_hint: str = None
    ) -> Movie:
        """
        Enrich a single movie with TMDB data.

        Args:
            movie: Movie object to enrich
            title_hint: Optional title hint for better matching

        Returns:
            Enhanced Movie object
        """
        if not self.api_key:
            logger.debug("TMDB API key not available, returning original movie")
            return movie

        try:
            # Use title hint if provided, otherwise use movie title
            search_title = title_hint or movie.title
            clean_title, year = self._extract_year_from_title(search_title)

            # Search for the movie
            tmdb_movie = await self.search_movie(clean_title, year)

            if not tmdb_movie:
                logger.debug(f"No TMDB match found for: {search_title}")
                return movie

            # Get detailed information
            tmdb_id = tmdb_movie.get("id")
            if tmdb_id:
                detailed_data = await self.get_movie_details(tmdb_id)
                if detailed_data:
                    tmdb_movie = detailed_data

            # Create enhanced movie object
            enhanced_movie = Movie(
                id=movie.id,  # Keep original ID
                title=movie.title,  # Keep original title
                overview=tmdb_movie.get("overview") or movie.overview,
                poster_path=self._format_poster_url(tmdb_movie.get("poster_path"))
                or movie.poster_path,
                backdrop_path=self._format_backdrop_url(tmdb_movie.get("backdrop_path"))
                or movie.backdrop_path,
                release_date=tmdb_movie.get("release_date") or movie.release_date,
                vote_average=tmdb_movie.get("vote_average") or movie.vote_average,
                vote_count=tmdb_movie.get("vote_count") or movie.vote_count,
                genres=self._extract_genres(tmdb_movie.get("genres", []))
                or movie.genres,
                runtime=tmdb_movie.get("runtime") or movie.runtime,
                # Additional TMDB data
                tmdb_id=tmdb_id,
                imdb_id=tmdb_movie.get("imdb_id"),
                budget=tmdb_movie.get("budget"),
                revenue=tmdb_movie.get("revenue"),
                popularity=tmdb_movie.get("popularity"),
                tagline=tmdb_movie.get("tagline"),
                status=tmdb_movie.get("status"),
                original_language=tmdb_movie.get("original_language"),
                production_companies=[
                    company.get("name")
                    for company in tmdb_movie.get("production_companies", [])
                    if company.get("name")
                ],
                keywords=[
                    keyword.get("name")
                    for keyword in tmdb_movie.get("keywords", {}).get("keywords", [])
                    if keyword.get("name")
                ],
            )

            logger.debug(f"Successfully enriched movie: {movie.title}")
            return enhanced_movie

        except Exception as e:
            logger.error(f"Error enriching movie '{movie.title}': {e}")
            return movie

    async def batch_enrich_movies(
        self,
        movies: List[Movie],
        title_hints: Optional[List[str]] = None,
        batch_size: int = 10,
    ) -> List[Movie]:
        """
        Enrich multiple movies with TMDB data in batches.

        Args:
            movies: List of Movie objects to enrich
            title_hints: Optional list of title hints for better matching
            batch_size: Number of movies to process concurrently

        Returns:
            List of enhanced Movie objects
        """
        if not movies:
            return []

        if not self.api_key:
            logger.info("TMDB API key not available, returning original movies")
            return movies

        logger.info(f"Starting batch enrichment of {len(movies)} movies")

        enriched_movies = []

        # Process in batches to respect rate limits
        for i in range(0, len(movies), batch_size):
            batch = movies[i : i + batch_size]
            batch_hints = None

            if title_hints:
                batch_hints = title_hints[i : i + batch_size]

            # Create tasks for concurrent processing
            tasks = []
            for j, movie in enumerate(batch):
                hint = batch_hints[j] if batch_hints and j < len(batch_hints) else None
                task = self.enrich_movie_with_tmdb_data(movie, hint)
                tasks.append(task)

            # Execute batch concurrently
            try:
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Error in batch enrichment: {result}")
                        # Add original movie if enrichment failed
                        enriched_movies.append(batch[len(enriched_movies) % len(batch)])
                    else:
                        enriched_movies.append(result)

            except Exception as e:
                logger.error(f"Error processing batch {i//batch_size + 1}: {e}")
                # Add original movies if batch failed
                enriched_movies.extend(batch)

            # Small delay between batches
            if i + batch_size < len(movies):
                await asyncio.sleep(1)

        logger.info(
            f"Completed batch enrichment: {len(enriched_movies)} movies processed"
        )
        return enriched_movies

    async def get_popular_movies(self, page: int = 1) -> List[Dict]:
        """Get popular movies from TMDB."""
        response = await self._make_request("movie/popular", {"page": page})
        return response.get("results", []) if response else []

    async def get_top_rated_movies(self, page: int = 1) -> List[Dict]:
        """Get top-rated movies from TMDB."""
        response = await self._make_request("movie/top_rated", {"page": page})
        return response.get("results", []) if response else []

    async def get_trending_movies(self, time_window: str = "week") -> List[Dict]:
        """Get trending movies from TMDB."""
        response = await self._make_request(f"trending/movie/{time_window}")
        return response.get("results", []) if response else []

    def clear_cache(self):
        """Clear the API response cache."""
        self.cache.clear()
        logger.info("TMDB cache cleared")

    async def health_check(self) -> Dict[str, Any]:
        """Check TMDB service health."""
        health_status = {
            "tmdb_service": "healthy",
            "api_key_configured": bool(self.api_key),
            "cache_size": len(self.cache),
        }

        if self.api_key:
            # Test API connection
            try:
                response = await self._make_request("configuration")
                if response:
                    health_status["api_connection"] = "connected"
                else:
                    health_status["api_connection"] = "failed"
                    health_status["tmdb_service"] = "degraded"
            except Exception as e:
                health_status["api_connection"] = f"error: {str(e)}"
                health_status["tmdb_service"] = "unhealthy"
        else:
            health_status["api_connection"] = "no_api_key"
            health_status["tmdb_service"] = "degraded"

        return health_status

    async def __aenter__(self):
        """Async context manager entry."""
        await self._init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_session()
