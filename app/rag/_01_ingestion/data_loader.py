"""
MovieLens Data Loader

Loads and preprocesses MovieLens dataset for the RAG system.
Handles movies.csv and ratings.csv with data cleaning and validation.
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MovieLensDataLoader:
    """Loads and preprocesses MovieLens dataset"""

    def __init__(self, data_path: str = "data/raw/latest-small/ml-latest-small"):
        """
        Initialize the data loader

        Args:
            data_path: Path to MovieLens data directory
        """
        self.data_path = Path(data_path)
        self.movies_df = None
        self.ratings_df = None
        self.processed_movies = None

    def load_movies(self) -> pd.DataFrame:
        """
        Load and clean movies.csv

        Returns:
            DataFrame with cleaned movie data
        """
        try:
            movies_file = self.data_path / "movies.csv"
            logger.info(f"Loading movies from {movies_file}")

            # Load movies data
            self.movies_df = pd.read_csv(movies_file)
            logger.info(f"Loaded {len(self.movies_df)} movies")

            # Clean and preprocess
            self.movies_df = self._clean_movies_data(self.movies_df)

            return self.movies_df

        except Exception as e:
            logger.error(f"Error loading movies data: {e}")
            raise

    def load_ratings(self) -> pd.DataFrame:
        """
        Load and clean ratings.csv

        Returns:
            DataFrame with cleaned ratings data
        """
        try:
            ratings_file = self.data_path / "ratings.csv"
            logger.info(f"Loading ratings from {ratings_file}")

            # Load ratings data
            self.ratings_df = pd.read_csv(ratings_file)
            logger.info(f"Loaded {len(self.ratings_df)} ratings")

            # Clean and preprocess
            self.ratings_df = self._clean_ratings_data(self.ratings_df)

            return self.ratings_df

        except Exception as e:
            logger.error(f"Error loading ratings data: {e}")
            raise

    def _clean_movies_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and preprocess movies data

        Args:
            df: Raw movies DataFrame

        Returns:
            Cleaned movies DataFrame
        """
        logger.info("Cleaning movies data...")

        # Create a copy to avoid modifying original
        cleaned_df = df.copy()

        # Extract year from title
        cleaned_df["year"] = cleaned_df["title"].str.extract(r"\((\d{4})\)$")[0]
        cleaned_df["year"] = pd.to_numeric(cleaned_df["year"], errors="coerce")

        # Clean title (remove year)
        cleaned_df["clean_title"] = cleaned_df["title"].str.replace(
            r"\s*\(\d{4}\)$", "", regex=True
        )

        # Process genres
        cleaned_df["genres_list"] = cleaned_df["genres"].str.split("|")
        cleaned_df["num_genres"] = cleaned_df["genres_list"].apply(len)

        # Handle missing values
        cleaned_df["year"].fillna(0, inplace=True)
        cleaned_df["genres"].fillna("Unknown", inplace=True)

        # Remove duplicates
        initial_count = len(cleaned_df)
        cleaned_df = cleaned_df.drop_duplicates(subset=["movieId"])
        final_count = len(cleaned_df)

        if initial_count != final_count:
            logger.warning(f"Removed {initial_count - final_count} duplicate movies")

        logger.info(f"Movies data cleaned: {len(cleaned_df)} records")
        return cleaned_df

    def _clean_ratings_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and preprocess ratings data

        Args:
            df: Raw ratings DataFrame

        Returns:
            Cleaned ratings DataFrame
        """
        logger.info("Cleaning ratings data...")

        # Create a copy to avoid modifying original
        cleaned_df = df.copy()

        # Convert timestamp to datetime
        cleaned_df["datetime"] = pd.to_datetime(cleaned_df["timestamp"], unit="s")

        # Validate rating range
        cleaned_df = cleaned_df[cleaned_df["rating"].between(0.5, 5.0)]

        # Remove invalid movieIds and userIds
        cleaned_df = cleaned_df[cleaned_df["movieId"] > 0]
        cleaned_df = cleaned_df[cleaned_df["userId"] > 0]

        # Remove duplicates (same user rating same movie multiple times - keep latest)
        cleaned_df = cleaned_df.sort_values("timestamp").drop_duplicates(
            subset=["userId", "movieId"], keep="last"
        )

        logger.info(f"Ratings data cleaned: {len(cleaned_df)} records")
        return cleaned_df

    def create_movie_features(self) -> pd.DataFrame:
        """
        Create enriched movie features by combining movies and ratings

        Returns:
            DataFrame with movie features including rating statistics
        """
        if self.movies_df is None or self.ratings_df is None:
            raise ValueError("Must load movies and ratings data first")

        logger.info("Creating movie features...")

        # Calculate rating statistics per movie
        rating_stats = (
            self.ratings_df.groupby("movieId")
            .agg({"rating": ["count", "mean", "std"], "userId": "nunique"})
            .round(2)
        )

        # Flatten column names
        rating_stats.columns = ["num_ratings", "avg_rating", "rating_std", "num_users"]
        rating_stats = rating_stats.reset_index()

        # Fill NaN standard deviations with 0 (for movies with only 1 rating)
        rating_stats["rating_std"].fillna(0, inplace=True)

        # Merge with movies data
        enriched_movies = self.movies_df.merge(rating_stats, on="movieId", how="left")

        # Fill missing rating stats for movies with no ratings
        enriched_movies[["num_ratings", "avg_rating", "rating_std", "num_users"]] = (
            enriched_movies[
                ["num_ratings", "avg_rating", "rating_std", "num_users"]
            ].fillna(0)
        )

        # Create popularity score (simple formula combining ratings and count)
        enriched_movies["popularity_score"] = (
            enriched_movies["avg_rating"] * np.log1p(enriched_movies["num_ratings"])
        ).round(2)

        # Create description for embedding (combining title, genres, and basic info)
        enriched_movies["description"] = enriched_movies.apply(
            self._create_description, axis=1
        )

        self.processed_movies = enriched_movies
        logger.info(f"Created features for {len(enriched_movies)} movies")

        return enriched_movies

    def _create_description(self, row) -> str:
        """
        Create a text description for each movie for embedding

        Args:
            row: Movie data row

        Returns:
            Text description string
        """
        description_parts = []

        # Add title
        description_parts.append(f"Title: {row['clean_title']}")

        # Add year if available
        if row["year"] > 0:
            description_parts.append(f"Year: {int(row['year'])}")

        # Add genres
        if row["genres"] != "Unknown":
            genres = row["genres"].replace("|", ", ")
            description_parts.append(f"Genres: {genres}")

        # Add rating info if available
        if row["num_ratings"] > 0:
            description_parts.append(f"Average Rating: {row['avg_rating']:.1f}/5.0")
            description_parts.append(f"Number of Ratings: {int(row['num_ratings'])}")

        return ". ".join(description_parts)

    def get_data_summary(self) -> Dict:
        """
        Get summary statistics of loaded data

        Returns:
            Dictionary with data summary
        """
        summary = {}

        if self.movies_df is not None:
            summary["movies"] = {
                "total_movies": len(self.movies_df),
                "unique_genres": len(
                    set(
                        [
                            g
                            for genres in self.movies_df["genres_list"]
                            for g in genres
                            if g != "Unknown"
                        ]
                    )
                ),
                "year_range": (
                    (
                        int(self.movies_df["year"].min()),
                        int(self.movies_df["year"].max()),
                    )
                    if self.movies_df["year"].max() > 0
                    else (0, 0)
                ),
                "movies_with_ratings": (
                    len(self.movies_df[self.movies_df["num_ratings"] > 0])
                    if "num_ratings" in self.movies_df.columns
                    else 0
                ),
            }

        if self.ratings_df is not None:
            summary["ratings"] = {
                "total_ratings": len(self.ratings_df),
                "unique_users": self.ratings_df["userId"].nunique(),
                "unique_movies": self.ratings_df["movieId"].nunique(),
                "rating_range": (
                    self.ratings_df["rating"].min(),
                    self.ratings_df["rating"].max(),
                ),
                "avg_rating": round(self.ratings_df["rating"].mean(), 2),
            }

        return summary

    def get_popular_movies(self, limit: int = 20):
        """
        Get popular movies based on popularity score

        Args:
            limit: Number of movies to return

        Returns:
            List of Movie objects
        """
        self._ensure_data_loaded()

        # Sort by popularity score (highest first)
        popular_movies = self.processed_movies.nlargest(limit, "popularity_score")

        return self._dataframe_to_movie_objects(popular_movies)

    def get_movies_by_genre(self, genre: str, limit: int = 20):
        """
        Get movies by genre

        Args:
            genre: Genre to filter by
            limit: Number of movies to return

        Returns:
            List of Movie objects
        """
        self._ensure_data_loaded()

        # Filter movies by genre
        genre_movies = self.processed_movies[
            self.processed_movies["genres"].str.contains(genre, case=False, na=False)
        ]

        # Sort by popularity score
        genre_movies = genre_movies.nlargest(limit, "popularity_score")

        return self._dataframe_to_movie_objects(genre_movies)

    def search_movies(self, query: str, limit: int = 10):
        """
        Search movies by title

        Args:
            query: Search query
            limit: Number of movies to return

        Returns:
            List of Movie objects
        """
        self._ensure_data_loaded()

        # Search in title (case insensitive)
        query_lower = query.lower()
        matching_movies = self.processed_movies[
            self.processed_movies["clean_title"]
            .str.lower()
            .str.contains(query_lower, na=False)
        ]

        # Sort by popularity score
        matching_movies = matching_movies.nlargest(limit, "popularity_score")

        return self._dataframe_to_movie_objects(matching_movies)

    def get_movie_by_id(self, movie_id: int):
        """
        Get a specific movie by ID

        Args:
            movie_id: Movie ID to find

        Returns:
            Movie object or None if not found
        """
        self._ensure_data_loaded()

        movie_row = self.processed_movies[self.processed_movies["movieId"] == movie_id]

        if movie_row.empty:
            return None

        return self._dataframe_to_movie_objects(movie_row)[0]

    def get_genres(self):
        """
        Get all unique genres

        Returns:
            List of genre strings
        """
        self._ensure_data_loaded()

        # Extract all genres from the genres column
        all_genres = set()
        for genres_str in self.processed_movies["genres"].dropna():
            if genres_str != "Unknown":
                genres_list = genres_str.split("|")
                all_genres.update(genres_list)

        return sorted(list(all_genres))

    def get_user_ratings(self, user_id: int):
        """
        Get ratings for a specific user

        Args:
            user_id: User ID to get ratings for

        Returns:
            Dictionary with user ratings data
        """
        self._ensure_data_loaded()

        if self.ratings_df is None:
            return {"error": "No ratings data loaded"}

        user_ratings = self.ratings_df[self.ratings_df["userId"] == user_id]

        if user_ratings.empty:
            return {"error": "User not found", "user_id": user_id}

        # Get movie details for rated movies
        rated_movie_ids = user_ratings["movieId"].tolist()
        rated_movies = self.processed_movies[
            self.processed_movies["movieId"].isin(rated_movie_ids)
        ]

        # Merge ratings with movie details
        user_data = user_ratings.merge(
            rated_movies[["movieId", "clean_title", "genres", "year"]],
            on="movieId",
            how="left",
        )

        return {
            "user_id": user_id,
            "total_ratings": len(user_ratings),
            "average_rating": round(user_ratings["rating"].mean(), 2),
            "ratings": user_data.to_dict("records"),
        }

    def _ensure_data_loaded(self):
        """Ensure all necessary data is loaded"""
        if self.movies_df is None:
            self.load_movies()
        if self.ratings_df is None:
            self.load_ratings()
        if self.processed_movies is None:
            self.create_movie_features()

    def _dataframe_to_movie_objects(self, df):
        """
        Convert DataFrame rows to Movie objects

        Args:
            df: DataFrame with movie data

        Returns:
            List of Movie objects (as dictionaries for now)
        """
        from ...models import Movie

        movies = []
        for _, row in df.iterrows():
            # Create movie object (simplified - adjust fields as needed)
            movie_data = {
                "id": int(row["movieId"]),
                "title": row["clean_title"],
                "overview": row.get("description", ""),
                "genres": (
                    row["genres"].split("|") if row["genres"] != "Unknown" else []
                ),
                "release_date": str(int(row["year"])) if row["year"] > 0 else None,
                "vote_average": float(row.get("avg_rating", 0)),
                "vote_count": int(row.get("num_ratings", 0)),
                "popularity": float(row.get("popularity_score", 0)),
                "poster_path": None,  # Not available in MovieLens data
                "backdrop_path": None,  # Not available in MovieLens data
                "imdb_id": None,  # Not available in MovieLens data
                "tmdb_id": None,  # Not available in MovieLens data
            }

            try:
                movie = Movie(**movie_data)
                movies.append(movie)
            except Exception as e:
                logger.warning(
                    f"Error creating Movie object for {row['clean_title']}: {e}"
                )
                continue

        return movies


def load_movielens_data(
    data_path: str = "data/raw/latest-small/ml-latest-small",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Convenience function to load all MovieLens data

    Args:
        data_path: Path to MovieLens data directory

    Returns:
        Tuple of (movies_df, ratings_df, enriched_movies_df)
    """
    loader = MovieLensDataLoader(data_path)

    # Load raw data
    movies_df = loader.load_movies()
    ratings_df = loader.load_ratings()

    # Create enriched features
    enriched_movies_df = loader.create_movie_features()

    # Print summary
    summary = loader.get_data_summary()
    logger.info("Data loading complete!")
    logger.info(f"Summary: {summary}")

    return movies_df, ratings_df, enriched_movies_df


if __name__ == "__main__":
    # Test the data loader
    movies, ratings, enriched = load_movielens_data()
    print(f"Loaded {len(movies)} movies and {len(ratings)} ratings")
    print(f"Sample movie description: {enriched.iloc[0]['description']}")
