"""
Quality Metrics

Evaluates retrieval quality including relevance scoring, precision@k, recall@k,
NDCG, and other information retrieval metrics.
"""

import logging
import math
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict
import numpy as np
from dataclasses import dataclass, field

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class RelevanceJudgment:
    """Single relevance judgment for a query-document pair."""

    query: str
    document_id: str
    relevance_score: float  # 0.0 (not relevant) to 1.0 (highly relevant)
    judgment_source: str = "manual"  # manual, automatic, implicit
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """Single search result with metadata."""

    document_id: str
    title: str
    score: float
    rank: int
    content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Results of quality evaluation."""

    query: str
    precision_at_k: Dict[int, float]
    recall_at_k: Dict[int, float]
    ndcg_at_k: Dict[int, float]
    map_score: float  # Mean Average Precision
    mrr_score: float  # Mean Reciprocal Rank
    total_relevant: int
    results_analyzed: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class QualityEvaluator:
    """
    Comprehensive quality evaluation system for retrieval results.

    Implements standard IR metrics including precision@k, recall@k, NDCG, MAP, MRR
    and provides tools for relevance judgment collection and analysis.
    """

    def __init__(self):
        """Initialize quality evaluator."""
        self.relevance_judgments = {}  # query -> {doc_id: relevance_score}
        self.evaluation_cache = {}  # query -> EvaluationResult

        # Default evaluation parameters
        self.k_values = [1, 3, 5, 10, 20]  # Standard k values for evaluation
        self.relevance_threshold = 0.5  # Threshold for binary relevance

        # Automatic relevance scoring weights
        self.auto_relevance_weights = {
            "semantic_similarity": 0.4,
            "title_match": 0.3,
            "keyword_match": 0.2,
            "metadata_match": 0.1,
        }

    def add_relevance_judgment(
        self,
        query: str,
        document_id: str,
        relevance_score: float,
        source: str = "manual",
    ) -> None:
        """Add a relevance judgment."""
        if query not in self.relevance_judgments:
            self.relevance_judgments[query] = {}

        self.relevance_judgments[query][document_id] = relevance_score

        # Clear cache for this query
        if query in self.evaluation_cache:
            del self.evaluation_cache[query]

    def add_relevance_judgments_batch(self, judgments: List[RelevanceJudgment]) -> None:
        """Add multiple relevance judgments."""
        for judgment in judgments:
            self.add_relevance_judgment(
                judgment.query,
                judgment.document_id,
                judgment.relevance_score,
                judgment.judgment_source,
            )

    def evaluate_search_results(
        self, query: str, results: List[SearchResult], use_cache: bool = True
    ) -> EvaluationResult:
        """
        Evaluate search results for a query.

        Args:
            query: Search query
            results: List of search results
            use_cache: Whether to use cached evaluation results

        Returns:
            EvaluationResult: Comprehensive evaluation metrics
        """
        # Check cache
        if use_cache and query in self.evaluation_cache:
            return self.evaluation_cache[query]

        # Get relevance judgments for this query
        judgments = self.relevance_judgments.get(query, {})

        if not judgments:
            logger.warning(
                f"No relevance judgments found for query: '{query}'. Using automatic scoring."
            )
            judgments = self._generate_automatic_relevance_scores(query, results)

        # Calculate metrics
        precision_at_k = self._calculate_precision_at_k(results, judgments)
        recall_at_k = self._calculate_recall_at_k(results, judgments)
        ndcg_at_k = self._calculate_ndcg_at_k(results, judgments)
        map_score = self._calculate_map(results, judgments)
        mrr_score = self._calculate_mrr(results, judgments)

        # Count relevant documents
        total_relevant = sum(
            1 for score in judgments.values() if score >= self.relevance_threshold
        )

        evaluation_result = EvaluationResult(
            query=query,
            precision_at_k=precision_at_k,
            recall_at_k=recall_at_k,
            ndcg_at_k=ndcg_at_k,
            map_score=map_score,
            mrr_score=mrr_score,
            total_relevant=total_relevant,
            results_analyzed=len(results),
            metadata={
                "has_manual_judgments": query in self.relevance_judgments,
                "judgment_count": len(judgments),
                "relevance_threshold": self.relevance_threshold,
            },
        )

        # Cache result
        if use_cache:
            self.evaluation_cache[query] = evaluation_result

        return evaluation_result

    def evaluate_query_set(
        self, query_results: Dict[str, List[SearchResult]]
    ) -> Dict[str, Any]:
        """
        Evaluate multiple queries and return aggregate metrics.

        Args:
            query_results: Dict mapping queries to their search results

        Returns:
            dict: Aggregate evaluation metrics
        """
        individual_results = {}

        # Evaluate each query
        for query, results in query_results.items():
            individual_results[query] = self.evaluate_search_results(query, results)

        # Calculate aggregate metrics
        aggregate_metrics = self._calculate_aggregate_metrics(individual_results)

        return {
            "individual_results": individual_results,
            "aggregate_metrics": aggregate_metrics,
            "evaluation_summary": {
                "total_queries": len(query_results),
                "queries_with_judgments": len(
                    [q for q in query_results.keys() if q in self.relevance_judgments]
                ),
                "avg_results_per_query": np.mean(
                    [len(results) for results in query_results.values()]
                ),
            },
        }

    def _calculate_precision_at_k(
        self, results: List[SearchResult], judgments: Dict[str, float]
    ) -> Dict[int, float]:
        """Calculate precision@k for different k values."""
        precision_scores = {}

        for k in self.k_values:
            if k > len(results):
                precision_scores[k] = 0.0
                continue

            relevant_count = 0
            for i in range(min(k, len(results))):
                doc_id = results[i].document_id
                if judgments.get(doc_id, 0.0) >= self.relevance_threshold:
                    relevant_count += 1

            precision_scores[k] = relevant_count / k if k > 0 else 0.0

        return precision_scores

    def _calculate_recall_at_k(
        self, results: List[SearchResult], judgments: Dict[str, float]
    ) -> Dict[int, float]:
        """Calculate recall@k for different k values."""
        recall_scores = {}

        # Count total relevant documents
        total_relevant = sum(
            1 for score in judgments.values() if score >= self.relevance_threshold
        )

        if total_relevant == 0:
            return {k: 0.0 for k in self.k_values}

        for k in self.k_values:
            relevant_found = 0
            for i in range(min(k, len(results))):
                doc_id = results[i].document_id
                if judgments.get(doc_id, 0.0) >= self.relevance_threshold:
                    relevant_found += 1

            recall_scores[k] = relevant_found / total_relevant

        return recall_scores

    def _calculate_ndcg_at_k(
        self, results: List[SearchResult], judgments: Dict[str, float]
    ) -> Dict[int, float]:
        """Calculate NDCG@k (Normalized Discounted Cumulative Gain)."""
        ndcg_scores = {}

        for k in self.k_values:
            if k > len(results):
                ndcg_scores[k] = 0.0
                continue

            # Calculate DCG@k
            dcg = 0.0
            for i in range(min(k, len(results))):
                doc_id = results[i].document_id
                relevance = judgments.get(doc_id, 0.0)
                if i == 0:
                    dcg += relevance
                else:
                    dcg += relevance / math.log2(i + 1)

            # Calculate IDCG@k (ideal DCG)
            ideal_relevances = sorted(judgments.values(), reverse=True)
            idcg = 0.0
            for i in range(min(k, len(ideal_relevances))):
                relevance = ideal_relevances[i]
                if i == 0:
                    idcg += relevance
                else:
                    idcg += relevance / math.log2(i + 1)

            # Calculate NDCG
            ndcg_scores[k] = dcg / idcg if idcg > 0 else 0.0

        return ndcg_scores

    def _calculate_map(
        self, results: List[SearchResult], judgments: Dict[str, float]
    ) -> float:
        """Calculate Mean Average Precision (MAP)."""
        if not results:
            return 0.0

        precision_sum = 0.0
        relevant_count = 0

        for i, result in enumerate(results):
            doc_id = result.document_id
            if judgments.get(doc_id, 0.0) >= self.relevance_threshold:
                relevant_count += 1
                # Calculate precision at this position
                precision_at_i = relevant_count / (i + 1)
                precision_sum += precision_at_i

        # Calculate total relevant documents
        total_relevant = sum(
            1 for score in judgments.values() if score >= self.relevance_threshold
        )

        return precision_sum / total_relevant if total_relevant > 0 else 0.0

    def _calculate_mrr(
        self, results: List[SearchResult], judgments: Dict[str, float]
    ) -> float:
        """Calculate Mean Reciprocal Rank (MRR)."""
        for i, result in enumerate(results):
            doc_id = result.document_id
            if judgments.get(doc_id, 0.0) >= self.relevance_threshold:
                return 1.0 / (i + 1)

        return 0.0  # No relevant documents found

    def _generate_automatic_relevance_scores(
        self, query: str, results: List[SearchResult]
    ) -> Dict[str, float]:
        """Generate automatic relevance scores based on search features."""
        auto_judgments = {}

        query_words = set(query.lower().split())

        for result in results:
            relevance_score = 0.0

            # Semantic similarity (use search score as proxy)
            if hasattr(result, "score") and result.score:
                semantic_score = min(result.score, 1.0)  # Normalize to 0-1
                relevance_score += (
                    semantic_score * self.auto_relevance_weights["semantic_similarity"]
                )

            # Title match
            if result.title:
                title_words = set(result.title.lower().split())
                title_overlap = len(query_words.intersection(title_words))
                title_score = (
                    min(title_overlap / len(query_words), 1.0) if query_words else 0.0
                )
                relevance_score += (
                    title_score * self.auto_relevance_weights["title_match"]
                )

            # Content match (if available)
            if result.content:
                content_words = set(result.content.lower().split())
                content_overlap = len(query_words.intersection(content_words))
                content_score = (
                    min(content_overlap / len(query_words), 1.0) if query_words else 0.0
                )
                relevance_score += (
                    content_score * self.auto_relevance_weights["keyword_match"]
                )

            # Metadata match (genre, year, etc.)
            metadata_score = self._calculate_metadata_relevance(query, result.metadata)
            relevance_score += (
                metadata_score * self.auto_relevance_weights["metadata_match"]
            )

            auto_judgments[result.document_id] = min(relevance_score, 1.0)

        return auto_judgments

    def _calculate_metadata_relevance(
        self, query: str, metadata: Dict[str, Any]
    ) -> float:
        """Calculate relevance score based on metadata matching."""
        query_lower = query.lower()
        relevance_score = 0.0

        # Genre matching
        if "genres" in metadata:
            genres = metadata["genres"]
            if isinstance(genres, list):
                for genre in genres:
                    if genre.lower() in query_lower:
                        relevance_score += 0.3
            elif isinstance(genres, str) and genres.lower() in query_lower:
                relevance_score += 0.3

        # Year matching (if query contains year)
        if "year" in metadata:
            year_str = str(metadata["year"])
            if year_str in query:
                relevance_score += 0.2

        # Director/actor matching (if available)
        for field in ["director", "actors", "cast"]:
            if field in metadata:
                field_value = str(metadata[field]).lower()
                if any(word in field_value for word in query_lower.split()):
                    relevance_score += 0.1

        return min(relevance_score, 1.0)

    def _calculate_aggregate_metrics(
        self, individual_results: Dict[str, EvaluationResult]
    ) -> Dict[str, Any]:
        """Calculate aggregate metrics across all queries."""
        if not individual_results:
            return {}

        # Collect all metrics
        all_precision = defaultdict(list)
        all_recall = defaultdict(list)
        all_ndcg = defaultdict(list)
        all_map = []
        all_mrr = []

        for result in individual_results.values():
            for k, score in result.precision_at_k.items():
                all_precision[k].append(score)
            for k, score in result.recall_at_k.items():
                all_recall[k].append(score)
            for k, score in result.ndcg_at_k.items():
                all_ndcg[k].append(score)
            all_map.append(result.map_score)
            all_mrr.append(result.mrr_score)

        # Calculate averages
        avg_precision = {k: np.mean(scores) for k, scores in all_precision.items()}
        avg_recall = {k: np.mean(scores) for k, scores in all_recall.items()}
        avg_ndcg = {k: np.mean(scores) for k, scores in all_ndcg.items()}
        avg_map = np.mean(all_map)
        avg_mrr = np.mean(all_mrr)

        return {
            "precision_at_k": avg_precision,
            "recall_at_k": avg_recall,
            "ndcg_at_k": avg_ndcg,
            "map": avg_map,
            "mrr": avg_mrr,
            "query_count": len(individual_results),
        }

    def generate_evaluation_report(
        self, evaluation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a comprehensive evaluation report."""
        aggregate = evaluation_results.get("aggregate_metrics", {})
        individual = evaluation_results.get("individual_results", {})
        summary = evaluation_results.get("evaluation_summary", {})

        # Performance assessment
        avg_ndcg_5 = aggregate.get("ndcg_at_k", {}).get(5, 0.0)
        avg_precision_5 = aggregate.get("precision_at_k", {}).get(5, 0.0)
        avg_map = aggregate.get("map", 0.0)

        # Grade assignment
        if avg_ndcg_5 >= 0.8 and avg_precision_5 >= 0.7:
            grade = "A"
        elif avg_ndcg_5 >= 0.6 and avg_precision_5 >= 0.5:
            grade = "B"
        elif avg_ndcg_5 >= 0.4 and avg_precision_5 >= 0.3:
            grade = "C"
        else:
            grade = "D"

        # Top performing queries
        top_queries = sorted(
            individual.items(), key=lambda x: x[1].ndcg_at_k.get(5, 0.0), reverse=True
        )[:3]

        # Worst performing queries
        worst_queries = sorted(
            individual.items(), key=lambda x: x[1].ndcg_at_k.get(5, 0.0)
        )[:3]

        return {
            "overall_grade": grade,
            "key_metrics": {
                "avg_ndcg_at_5": avg_ndcg_5,
                "avg_precision_at_5": avg_precision_5,
                "avg_map": avg_map,
                "avg_mrr": aggregate.get("mrr", 0.0),
            },
            "performance_analysis": {
                "total_queries_evaluated": summary.get("total_queries", 0),
                "queries_with_manual_judgments": summary.get(
                    "queries_with_judgments", 0
                ),
                "avg_results_per_query": summary.get("avg_results_per_query", 0),
            },
            "top_performing_queries": [
                {
                    "query": query,
                    "ndcg_at_5": result.ndcg_at_k.get(5, 0.0),
                    "precision_at_5": result.precision_at_k.get(5, 0.0),
                }
                for query, result in top_queries
            ],
            "improvement_opportunities": [
                {
                    "query": query,
                    "ndcg_at_5": result.ndcg_at_k.get(5, 0.0),
                    "precision_at_5": result.precision_at_k.get(5, 0.0),
                    "suggestions": self._generate_improvement_suggestions(
                        query, result
                    ),
                }
                for query, result in worst_queries
            ],
            "recommendations": self._generate_recommendations(aggregate),
        }

    def _generate_improvement_suggestions(
        self, query: str, result: EvaluationResult
    ) -> List[str]:
        """Generate improvement suggestions for poorly performing queries."""
        suggestions = []

        if result.precision_at_k.get(5, 0.0) < 0.3:
            suggestions.append(
                "Low precision suggests irrelevant results - improve query understanding"
            )

        if result.recall_at_k.get(10, 0.0) < 0.5:
            suggestions.append(
                "Low recall suggests missing relevant documents - expand retrieval coverage"
            )

        if result.ndcg_at_k.get(5, 0.0) < 0.4:
            suggestions.append(
                "Low NDCG indicates poor ranking - improve result ordering"
            )

        if result.total_relevant == 0:
            suggestions.append(
                "No relevant documents found - check query processing and indexing"
            )

        return suggestions

    def _generate_recommendations(self, aggregate_metrics: Dict[str, Any]) -> List[str]:
        """Generate system-wide recommendations based on aggregate metrics."""
        recommendations = []

        avg_precision_5 = aggregate_metrics.get("precision_at_k", {}).get(5, 0.0)
        avg_recall_5 = aggregate_metrics.get("recall_at_k", {}).get(5, 0.0)
        avg_map = aggregate_metrics.get("map", 0.0)

        if avg_precision_5 < 0.5:
            recommendations.append(
                "Focus on improving result relevance through better query processing and ranking"
            )

        if avg_recall_5 < 0.6:
            recommendations.append(
                "Expand retrieval coverage to capture more relevant documents"
            )

        if avg_map < 0.4:
            recommendations.append(
                "Improve overall ranking quality through enhanced scoring algorithms"
            )

        return recommendations


# Global instance
quality_evaluator = QualityEvaluator()


def get_quality_evaluator() -> QualityEvaluator:
    """Get global quality evaluator instance."""
    return quality_evaluator


# Convenience functions
def evaluate_search_quality(
    query: str, results: List[Dict[str, Any]]
) -> EvaluationResult:
    """
    Evaluate search quality for a single query.

    Args:
        query: Search query
        results: List of search results (dict format)

    Returns:
        EvaluationResult: Quality evaluation metrics
    """
    # Convert results to SearchResult objects
    search_results = []
    for i, result in enumerate(results):
        search_result = SearchResult(
            document_id=str(result.get("movie_id", result.get("id", i))),
            title=result.get("title", "Unknown"),
            score=result.get("scores", {}).get("final", result.get("score", 0.0)),
            rank=i + 1,
            content=result.get("overview", ""),
            metadata=result.get("metadata", {}),
        )
        search_results.append(search_result)

    return quality_evaluator.evaluate_search_results(query, search_results)


def add_manual_relevance_judgments(
    query: str, relevance_data: Dict[str, float]
) -> None:
    """
    Add manual relevance judgments for a query.

    Args:
        query: Search query
        relevance_data: Dict mapping document IDs to relevance scores (0.0-1.0)
    """
    for doc_id, relevance_score in relevance_data.items():
        quality_evaluator.add_relevance_judgment(
            query, doc_id, relevance_score, "manual"
        )
