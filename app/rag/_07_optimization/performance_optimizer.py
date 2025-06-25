"""
Performance Optimizer

Advanced optimization techniques for RAG pipeline performance improvement.
Includes query optimization, ranking optimization, and system tuning.
"""

import logging
import time
import math
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import numpy as np
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Result of optimization operation."""

    original_query: str
    optimized_query: str
    optimization_type: str
    improvement_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceProfile:
    """Performance profile for query types."""

    query_pattern: str
    avg_latency: float
    success_rate: float
    typical_result_count: int
    optimization_suggestions: List[str] = field(default_factory=list)


class QueryOptimizer:
    """
    Intelligent query optimization for improved search performance.

    Features:
    - Query expansion and contraction
    - Intent-based optimization
    - Performance-driven query rewriting
    - A/B testing for query variations
    """

    def __init__(self):
        """Initialize query optimizer."""
        self.optimization_history = deque(maxlen=1000)
        self.performance_profiles = {}

        # Common optimization patterns
        self.expansion_terms = {
            "action": ["thriller", "adventure", "exciting", "intense"],
            "comedy": ["funny", "humorous", "laugh", "amusing"],
            "horror": ["scary", "frightening", "terror", "suspense"],
            "romance": ["love", "romantic", "relationship", "couple"],
            "sci-fi": ["science fiction", "futuristic", "space", "technology"],
            "drama": ["emotional", "serious", "character-driven", "story"],
        }

        # Query simplification patterns
        self.simplification_patterns = [
            # Remove redundant words
            ("very good", "good"),
            ("really great", "great"),
            ("highly recommended", "recommended"),
            # Normalize common phrases
            ("movies like", "similar to"),
            ("films similar to", "similar to"),
            ("something like", "similar to"),
        ]

    def optimize_query(
        self, query: str, context: Optional[Dict] = None
    ) -> OptimizationResult:
        """
        Optimize a query for better performance and relevance.

        Args:
            query: Original query string
            context: Additional context (previous searches, user preferences, etc.)

        Returns:
            OptimizationResult: Optimization details and improved query
        """
        original_query = query.strip()
        optimized_query = original_query
        optimization_type = "none"
        improvement_score = 0.0
        metadata = {}

        # Skip optimization for very short or very long queries
        if len(original_query) < 3 or len(original_query) > 200:
            return OptimizationResult(
                original_query=original_query,
                optimized_query=optimized_query,
                optimization_type="skipped",
                improvement_score=0.0,
                metadata={"reason": "query length out of optimal range"},
            )

        # Apply optimization strategies
        candidates = []

        # 1. Query expansion for short queries
        if len(original_query.split()) <= 2:
            expanded = self._expand_query(original_query)
            if expanded != original_query:
                candidates.append(("expansion", expanded, 0.3))

        # 2. Query simplification for complex queries
        if len(original_query.split()) >= 6:
            simplified = self._simplify_query(original_query)
            if simplified != original_query:
                candidates.append(("simplification", simplified, 0.2))

        # 3. Intent-based optimization
        intent_optimized = self._optimize_by_intent(original_query)
        if intent_optimized != original_query:
            candidates.append(("intent_optimization", intent_optimized, 0.4))

        # 4. Performance-based optimization (if we have historical data)
        perf_optimized = self._optimize_by_performance(original_query)
        if perf_optimized != original_query:
            candidates.append(("performance_optimization", perf_optimized, 0.5))

        # Select best optimization
        if candidates:
            optimization_type, optimized_query, improvement_score = max(
                candidates, key=lambda x: x[2]
            )
            metadata["candidates"] = len(candidates)
            metadata["selected_strategy"] = optimization_type

        result = OptimizationResult(
            original_query=original_query,
            optimized_query=optimized_query,
            optimization_type=optimization_type,
            improvement_score=improvement_score,
            metadata=metadata,
        )

        # Store for learning
        self.optimization_history.append(result)

        return result

    def _expand_query(self, query: str) -> str:
        """Expand short queries with related terms."""
        query_lower = query.lower()
        expanded_terms = []

        for genre, related_terms in self.expansion_terms.items():
            if genre in query_lower:
                # Add one relevant expansion term
                for term in related_terms:
                    if term not in query_lower:
                        expanded_terms.append(term)
                        break

        if expanded_terms:
            return f"{query} {expanded_terms[0]}"

        return query

    def _simplify_query(self, query: str) -> str:
        """Simplify complex queries by removing redundancy."""
        simplified = query

        for pattern, replacement in self.simplification_patterns:
            simplified = simplified.replace(pattern, replacement)

        # Remove duplicate words
        words = simplified.split()
        seen = set()
        unique_words = []
        for word in words:
            word_lower = word.lower()
            if word_lower not in seen:
                unique_words.append(word)
                seen.add(word_lower)

        return " ".join(unique_words)

    def _optimize_by_intent(self, query: str) -> str:
        """Optimize query based on detected intent."""
        query_lower = query.lower()

        # Detect recommendation intent
        if any(phrase in query_lower for phrase in ["like", "similar to", "recommend"]):
            # Extract the main subject
            if "like" in query_lower:
                parts = query_lower.split("like")
                if len(parts) > 1:
                    subject = parts[1].strip()
                    return f"similar to {subject}"

        # Detect specific movie search
        if any(
            phrase in query_lower for phrase in ["find", "search for", "looking for"]
        ):
            # Remove search verbs for cleaner query
            optimized = query_lower
            for phrase in ["find", "search for", "looking for", "i want", "show me"]:
                optimized = optimized.replace(phrase, "").strip()
            return optimized

        return query

    def _optimize_by_performance(self, query: str) -> str:
        """Optimize query based on historical performance data."""
        # Check if we have performance data for similar queries
        query_pattern = self._extract_query_pattern(query)

        if query_pattern in self.performance_profiles:
            profile = self.performance_profiles[query_pattern]

            # If this pattern performs poorly, try optimization
            if profile.avg_latency > 0.5 or profile.success_rate < 0.8:
                # Apply suggestions from profile
                optimized = query
                for suggestion in profile.optimization_suggestions:
                    if suggestion == "simplify":
                        optimized = self._simplify_query(optimized)
                    elif suggestion == "expand":
                        optimized = self._expand_query(optimized)

                return optimized

        return query

    def _extract_query_pattern(self, query: str) -> str:
        """Extract pattern from query for performance tracking."""
        words = query.lower().split()

        # Categorize by length and content
        if len(words) <= 2:
            return "short_query"
        elif len(words) >= 6:
            return "long_query"
        elif any(genre in query.lower() for genre in self.expansion_terms.keys()):
            return "genre_query"
        elif any(word in query.lower() for word in ["like", "similar", "recommend"]):
            return "recommendation_query"
        else:
            return "general_query"

    def update_performance_profile(
        self, query: str, latency: float, success_rate: float, result_count: int
    ) -> None:
        """Update performance profile based on query results."""
        pattern = self._extract_query_pattern(query)

        if pattern not in self.performance_profiles:
            self.performance_profiles[pattern] = PerformanceProfile(
                query_pattern=pattern,
                avg_latency=latency,
                success_rate=success_rate,
                typical_result_count=result_count,
            )
        else:
            profile = self.performance_profiles[pattern]
            # Update with exponential moving average
            alpha = 0.3  # Learning rate
            profile.avg_latency = alpha * latency + (1 - alpha) * profile.avg_latency
            profile.success_rate = (
                alpha * success_rate + (1 - alpha) * profile.success_rate
            )
            profile.typical_result_count = int(
                alpha * result_count + (1 - alpha) * profile.typical_result_count
            )

            # Update optimization suggestions
            profile.optimization_suggestions.clear()
            if profile.avg_latency > 0.5:
                profile.optimization_suggestions.append("simplify")
            if profile.success_rate < 0.8:
                profile.optimization_suggestions.append("expand")

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        if not self.optimization_history:
            return {"total_optimizations": 0}

        total = len(self.optimization_history)
        by_type = defaultdict(int)
        avg_improvement = 0.0

        for result in self.optimization_history:
            by_type[result.optimization_type] += 1
            avg_improvement += result.improvement_score

        avg_improvement /= total

        return {
            "total_optimizations": total,
            "avg_improvement_score": avg_improvement,
            "optimization_types": dict(by_type),
            "performance_profiles": len(self.performance_profiles),
        }


class ResultRankingOptimizer:
    """
    Optimize result ranking based on user interaction patterns and relevance feedback.

    Features:
    - Click-through rate optimization
    - Relevance feedback integration
    - Personalization signals
    - Diversity optimization
    """

    def __init__(self):
        """Initialize ranking optimizer."""
        self.interaction_history = defaultdict(list)
        self.relevance_signals = defaultdict(float)
        self.ranking_weights = {
            "semantic_similarity": 0.4,
            "popularity": 0.2,
            "freshness": 0.1,
            "diversity": 0.1,
            "personalization": 0.2,
        }

    def optimize_ranking(
        self, query: str, results: List[Dict], user_context: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Optimize result ranking based on learned patterns.

        Args:
            query: Search query
            results: Original search results
            user_context: User context and preferences

        Returns:
            List[Dict]: Re-ranked results
        """
        if not results:
            return results

        # Calculate optimization scores for each result
        optimized_results = []

        for i, result in enumerate(results):
            optimization_score = self._calculate_optimization_score(
                query, result, i, user_context
            )

            # Combine with original score
            original_score = result.get("scores", {}).get("final", 0.0)
            combined_score = 0.7 * original_score + 0.3 * optimization_score

            # Update result
            optimized_result = result.copy()
            optimized_result["scores"] = optimized_result.get("scores", {}).copy()
            optimized_result["scores"]["optimization"] = optimization_score
            optimized_result["scores"]["final"] = combined_score
            optimized_result["optimization_factors"] = self._get_optimization_factors(
                query, result, user_context
            )

            optimized_results.append(optimized_result)

        # Sort by optimized scores
        optimized_results.sort(key=lambda x: x["scores"]["final"], reverse=True)

        # Apply diversity constraint
        diversified_results = self._apply_diversity_constraint(optimized_results)

        return diversified_results

    def _calculate_optimization_score(
        self, query: str, result: Dict, position: int, user_context: Optional[Dict]
    ) -> float:
        """Calculate optimization score for a result."""
        score = 0.0

        # Popularity signal (based on historical interactions)
        movie_id = str(result.get("movie_id", ""))
        popularity_score = self.relevance_signals.get(movie_id, 0.0)
        score += self.ranking_weights["popularity"] * popularity_score

        # Position bias compensation (later results get slight boost)
        position_boost = 1.0 - (position * 0.05)  # Small boost for lower positions
        score += self.ranking_weights["diversity"] * position_boost

        # Query-specific relevance
        query_relevance = self._calculate_query_relevance(query, result)
        score += self.ranking_weights["semantic_similarity"] * query_relevance

        # Freshness signal (newer movies get slight boost)
        freshness_score = self._calculate_freshness_score(result)
        score += self.ranking_weights["freshness"] * freshness_score

        # Personalization (if user context available)
        if user_context:
            personalization_score = self._calculate_personalization_score(
                result, user_context
            )
            score += self.ranking_weights["personalization"] * personalization_score

        return min(score, 1.0)  # Cap at 1.0

    def _calculate_query_relevance(self, query: str, result: Dict) -> float:
        """Calculate query-specific relevance score."""
        query_terms = set(query.lower().split())

        # Check title relevance
        title = result.get("title", "").lower()
        title_terms = set(title.split())
        title_overlap = len(query_terms.intersection(title_terms))
        title_score = title_overlap / len(query_terms) if query_terms else 0.0

        # Check genre relevance
        genres = result.get("genres", [])
        if isinstance(genres, list):
            genre_terms = set([g.lower() for g in genres])
        else:
            genre_terms = set([genres.lower()]) if genres else set()

        genre_overlap = len(query_terms.intersection(genre_terms))
        genre_score = genre_overlap / len(query_terms) if query_terms else 0.0

        return 0.7 * title_score + 0.3 * genre_score

    def _calculate_freshness_score(self, result: Dict) -> float:
        """Calculate freshness score based on movie year."""
        year = result.get("year", 1900)
        current_year = datetime.now().year

        # Normalize year to 0-1 scale (last 50 years)
        year_diff = current_year - year
        if year_diff <= 5:
            return 1.0  # Very recent
        elif year_diff <= 20:
            return 0.8  # Recent
        elif year_diff <= 50:
            return 0.5  # Moderate
        else:
            return 0.2  # Classic

    def _calculate_personalization_score(
        self, result: Dict, user_context: Dict
    ) -> float:
        """Calculate personalization score based on user preferences."""
        score = 0.0

        # Genre preferences
        user_genres = set(user_context.get("preferred_genres", []))
        result_genres = set(result.get("genres", []))
        if user_genres and result_genres:
            genre_match = len(user_genres.intersection(result_genres)) / len(
                user_genres
            )
            score += 0.5 * genre_match

        # Year preferences
        preferred_years = user_context.get("preferred_year_range", [])
        if preferred_years:
            result_year = result.get("year", 0)
            if preferred_years[0] <= result_year <= preferred_years[1]:
                score += 0.3

        # Rating preferences
        min_rating = user_context.get("min_rating", 0.0)
        result_rating = result.get("rating", 0.0)
        if result_rating >= min_rating:
            score += 0.2

        return min(score, 1.0)

    def _apply_diversity_constraint(self, results: List[Dict]) -> List[Dict]:
        """Apply diversity constraint to avoid too many similar results."""
        if len(results) <= 3:
            return results

        diversified = []
        seen_genres = set()
        seen_years = set()

        # First pass: take top results that add diversity
        for result in results:
            genres = set(result.get("genres", []))
            year_decade = (result.get("year", 1900) // 10) * 10

            # Check if this adds diversity
            adds_genre_diversity = not genres.intersection(seen_genres)
            adds_year_diversity = year_decade not in seen_years

            if len(diversified) < 3 or adds_genre_diversity or adds_year_diversity:
                diversified.append(result)
                seen_genres.update(genres)
                seen_years.add(year_decade)

                if len(diversified) >= len(results):
                    break

        # Second pass: fill remaining slots with highest scoring results
        remaining_slots = len(results) - len(diversified)
        if remaining_slots > 0:
            remaining_results = [r for r in results if r not in diversified]
            diversified.extend(remaining_results[:remaining_slots])

        return diversified

    def _get_optimization_factors(
        self, query: str, result: Dict, user_context: Optional[Dict]
    ) -> Dict[str, float]:
        """Get detailed optimization factors for transparency."""
        return {
            "query_relevance": self._calculate_query_relevance(query, result),
            "popularity": self.relevance_signals.get(
                str(result.get("movie_id", "")), 0.0
            ),
            "freshness": self._calculate_freshness_score(result),
            "personalization": (
                self._calculate_personalization_score(result, user_context)
                if user_context
                else 0.0
            ),
        }

    def record_interaction(
        self, query: str, result: Dict, interaction_type: str
    ) -> None:
        """Record user interaction for learning."""
        movie_id = str(result.get("movie_id", ""))
        timestamp = time.time()

        # Record interaction
        self.interaction_history[movie_id].append(
            {
                "query": query,
                "interaction_type": interaction_type,  # 'click', 'view', 'like', etc.
                "timestamp": timestamp,
            }
        )

        # Update relevance signals
        interaction_weights = {
            "click": 0.1,
            "view": 0.2,
            "like": 0.5,
            "share": 0.3,
            "bookmark": 0.4,
        }

        weight = interaction_weights.get(interaction_type, 0.1)
        self.relevance_signals[movie_id] = min(
            self.relevance_signals[movie_id] + weight, 1.0
        )

    def get_ranking_stats(self) -> Dict[str, Any]:
        """Get ranking optimization statistics."""
        total_interactions = sum(
            len(interactions) for interactions in self.interaction_history.values()
        )

        return {
            "total_interactions": total_interactions,
            "movies_with_signals": len(self.relevance_signals),
            "ranking_weights": self.ranking_weights,
            "avg_relevance_signal": (
                np.mean(list(self.relevance_signals.values()))
                if self.relevance_signals
                else 0.0
            ),
        }


# Global instances
_query_optimizer = None
_ranking_optimizer = None


def get_query_optimizer() -> QueryOptimizer:
    """Get global query optimizer instance."""
    global _query_optimizer
    if _query_optimizer is None:
        _query_optimizer = QueryOptimizer()
    return _query_optimizer


def get_ranking_optimizer() -> ResultRankingOptimizer:
    """Get global ranking optimizer instance."""
    global _ranking_optimizer
    if _ranking_optimizer is None:
        _ranking_optimizer = ResultRankingOptimizer()
    return _ranking_optimizer


# Convenience functions
def optimize_query(query: str, context: Optional[Dict] = None) -> str:
    """Optimize a query for better performance."""
    result = get_query_optimizer().optimize_query(query, context)
    return result.optimized_query


def optimize_results(
    query: str, results: List[Dict], user_context: Optional[Dict] = None
) -> List[Dict]:
    """Optimize result ranking."""
    return get_ranking_optimizer().optimize_ranking(query, results, user_context)


def record_user_interaction(query: str, result: Dict, interaction_type: str) -> None:
    """Record user interaction for learning."""
    get_ranking_optimizer().record_interaction(query, result, interaction_type)
