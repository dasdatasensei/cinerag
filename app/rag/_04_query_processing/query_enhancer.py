"""
Query Enhancer for RAG Query Processing

This service enhances user queries before they are processed by the retrieval system,
improving search quality through query expansion, normalization, and optimization.
"""

import re
import logging
from typing import List, Dict, Set, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class QueryEnhancer:
    """Enhanced query processing for improved movie search and recommendations."""

    def __init__(self):
        # Common movie-related synonyms and expansions
        self.genre_synonyms = {
            "scary": "horror",
            "funny": "comedy",
            "romantic": "romance",
            "action-packed": "action",
            "sci-fi": "science fiction",
            "scifi": "science fiction",
            "superhero": "action adventure",
            "kids": "family animation",
            "children": "family animation",
            "thriller": "thriller suspense",
            "drama": "drama emotional",
            "documentary": "documentary educational",
            "animated": "animation",
            "foreign": "international",
            "classic": "vintage old",
            "recent": "new latest",
            "popular": "trending top-rated",
        }

        # Movie quality descriptors
        self.quality_terms = {
            "good": "high-rated quality excellent",
            "best": "top-rated excellent outstanding",
            "great": "excellent outstanding high-quality",
            "amazing": "outstanding excellent incredible",
            "awesome": "excellent great outstanding",
            "terrible": "low-rated poor bad",
            "bad": "low-rated poor",
            "boring": "slow-paced tedious",
            "exciting": "thrilling action-packed engaging",
            "emotional": "touching heartfelt moving",
            "funny": "comedy humorous hilarious",
            "dark": "serious gritty intense",
            "light": "feel-good uplifting cheerful",
        }

        # Mood-based expansions
        self.mood_expansions = {
            "sad": "emotional drama tearjerker",
            "happy": "uplifting feel-good comedy",
            "scared": "horror thriller suspense",
            "excited": "action adventure thrilling",
            "relaxed": "calm peaceful slow-paced",
            "romantic": "love romance relationship",
            "nostalgic": "classic vintage retro",
            "adventurous": "adventure action exploration",
            "thoughtful": "philosophical deep meaningful",
        }

        # Common misspellings and corrections
        self.spell_corrections = {
            "recomend": "recommend",
            "movei": "movie",
            "moive": "movie",
            "fim": "film",
            "wath": "watch",
            "similer": "similar",
            "similiar": "similar",
            "genere": "genre",
            "commedy": "comedy",
            "horrer": "horror",
            "fantacy": "fantasy",
            "acton": "action",
            "thriler": "thriller",
        }

        # Time period mappings
        self.time_periods = {
            "recent": "2020-2024",
            "new": "2020-2024",
            "latest": "2022-2024",
            "current": "2023-2024",
            "modern": "2010-2024",
            "classic": "1930-1980",
            "old": "1930-1990",
            "vintage": "1930-1970",
            "90s": "1990-1999",
            "nineties": "1990-1999",
            "2000s": "2000-2009",
            "2010s": "2010-2019",
        }

    def enhance_query(self, query: str) -> str:
        """
        Main query enhancement method that applies multiple enhancement techniques.

        Args:
            query: Original user query

        Returns:
            Enhanced query optimized for vector search
        """
        if not query or not query.strip():
            return query

        try:
            enhanced = query.lower().strip()

            # Apply enhancements in order
            enhanced = self._correct_spelling(enhanced)
            enhanced = self._expand_synonyms(enhanced)
            enhanced = self._expand_quality_terms(enhanced)
            enhanced = self._expand_mood_terms(enhanced)
            enhanced = self._add_time_context(enhanced)
            enhanced = self._normalize_query(enhanced)

            logger.debug(f"Enhanced query: '{query}' → '{enhanced}'")
            return enhanced

        except Exception as e:
            logger.error(f"Error enhancing query '{query}': {e}")
            return query  # Return original on error

    def _correct_spelling(self, query: str) -> str:
        """Correct common spelling mistakes."""
        corrected = query
        for misspell, correct in self.spell_corrections.items():
            corrected = re.sub(r"\b" + re.escape(misspell) + r"\b", correct, corrected)
        return corrected

    def _expand_synonyms(self, query: str) -> str:
        """Expand genre synonyms to improve matching."""
        expanded = query
        for synonym, expansion in self.genre_synonyms.items():
            if synonym in expanded:
                expanded = expanded.replace(synonym, f"{synonym} {expansion}")
        return expanded

    def _expand_quality_terms(self, query: str) -> str:
        """Expand quality descriptors."""
        expanded = query
        for term, expansion in self.quality_terms.items():
            if (
                f" {term} " in f" {expanded} "
                or expanded.startswith(f"{term} ")
                or expanded.endswith(f" {term}")
            ):
                expanded = expanded.replace(term, f"{term} {expansion}")
        return expanded

    def _expand_mood_terms(self, query: str) -> str:
        """Expand mood-based terms."""
        expanded = query
        for mood, expansion in self.mood_expansions.items():
            if (
                f"feeling {mood}" in expanded
                or f"feel {mood}" in expanded
                or f"i'm {mood}" in expanded
            ):
                expanded = f"{expanded} {expansion}"
        return expanded

    def _add_time_context(self, query: str) -> str:
        """Add time period context where applicable."""
        enhanced = query
        for period, years in self.time_periods.items():
            if period in enhanced:
                enhanced = f"{enhanced} from {years}"
        return enhanced

    def _normalize_query(self, query: str) -> str:
        """Final normalization and cleanup."""
        # Remove extra spaces
        normalized = re.sub(r"\s+", " ", query).strip()

        # Remove redundant words
        words = normalized.split()
        seen = set()
        unique_words = []
        for word in words:
            if word not in seen:
                unique_words.append(word)
                seen.add(word)

        return " ".join(unique_words)

    def extract_filters(self, query: str) -> Dict[str, any]:
        """
        Extract explicit filters from the query.

        Returns:
            Dictionary with extracted filters (genre, year, rating, etc.)
        """
        filters = {}
        query_lower = query.lower()

        # Extract year ranges
        year_match = re.search(r"(?:from\s+)?(\d{4})(?:\s*-\s*(\d{4}))?", query)
        if year_match:
            start_year = int(year_match.group(1))
            end_year = int(year_match.group(2)) if year_match.group(2) else start_year
            filters["year_range"] = (start_year, end_year)

        # Extract rating requirements
        rating_match = re.search(
            r"rated?\s+(?:above|over|at\s+least)\s+(\d+(?:\.\d+)?)", query_lower
        )
        if rating_match:
            filters["min_rating"] = float(rating_match.group(1))

        # Extract genre preferences
        detected_genres = []
        for genre in [
            "action",
            "comedy",
            "drama",
            "horror",
            "romance",
            "thriller",
            "sci-fi",
            "fantasy",
            "animation",
            "documentary",
            "crime",
            "mystery",
        ]:
            if genre in query_lower:
                detected_genres.append(genre.title())

        if detected_genres:
            filters["genres"] = detected_genres

        # Extract length preferences
        if any(term in query_lower for term in ["short", "brief", "quick"]):
            filters["max_runtime"] = 90
        elif any(term in query_lower for term in ["long", "epic", "extended"]):
            filters["min_runtime"] = 150

        return filters

    def suggest_query_improvements(
        self, query: str, results_count: int = 0
    ) -> List[str]:
        """
        Suggest query improvements if search results are poor.

        Args:
            query: Original query
            results_count: Number of results returned

        Returns:
            List of suggested improvements
        """
        suggestions = []

        if results_count == 0:
            suggestions.extend(
                [
                    "Try using more general terms (e.g., 'action movies' instead of specific titles)",
                    "Check spelling of movie titles and genres",
                    "Use mood descriptors like 'funny', 'scary', or 'romantic'",
                    "Try searching by genre instead of specific characteristics",
                ]
            )

        elif results_count < 3:
            suggestions.extend(
                [
                    "Add genre keywords to get more results",
                    "Remove very specific terms to broaden the search",
                    "Try using synonyms for your search terms",
                ]
            )

        # Specific suggestions based on query content
        if len(query.split()) > 10:
            suggestions.append("Try using fewer, more specific keywords")

        if not any(
            genre in query.lower()
            for genre in ["action", "comedy", "drama", "horror", "romance"]
        ):
            suggestions.append("Consider adding a genre to help narrow down results")

        return suggestions[:3]  # Return top 3 suggestions

    def get_semantic_keywords(self, query: str) -> List[str]:
        """
        Extract semantic keywords for enhanced vector search.

        Returns:
            List of semantically relevant keywords
        """
        keywords = set()
        query_lower = query.lower()

        # Add original words
        words = re.findall(r"\b\w+\b", query_lower)
        keywords.update(words)

        # Add semantic expansions
        for word in words:
            if word in self.genre_synonyms:
                keywords.update(self.genre_synonyms[word].split())
            if word in self.quality_terms:
                keywords.update(self.quality_terms[word].split())
            if word in self.mood_expansions:
                keywords.update(self.mood_expansions[word].split())

        # Remove common stop words that don't add value
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
            "i",
            "me",
            "my",
            "you",
            "your",
            "it",
            "its",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
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
        }
        keywords = [k for k in keywords if k not in stop_words and len(k) > 2]

        return list(keywords)

    def optimize_for_vector_search(self, query: str) -> str:
        """
        Optimize query specifically for vector similarity search.

        Returns:
            Query optimized for embedding-based search
        """
        # Start with enhanced query
        optimized = self.enhance_query(query)

        # Add semantic keywords
        keywords = self.get_semantic_keywords(query)

        # Combine with important keywords
        important_keywords = [
            k for k in keywords if len(k) > 4 or k in ["sci-fi", "drama", "action"]
        ]

        if important_keywords:
            optimized = (
                f"{optimized} {' '.join(important_keywords[:5])}"  # Add top 5 keywords
            )

        return self._normalize_query(optimized)


# Global instance for easy access
query_enhancer = None


def get_query_enhancer() -> QueryEnhancer:
    """
    Get or create global query enhancer instance.

    Returns:
        QueryEnhancer: Global enhancer instance
    """
    global query_enhancer

    if query_enhancer is None:
        query_enhancer = QueryEnhancer()

    return query_enhancer
