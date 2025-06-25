"""
Result Ranking & Re-ranking

Advanced algorithms for ranking and re-ranking search results
using multiple signals and machine learning techniques.
"""

import logging
import math
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from collections import defaultdict
import datetime

# Configure logging
logger = logging.getLogger(__name__)


class ResultRanker:
    """
    Advanced result ranking engine with multiple ranking strategies.

    Supports various ranking algorithms including:
    - BM25-style scoring
    - Learning-to-Rank signals
    - Diversity optimization
    - Temporal relevance
    - User preference modeling
    """

    def __init__(self):
        """Initialize the result ranker."""
        # Ranking configuration
        self.config = {
            "diversity_threshold": 0.8,  # Similarity threshold for diversity
            "temporal_decay": 0.1,  # Decay factor for old movies
            "popularity_weight": 0.15,  # Weight for popularity signals
            "freshness_weight": 0.1,  # Weight for recent content
            "quality_weight": 0.2,  # Weight for quality indicators
            "personalization_weight": 0.0,  # Weight for personalization (future)
        }

        # Feature weights for learning-to-rank style scoring
        self.feature_weights = {
            "semantic_similarity": 1.0,
            "title_match": 2.0,
            "genre_match": 1.5,
            "year_relevance": 1.2,
            "popularity_score": 1.1,
            "rating_score": 1.3,
            "diversity_bonus": 0.8,
            "freshness_bonus": 0.9,
        }

        # Genre preferences (could be personalized in future)
        self.genre_preferences = defaultdict(float)

    def rank_results(
        self,
        results: List[Dict],
        query_info: Dict,
        ranking_strategy: str = "hybrid",
        user_preferences: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Rank results using specified strategy.

        Args:
            results: List of search results to rank
            query_info: Information about the original query
            ranking_strategy: 'semantic', 'popularity', 'hybrid', 'diversity'
            user_preferences: Optional user preference data

        Returns:
            list: Ranked results with ranking metadata
        """
        if not results:
            return results

        logger.info(
            f"Ranking {len(results)} results using strategy: {ranking_strategy}"
        )

        try:
            # Apply ranking strategy
            if ranking_strategy == "semantic":
                ranked_results = self._semantic_ranking(results, query_info)
            elif ranking_strategy == "popularity":
                ranked_results = self._popularity_ranking(results, query_info)
            elif ranking_strategy == "diversity":
                ranked_results = self._diversity_ranking(results, query_info)
            elif ranking_strategy == "temporal":
                ranked_results = self._temporal_ranking(results, query_info)
            else:  # hybrid
                ranked_results = self._hybrid_ranking(
                    results, query_info, user_preferences
                )

            # Add ranking metadata
            for i, result in enumerate(ranked_results):
                result["ranking_info"] = {
                    "rank": i + 1,
                    "strategy": ranking_strategy,
                    "ranking_score": result.get("final_score", 0.0),
                    "features": self._extract_ranking_features(result, query_info),
                }

            logger.info(
                f"Ranking completed. Top result: {ranked_results[0].get('title', 'Unknown')}"
            )
            return ranked_results

        except Exception as e:
            logger.error(f"Ranking failed: {str(e)}")
            # Return original results if ranking fails
            return results

    def _semantic_ranking(self, results: List[Dict], query_info: Dict) -> List[Dict]:
        """Rank purely based on semantic similarity."""
        return sorted(
            results,
            key=lambda x: x.get("scores", {}).get("semantic", 0.0),
            reverse=True,
        )

    def _popularity_ranking(self, results: List[Dict], query_info: Dict) -> List[Dict]:
        """Rank based on popularity and ratings."""

        def popularity_score(result):
            payload = result.get("payload", {})
            popularity = payload.get("popularity", 0)
            vote_average = payload.get("vote_average", 0)
            vote_count = payload.get("vote_count", 0)

            # Combine popularity, rating, and vote count
            pop_score = min(popularity / 100.0, 1.0)  # Normalize popularity
            rating_score = vote_average / 10.0  # Normalize rating
            count_score = min(
                math.log(vote_count + 1) / 10.0, 1.0
            )  # Log scale vote count

            return (pop_score + rating_score + count_score) / 3.0

        return sorted(results, key=popularity_score, reverse=True)

    def _diversity_ranking(self, results: List[Dict], query_info: Dict) -> List[Dict]:
        """Rank to maximize diversity while maintaining relevance."""
        if len(results) <= 1:
            return results

        # Start with highest scoring result
        ranked_results = [max(results, key=lambda x: x.get("final_score", 0.0))]
        remaining_results = [r for r in results if r != ranked_results[0]]

        # Iteratively add most diverse results
        while remaining_results and len(ranked_results) < len(results):
            best_result = None
            best_diversity_score = -1

            for candidate in remaining_results:
                # Calculate diversity score against already selected results
                diversity_score = self._calculate_diversity_score(
                    candidate, ranked_results
                )
                relevance_score = candidate.get("final_score", 0.0)

                # Combine diversity and relevance
                combined_score = 0.6 * relevance_score + 0.4 * diversity_score

                if combined_score > best_diversity_score:
                    best_diversity_score = combined_score
                    best_result = candidate

            if best_result:
                ranked_results.append(best_result)
                remaining_results.remove(best_result)

        return ranked_results

    def _temporal_ranking(self, results: List[Dict], query_info: Dict) -> List[Dict]:
        """Rank with temporal relevance consideration."""
        current_year = datetime.datetime.now().year

        def temporal_score(result):
            year = result.get("year", current_year)
            age = current_year - year

            # Apply temporal decay
            temporal_factor = math.exp(-self.config["temporal_decay"] * age / 10.0)

            # Boost for classic movies (> 30 years old)
            if age > 30:
                temporal_factor *= 1.2

            # Combine with original score
            original_score = result.get("final_score", 0.0)
            return original_score * temporal_factor

        return sorted(results, key=temporal_score, reverse=True)

    def _hybrid_ranking(
        self,
        results: List[Dict],
        query_info: Dict,
        user_preferences: Optional[Dict] = None,
    ) -> List[Dict]:
        """Advanced hybrid ranking using multiple signals."""

        # Calculate comprehensive scores for each result
        for result in results:
            features = self._extract_ranking_features(result, query_info)
            hybrid_score = self._calculate_hybrid_score(features, user_preferences)
            result["hybrid_score"] = hybrid_score

        # Sort by hybrid score
        ranked_results = sorted(
            results, key=lambda x: x.get("hybrid_score", 0.0), reverse=True
        )

        # Apply diversity post-processing
        return self._apply_diversity_filter(ranked_results)

    def _extract_ranking_features(
        self, result: Dict, query_info: Dict
    ) -> Dict[str, float]:
        """Extract ranking features from a result."""
        features = {}
        payload = result.get("payload", {})
        scores = result.get("scores", {})

        # Semantic similarity features
        features["semantic_similarity"] = scores.get("semantic", 0.0)
        features["keyword_match"] = scores.get("keyword", 0.0)
        features["metadata_match"] = scores.get("metadata", 0.0)

        # Content features
        features["title_match"] = self._calculate_title_match(result, query_info)
        features["genre_match"] = self._calculate_genre_match(result, query_info)

        # Quality features
        features["popularity_score"] = min(payload.get("popularity", 0) / 100.0, 1.0)
        features["rating_score"] = payload.get("vote_average", 0) / 10.0
        features["vote_count_score"] = min(
            math.log(payload.get("vote_count", 1)) / 10.0, 1.0
        )

        # Temporal features
        features["year_relevance"] = self._calculate_year_relevance(result)
        features["freshness_bonus"] = self._calculate_freshness_bonus(result)

        # Diversity features (calculated later in ranking)
        features["diversity_bonus"] = 0.0

        return features

    def _calculate_title_match(self, result: Dict, query_info: Dict) -> float:
        """Calculate how well the title matches the query."""
        title = result.get("title", "").lower()
        query_text = query_info.get("text", "").lower()

        if not title or not query_text:
            return 0.0

        # Simple word overlap score
        title_words = set(title.split())
        query_words = set(query_text.split())

        if not query_words:
            return 0.0

        overlap = len(title_words.intersection(query_words))
        return overlap / len(query_words)

    def _calculate_genre_match(self, result: Dict, query_info: Dict) -> float:
        """Calculate genre matching score."""
        genres = result.get("genres", [])
        query_text = query_info.get("text", "").lower()

        if not genres or not query_text:
            return 0.0

        genre_matches = 0
        for genre in genres:
            if genre.lower() in query_text:
                genre_matches += 1

        return min(genre_matches / len(genres), 1.0)

    def _calculate_year_relevance(self, result: Dict) -> float:
        """Calculate year relevance score."""
        year = result.get("year")
        if not year:
            return 0.5  # Neutral score for unknown year

        current_year = datetime.datetime.now().year
        age = current_year - year

        # Peak relevance for movies 2-10 years old
        if 2 <= age <= 10:
            return 1.0
        elif age <= 1:
            return 0.8  # Very new movies
        elif age <= 30:
            return 0.7  # Modern movies
        else:
            return 0.9  # Classic movies get a boost

    def _calculate_freshness_bonus(self, result: Dict) -> float:
        """Calculate freshness bonus for recent content."""
        year = result.get("year")
        if not year:
            return 0.0

        current_year = datetime.datetime.now().year
        age = current_year - year

        # Bonus for very recent movies
        if age <= 2:
            return 0.2
        elif age <= 5:
            return 0.1
        else:
            return 0.0

    def _calculate_hybrid_score(
        self, features: Dict[str, float], user_preferences: Optional[Dict] = None
    ) -> float:
        """Calculate final hybrid ranking score."""
        score = 0.0

        # Apply feature weights
        for feature_name, feature_value in features.items():
            weight = self.feature_weights.get(feature_name, 1.0)
            score += feature_value * weight

        # Apply user preferences if available
        if user_preferences:
            preference_boost = self._calculate_preference_boost(
                features, user_preferences
            )
            score += preference_boost * self.config["personalization_weight"]

        return score

    def _calculate_preference_boost(
        self, features: Dict[str, float], user_preferences: Dict
    ) -> float:
        """Calculate personalization boost based on user preferences."""
        # This is a placeholder for future personalization features
        # Could include preferred genres, time periods, etc.
        return 0.0

    def _calculate_diversity_score(
        self, candidate: Dict, selected_results: List[Dict]
    ) -> float:
        """Calculate diversity score for a candidate against selected results."""
        if not selected_results:
            return 1.0

        candidate_genres = set(candidate.get("genres", []))
        candidate_year = candidate.get("year", 0)

        diversity_score = 0.0

        for selected in selected_results:
            selected_genres = set(selected.get("genres", []))
            selected_year = selected.get("year", 0)

            # Genre diversity
            genre_overlap = len(candidate_genres.intersection(selected_genres))
            genre_diversity = 1.0 - (genre_overlap / max(len(candidate_genres), 1))

            # Year diversity
            year_diff = (
                abs(candidate_year - selected_year)
                if candidate_year and selected_year
                else 10
            )
            year_diversity = min(year_diff / 20.0, 1.0)  # Normalize to 0-1

            # Combined diversity for this pair
            pair_diversity = (genre_diversity + year_diversity) / 2.0
            diversity_score += pair_diversity

        # Average diversity across all selected results
        return diversity_score / len(selected_results)

    def _apply_diversity_filter(self, ranked_results: List[Dict]) -> List[Dict]:
        """Apply diversity filtering to reduce similar results."""
        if len(ranked_results) <= 1:
            return ranked_results

        filtered_results = [ranked_results[0]]  # Always keep top result

        for candidate in ranked_results[1:]:
            # Check diversity against already selected results
            diversity_score = self._calculate_diversity_score(
                candidate, filtered_results
            )

            # Only add if sufficiently diverse OR very high scoring
            high_score_threshold = filtered_results[0].get("hybrid_score", 0) * 0.9

            if (
                diversity_score >= self.config["diversity_threshold"]
                or candidate.get("hybrid_score", 0) >= high_score_threshold
            ):
                filtered_results.append(candidate)

            # Update diversity bonus feature for selected results
            candidate_features = candidate.get("ranking_info", {}).get("features", {})
            candidate_features["diversity_bonus"] = diversity_score

        return filtered_results

    def get_ranking_explanation(self, result: Dict) -> Dict[str, Any]:
        """Get explanation of why a result was ranked at its position."""
        ranking_info = result.get("ranking_info", {})
        features = ranking_info.get("features", {})

        # Identify top contributing features
        feature_contributions = []
        for feature, value in features.items():
            weight = self.feature_weights.get(feature, 1.0)
            contribution = value * weight
            feature_contributions.append(
                {
                    "feature": feature,
                    "value": value,
                    "weight": weight,
                    "contribution": contribution,
                }
            )

        # Sort by contribution
        feature_contributions.sort(key=lambda x: x["contribution"], reverse=True)

        return {
            "rank": ranking_info.get("rank", 0),
            "final_score": ranking_info.get("ranking_score", 0.0),
            "strategy": ranking_info.get("strategy", "unknown"),
            "top_features": feature_contributions[:5],
            "explanation": self._generate_explanation_text(feature_contributions[:3]),
        }

    def _generate_explanation_text(self, top_features: List[Dict]) -> str:
        """Generate human-readable explanation text."""
        if not top_features:
            return "Ranked based on overall relevance."

        explanations = []
        for feature in top_features:
            name = feature["feature"]
            value = feature["value"]

            if name == "semantic_similarity" and value > 0.7:
                explanations.append("high semantic relevance")
            elif name == "title_match" and value > 0.5:
                explanations.append("strong title match")
            elif name == "genre_match" and value > 0.5:
                explanations.append("matching genre")
            elif name == "popularity_score" and value > 0.7:
                explanations.append("high popularity")
            elif name == "rating_score" and value > 0.7:
                explanations.append("excellent ratings")

        if explanations:
            return f"Ranked highly due to: {', '.join(explanations)}"
        else:
            return "Ranked based on overall relevance."

    def update_config(self, new_config: Dict) -> bool:
        """Update ranking configuration."""
        try:
            for key, value in new_config.items():
                if key in self.config:
                    self.config[key] = value
                    logger.info(f"Updated ranking config: {key} = {value}")
                elif key in self.feature_weights:
                    self.feature_weights[key] = value
                    logger.info(f"Updated feature weight: {key} = {value}")
                else:
                    logger.warning(f"Invalid config key ignored: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to update ranking config: {str(e)}")
            return False


# Global instance for easy access
result_ranker = None


def get_result_ranker() -> ResultRanker:
    """
    Get or create global result ranker instance.

    Returns:
        ResultRanker: Global ranker instance
    """
    global result_ranker

    if result_ranker is None:
        result_ranker = ResultRanker()

    return result_ranker


# Convenience functions
def rank_search_results(
    results: List[Dict], query_info: Dict, strategy: str = "hybrid"
) -> List[Dict]:
    """
    Rank search results using global ranker instance.

    Args:
        results: Search results to rank
        query_info: Query information
        strategy: Ranking strategy

    Returns:
        list: Ranked results
    """
    ranker = get_result_ranker()
    return ranker.rank_results(results, query_info, strategy)


def explain_ranking(result: Dict) -> Dict[str, Any]:
    """
    Get ranking explanation for a result.

    Args:
        result: Search result with ranking info

    Returns:
        dict: Ranking explanation
    """
    ranker = get_result_ranker()
    return ranker.get_ranking_explanation(result)
