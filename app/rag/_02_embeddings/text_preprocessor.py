"""
Text Preprocessor for Movie Embeddings

Handles cleaning and preparation of movie text data for embedding generation.
Creates rich text representations by combining multiple movie fields.
"""

import re
import html
import logging
from typing import List, Dict, Optional, Any
import pandas as pd

logger = logging.getLogger(__name__)


class MovieTextPreprocessor:
    """Preprocesses movie data into embedding-ready text"""

    def __init__(self):
        """Initialize text preprocessor"""
        self.setup_regex_patterns()

    def setup_regex_patterns(self):
        """Setup regex patterns for text cleaning"""
        # Remove HTML tags
        self.html_pattern = re.compile(r"<[^>]+>")
        # Normalize whitespace
        self.whitespace_pattern = re.compile(r"\s+")
        # Remove special characters but keep important punctuation
        self.special_chars_pattern = re.compile(r"[^\w\s\.\,\!\?\:\;\-\(\)]")

    def clean_text(self, text: str) -> str:
        """
        Clean individual text fields

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        if not text or pd.isna(text):
            return ""

        # Convert to string and handle HTML entities
        text = str(text)
        text = html.unescape(text)

        # Remove HTML tags
        text = self.html_pattern.sub(" ", text)

        # Remove excessive special characters
        text = self.special_chars_pattern.sub(" ", text)

        # Normalize whitespace
        text = self.whitespace_pattern.sub(" ", text)

        # Strip and return
        return text.strip()

    def parse_genres_list(self, genres_str: str) -> List[str]:
        """
        Parse genres from string representation of list

        Args:
            genres_str: String like "['Comedy', 'Drama']"

        Returns:
            List of genre strings
        """
        if not genres_str or pd.isna(genres_str):
            return []

        try:
            # Remove brackets and quotes, split by comma
            cleaned = genres_str.strip("[]").replace("'", "").replace('"', "")
            genres = [g.strip() for g in cleaned.split(",") if g.strip()]
            return genres
        except Exception as e:
            logger.warning(f"Error parsing genres '{genres_str}': {e}")
            return []

    def create_movie_description(self, movie_row: Dict[str, Any]) -> str:
        """
        Create rich text description for a movie

        Args:
            movie_row: Dictionary containing movie data

        Returns:
            Rich text description for embedding
        """
        parts = []

        # Title and year
        title = self.clean_text(movie_row.get("clean_title", ""))
        year = movie_row.get("year")
        if title:
            if year and not pd.isna(year):
                parts.append(f"Movie: {title} ({int(year)})")
            else:
                parts.append(f"Movie: {title}")

        # Genres
        genres_list = self.parse_genres_list(str(movie_row.get("genres_list", "")))
        if genres_list:
            parts.append(f"Genres: {', '.join(genres_list)}")

        # Rating information
        avg_rating = movie_row.get("avg_rating")
        num_ratings = movie_row.get("num_ratings")
        if avg_rating and not pd.isna(avg_rating):
            rating_text = f"Average rating: {avg_rating:.1f}/5.0"
            if num_ratings and not pd.isna(num_ratings):
                rating_text += f" from {int(num_ratings)} ratings"
            parts.append(rating_text)

        # Popularity
        popularity = movie_row.get("popularity_score")
        if popularity and not pd.isna(popularity):
            parts.append(f"Popularity score: {popularity:.1f}")

        # Description (if available from TMDB)
        description = movie_row.get("description", "")
        if description and not pd.isna(description) and description.strip():
            cleaned_desc = self.clean_text(description)
            if (
                cleaned_desc and len(cleaned_desc) > 20
            ):  # Only include substantial descriptions
                parts.append(f"Description: {cleaned_desc}")

        # Join all parts
        return ". ".join(parts) + "."

    def create_search_variants(self, movie_row: Dict[str, Any]) -> List[str]:
        """
        Create multiple text variants for better embedding coverage

        Args:
            movie_row: Dictionary containing movie data

        Returns:
            List of text variants
        """
        variants = []

        # Main description
        main_desc = self.create_movie_description(movie_row)
        variants.append(main_desc)

        # Title + genres variant
        title = self.clean_text(movie_row.get("clean_title", ""))
        genres_list = self.parse_genres_list(str(movie_row.get("genres_list", "")))
        if title and genres_list:
            variants.append(f"{title} is a {', '.join(genres_list[:3])} movie")

        # Genre-focused variant
        if genres_list:
            year = movie_row.get("year")
            year_text = f" from {int(year)}" if year and not pd.isna(year) else ""
            variants.append(f"A {', '.join(genres_list)} film{year_text}")

        return variants

    def preprocess_movie_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess entire dataframe of movies

        Args:
            df: DataFrame with movie data

        Returns:
            DataFrame with added embedding text columns
        """
        logger.info(f"Preprocessing {len(df)} movies for embedding...")

        processed_df = df.copy()

        # Create main embedding text
        processed_df["embedding_text"] = df.apply(
            lambda row: self.create_movie_description(row.to_dict()), axis=1
        )

        # Create text variants
        processed_df["text_variants"] = df.apply(
            lambda row: self.create_search_variants(row.to_dict()), axis=1
        )

        # Calculate text statistics
        processed_df["text_length"] = processed_df["embedding_text"].str.len()
        processed_df["word_count"] = (
            processed_df["embedding_text"].str.split().str.len()
        )

        # Log statistics
        avg_length = processed_df["text_length"].mean()
        avg_words = processed_df["word_count"].mean()
        logger.info(f"Average text length: {avg_length:.1f} characters")
        logger.info(f"Average word count: {avg_words:.1f} words")

        return processed_df

    def validate_preprocessed_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate preprocessed data quality

        Args:
            df: Preprocessed DataFrame

        Returns:
            Validation report
        """
        report = {
            "total_movies": len(df),
            "empty_texts": 0,
            "short_texts": 0,
            "average_length": 0,
            "min_length": 0,
            "max_length": 0,
        }

        if "embedding_text" in df.columns:
            text_lengths = df["embedding_text"].str.len()
            report["empty_texts"] = (text_lengths == 0).sum()
            report["short_texts"] = (text_lengths < 20).sum()
            report["average_length"] = text_lengths.mean()
            report["min_length"] = text_lengths.min()
            report["max_length"] = text_lengths.max()

        logger.info(f"Validation Report: {report}")
        return report


def create_text_preprocessor() -> MovieTextPreprocessor:
    """Factory function to create text preprocessor"""
    return MovieTextPreprocessor()


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Test with sample data
    sample_data = {
        "movieId": 1,
        "clean_title": "Toy Story",
        "year": 1995,
        "genres_list": "['Adventure', 'Animation', 'Children', 'Comedy', 'Fantasy']",
        "avg_rating": 3.92,
        "num_ratings": 215,
        "popularity_score": 21.07,
        "description": "A cowboy doll is profoundly threatened and jealous when a new spaceman figure supplants him as top toy in a boy's room.",
    }

    preprocessor = create_text_preprocessor()
    result = preprocessor.create_movie_description(sample_data)
    print("Sample embedding text:")
    print(result)
    print("\nText variants:")
    for variant in preprocessor.create_search_variants(sample_data):
        print(f"- {variant}")
