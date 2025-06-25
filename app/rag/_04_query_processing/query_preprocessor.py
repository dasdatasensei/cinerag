"""
Query Preprocessing

Handles cleaning, normalization, and basic preprocessing of user search queries
before they are passed to the semantic search engine.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
import unicodedata

# Configure logging
logger = logging.getLogger(__name__)


class QueryPreprocessor:
    """
    Preprocesses user queries for better semantic search results.

    Handles text cleaning, normalization, and basic query transformations
    to improve search quality and consistency.
    """

    def __init__(self):
        """Initialize the query preprocessor."""
        # Common movie-related stop words to preserve (don't remove these)
        self.preserve_words = {
            "action",
            "comedy",
            "drama",
            "horror",
            "thriller",
            "romance",
            "sci-fi",
            "fantasy",
            "animated",
            "documentary",
            "mystery",
            "adventure",
            "family",
            "western",
            "kids",
            "children",
            "dark",
            "funny",
            "scary",
            "old",
            "new",
            "classic",
            "movie",
            "film",
            "cinema",
            "flick",
        }

        # Words to remove (less meaningful for movie search)
        self.stop_words = {
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
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "me",
            "him",
            "her",
            "us",
            "them",
            "my",
            "your",
            "his",
            "her",
            "its",
            "our",
            "their",
            "this",
            "that",
            "these",
            "those",
            "some",
            "any",
            "all",
            "no",
            "not",
        }

        # Movie genre synonyms and expansions
        self.genre_synonyms = {
            "sci-fi": "science fiction",
            "scifi": "science fiction",
            "romcom": "romantic comedy",
            "rom-com": "romantic comedy",
            "action": "action adventure",
            "kids": "children family",
            "animated": "animation children",
            "superhero": "action adventure fantasy",
            "zombie": "horror thriller",
            "vampire": "horror fantasy",
            "space": "science fiction adventure",
            "war": "drama action",
            "crime": "thriller drama",
            "western": "drama adventure",
        }

        # Common movie search patterns
        self.search_patterns = [
            (r"movies?\s+like\s+", ""),  # "movies like" -> ""
            (r"films?\s+like\s+", ""),  # "films like" -> ""
            (r"similar\s+to\s+", ""),  # "similar to" -> ""
            (r"something\s+like\s+", ""),  # "something like" -> ""
            (r"find\s+me\s+", ""),  # "find me" -> ""
            (r"show\s+me\s+", ""),  # "show me" -> ""
            (r"looking\s+for\s+", ""),  # "looking for" -> ""
            (r"search\s+for\s+", ""),  # "search for" -> ""
            (r"i\s+want\s+", ""),  # "i want" -> ""
            (r"i\s+need\s+", ""),  # "i need" -> ""
        ]

    def clean_text(self, query: str) -> str:
        """
        Basic text cleaning and normalization.

        Args:
            query: Raw user query

        Returns:
            str: Cleaned query text
        """
        if not query or not isinstance(query, str):
            return ""

        # Normalize unicode characters
        query = unicodedata.normalize("NFKD", query)

        # Convert to lowercase
        query = query.lower().strip()

        # Remove extra whitespace
        query = re.sub(r"\s+", " ", query)

        # Remove special characters but keep apostrophes and hyphens
        query = re.sub(r"[^\w\s\'-]", " ", query)

        # Clean up apostrophes and contractions
        query = re.sub(r"'s\b", "", query)  # Remove possessive 's
        query = re.sub(r"n't\b", " not", query)  # "can't" -> "can not"
        query = re.sub(r"'re\b", " are", query)  # "they're" -> "they are"
        query = re.sub(r"'ll\b", " will", query)  # "I'll" -> "I will"
        query = re.sub(r"'ve\b", " have", query)  # "I've" -> "I have"
        query = re.sub(r"'d\b", " would", query)  # "I'd" -> "I would"

        # Remove extra spaces
        query = re.sub(r"\s+", " ", query).strip()

        return query

    def apply_search_patterns(self, query: str) -> str:
        """
        Apply common search pattern transformations.

        Args:
            query: Cleaned query text

        Returns:
            str: Query with patterns applied
        """
        for pattern, replacement in self.search_patterns:
            query = re.sub(pattern, replacement, query, flags=re.IGNORECASE)

        return query.strip()

    def expand_synonyms(self, query: str) -> str:
        """
        Expand genre synonyms and common movie terms.

        Args:
            query: Query text

        Returns:
            str: Query with expanded synonyms
        """
        words = query.split()
        expanded_words = []

        for word in words:
            if word in self.genre_synonyms:
                # Replace with expanded version
                expanded_words.extend(self.genre_synonyms[word].split())
            else:
                expanded_words.append(word)

        return " ".join(expanded_words)

    def remove_stop_words(self, query: str, preserve_context: bool = True) -> str:
        """
        Remove stop words while preserving important movie-related terms.

        Args:
            query: Query text
            preserve_context: Whether to preserve movie-related words

        Returns:
            str: Query with stop words removed
        """
        words = query.split()
        filtered_words = []

        for word in words:
            # Always preserve movie-related words
            if preserve_context and word in self.preserve_words:
                filtered_words.append(word)
            # Remove common stop words
            elif word not in self.stop_words:
                filtered_words.append(word)

        # Ensure we don't return empty query
        result = " ".join(filtered_words)
        return result if result.strip() else query

    def normalize_movie_terms(self, query: str) -> str:
        """
        Normalize common movie-related terms.

        Args:
            query: Query text

        Returns:
            str: Query with normalized terms
        """
        # Normalize common variations
        normalizations = {
            r"\bmovies?\b": "movie",
            r"\bfilms?\b": "movie",
            r"\bflicks?\b": "movie",
            r"\bcinema\b": "movie",
            r"\bshow\b": "movie",
            r"\bseries\b": "movie",
            r"\bkids?\b": "children",
            r"\bchild\b": "children",
            r"\bfamily\b": "children family",
            r"\bold\b": "classic",
            r"\bvintage\b": "classic",
            r"\bretro\b": "classic",
            r"\bmodern\b": "new",
            r"\brecent\b": "new",
            r"\blatest\b": "new",
            r"\bfunny\b": "comedy",
            r"\bhilarious\b": "comedy",
            r"\bscary\b": "horror",
            r"\bfrightening\b": "horror",
            r"\bterrifying\b": "horror",
            r"\bromantic\b": "romance",
            r"\blove\b": "romance",
        }

        for pattern, replacement in normalizations.items():
            query = re.sub(pattern, replacement, query, flags=re.IGNORECASE)

        return query

    def extract_year_range(self, query: str) -> Tuple[str, Optional[Dict[str, int]]]:
        """
        Extract year information from query.

        Args:
            query: Query text

        Returns:
            tuple: (cleaned_query, year_info_dict)
        """
        year_info = None

        # Pattern for year ranges (e.g., "1990s", "2000-2010", "after 2000")
        patterns = [
            (r"\b(19\d{2}s?|20\d{2}s?)\b", "single_year"),  # 1995, 1990s, 2005
            (r"\b(19\d{2}|20\d{2})\s*-\s*(19\d{2}|20\d{2})\b", "range"),  # 1990-2000
            (r"\bafter\s+(19\d{2}|20\d{2})\b", "after"),  # after 2000
            (r"\bbefore\s+(19\d{2}|20\d{2})\b", "before"),  # before 2000
            (r"\bsince\s+(19\d{2}|20\d{2})\b", "after"),  # since 2000
            (r"\bfrom\s+(19\d{2}|20\d{2})\b", "after"),  # from 2000
        ]

        for pattern, year_type in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                year_info = {"type": year_type, "match": match.group()}
                # Remove year information from query
                query = re.sub(pattern, "", query, flags=re.IGNORECASE)
                break

        # Clean up query
        query = re.sub(r"\s+", " ", query).strip()

        return query, year_info

    def preprocess_query(
        self,
        query: str,
        expand_synonyms: bool = True,
        remove_stop_words: bool = True,
        normalize_terms: bool = True,
    ) -> Dict[str, any]:
        """
        Complete query preprocessing pipeline.

        Args:
            query: Raw user query
            expand_synonyms: Whether to expand genre synonyms
            remove_stop_words: Whether to remove stop words
            normalize_terms: Whether to normalize movie terms

        Returns:
            dict: Preprocessed query information
        """
        if not query:
            return {
                "original_query": "",
                "processed_query": "",
                "year_info": None,
                "processing_steps": [],
            }

        processing_steps = []
        current_query = str(query)

        # Step 1: Basic text cleaning
        current_query = self.clean_text(current_query)
        processing_steps.append(f"cleaned: '{current_query}'")

        # Step 2: Apply search patterns
        current_query = self.apply_search_patterns(current_query)
        processing_steps.append(f"patterns_applied: '{current_query}'")

        # Step 3: Extract year information
        current_query, year_info = self.extract_year_range(current_query)
        if year_info:
            processing_steps.append(f"year_extracted: {year_info}")

        # Step 4: Normalize movie terms
        if normalize_terms:
            current_query = self.normalize_movie_terms(current_query)
            processing_steps.append(f"normalized: '{current_query}'")

        # Step 5: Expand synonyms
        if expand_synonyms:
            expanded_query = self.expand_synonyms(current_query)
            if expanded_query != current_query:
                current_query = expanded_query
                processing_steps.append(f"synonyms_expanded: '{current_query}'")

        # Step 6: Remove stop words
        if remove_stop_words:
            filtered_query = self.remove_stop_words(current_query)
            if filtered_query != current_query:
                current_query = filtered_query
                processing_steps.append(f"stop_words_removed: '{current_query}'")

        # Final cleanup
        current_query = re.sub(r"\s+", " ", current_query).strip()

        # Ensure we have something to search with
        if not current_query:
            current_query = self.clean_text(query)

        result = {
            "original_query": query,
            "processed_query": current_query,
            "year_info": year_info,
            "processing_steps": processing_steps,
            "query_length": len(current_query),
            "word_count": len(current_query.split()) if current_query else 0,
        }

        logger.info(f"Query preprocessing: '{query}' -> '{current_query}'")
        return result


# Global instance for easy access
query_preprocessor = None


def get_query_preprocessor() -> QueryPreprocessor:
    """
    Get or create global query preprocessor instance.

    Returns:
        QueryPreprocessor: Global preprocessor instance
    """
    global query_preprocessor

    if query_preprocessor is None:
        query_preprocessor = QueryPreprocessor()

    return query_preprocessor
