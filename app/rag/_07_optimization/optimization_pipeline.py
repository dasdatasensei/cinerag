"""
Optimization Pipeline

Main optimization pipeline that integrates caching, query optimization,
and result ranking to provide comprehensive RAG system optimization.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime

from .cache_manager import get_cache_manager, get_cache_statistics
from .performance_optimizer import (
    get_query_optimizer,
    get_ranking_optimizer,
    optimize_query,
    optimize_results,
    record_user_interaction,
)

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class OptimizationMetrics:
    """Metrics for optimization performance."""

    cache_hit_rate: float
    query_optimization_rate: float
    avg_performance_improvement: float
    total_optimizations: int
    response_time_improvement: float = 0.0


@dataclass
class SearchSession:
    """Track a search session for optimization."""

    session_id: str
    original_query: str
    optimized_query: str
    cache_hit: bool
    response_time: float
    result_count: int
    optimization_applied: bool
    user_interactions: List[Dict] = field(default_factory=list)


class OptimizationPipeline:
    """
    Comprehensive optimization pipeline for RAG system.

    Features:
    - Intelligent caching with multi-tier architecture
    - Query optimization and rewriting
    - Result ranking optimization
    - Performance monitoring and adaptation
    - User interaction learning
    """

    def __init__(self, enable_optimization: bool = True):
        """
        Initialize optimization pipeline.

        Args:
            enable_optimization: Whether to enable optimization features
        """
        self.enable_optimization = enable_optimization
        self.cache_manager = get_cache_manager()
        self.query_optimizer = get_query_optimizer()
        self.ranking_optimizer = get_ranking_optimizer()

        # Session tracking
        self.active_sessions = {}
        self.session_counter = 0

        # Performance tracking
        self.optimization_metrics = OptimizationMetrics(
            cache_hit_rate=0.0,
            query_optimization_rate=0.0,
            avg_performance_improvement=0.0,
            total_optimizations=0,
        )

        # Popular queries for cache warming
        self.popular_queries = [
            "action movies",
            "comedy films",
            "horror movies",
            "romantic comedies",
            "sci-fi adventure",
            "animated movies",
            "thriller films",
            "drama movies",
        ]

        logger.info(
            f"Optimization pipeline initialized (enabled: {enable_optimization})"
        )

    def search_with_optimization(
        self,
        query: str,
        search_function: Callable,
        user_context: Optional[Dict] = None,
        filters: Optional[Dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute search with full optimization pipeline.

        Args:
            query: Original search query
            search_function: Base search function to call
            user_context: User preferences and context
            filters: Search filters
            **kwargs: Additional search parameters

        Returns:
            dict: Optimized search results with metadata
        """
        start_time = time.time()
        session_id = f"session_{self.session_counter}"
        self.session_counter += 1

        # Initialize session
        session = SearchSession(
            session_id=session_id,
            original_query=query,
            optimized_query=query,
            cache_hit=False,
            response_time=0.0,
            result_count=0,
            optimization_applied=False,
        )

        self.active_sessions[session_id] = session

        try:
            # Step 1: Check cache first
            cached_results = None
            if self.enable_optimization:
                cached_results = self.cache_manager.get_search_results(query, filters)
                if cached_results is not None:
                    session.cache_hit = True
                    session.response_time = time.time() - start_time
                    session.result_count = len(cached_results)

                    logger.debug(f"Cache hit for query: {query[:50]}")

                    return {
                        "results": cached_results,
                        "total_found": len(cached_results),
                        "search_time": session.response_time,
                        "optimization_info": {
                            "cache_hit": True,
                            "query_optimized": False,
                            "ranking_optimized": False,
                            "session_id": session_id,
                        },
                    }

            # Step 2: Query optimization
            optimized_query = query
            query_optimization_applied = False

            if self.enable_optimization:
                optimization_result = self.query_optimizer.optimize_query(
                    query, user_context
                )

                if optimization_result.optimization_type != "none":
                    optimized_query = optimization_result.optimized_query
                    query_optimization_applied = True
                    session.optimized_query = optimized_query
                    session.optimization_applied = True

                    logger.debug(
                        f"Query optimized: '{query}' -> '{optimized_query}' "
                        f"({optimization_result.optimization_type})"
                    )

            # Step 3: Execute search
            search_start = time.time()
            search_results = search_function(optimized_query, **kwargs)
            search_time = time.time() - search_start

            # Extract results
            if isinstance(search_results, dict) and "results" in search_results:
                results = search_results["results"]
                total_found = search_results.get("total_found", len(results))
            else:
                results = search_results if isinstance(search_results, list) else []
                total_found = len(results)

            # Step 4: Result ranking optimization
            ranking_optimization_applied = False
            if self.enable_optimization and results:
                optimized_results = self.ranking_optimizer.optimize_ranking(
                    query, results, user_context
                )

                # Check if ranking changed significantly
                if self._ranking_changed(results, optimized_results):
                    results = optimized_results
                    ranking_optimization_applied = True
                    logger.debug(f"Ranking optimized for query: {query[:50]}")

            # Step 5: Cache results
            if self.enable_optimization and results and not session.cache_hit:
                self.cache_manager.put_search_results(query, results, filters)
                logger.debug(f"Results cached for query: {query[:50]}")

            # Update session
            session.response_time = time.time() - start_time
            session.result_count = len(results)

            # Update performance profiles
            if self.enable_optimization:
                success_rate = 1.0 if results else 0.0
                self.query_optimizer.update_performance_profile(
                    query, search_time, success_rate, len(results)
                )

            # Prepare response
            response = {
                "results": results,
                "total_found": total_found,
                "search_time": session.response_time,
                "optimization_info": {
                    "cache_hit": False,
                    "query_optimized": query_optimization_applied,
                    "ranking_optimized": ranking_optimization_applied,
                    "original_query": query,
                    "optimized_query": optimized_query,
                    "session_id": session_id,
                },
            }

            # Add search metadata if available
            if isinstance(search_results, dict):
                for key in ["query_info", "search_metadata", "debug_info"]:
                    if key in search_results:
                        response[key] = search_results[key]

            return response

        except Exception as e:
            logger.error(f"Search optimization failed: {str(e)}")
            session.response_time = time.time() - start_time

            # Fallback to basic search
            try:
                fallback_results = search_function(query, **kwargs)
                return fallback_results
            except Exception as fallback_error:
                logger.error(f"Fallback search failed: {str(fallback_error)}")
                return {
                    "results": [],
                    "total_found": 0,
                    "search_time": session.response_time,
                    "error": str(e),
                    "optimization_info": {
                        "cache_hit": False,
                        "query_optimized": False,
                        "ranking_optimized": False,
                        "error": str(e),
                    },
                }

    def record_interaction(
        self, session_id: str, result: Dict, interaction_type: str
    ) -> None:
        """
        Record user interaction for learning and optimization.

        Args:
            session_id: Session identifier
            result: Search result that was interacted with
            interaction_type: Type of interaction (click, view, like, etc.)
        """
        if not self.enable_optimization:
            return

        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]

            # Record interaction
            interaction = {
                "result": result,
                "interaction_type": interaction_type,
                "timestamp": time.time(),
            }
            session.user_interactions.append(interaction)

            # Update ranking optimizer
            self.ranking_optimizer.record_interaction(
                session.original_query, result, interaction_type
            )

            logger.debug(
                f"Recorded {interaction_type} interaction for session {session_id}"
            )

    def warm_cache(self, search_function: Callable) -> Dict[str, Any]:
        """
        Warm cache with popular queries.

        Args:
            search_function: Search function to use for warming

        Returns:
            dict: Cache warming results
        """
        if not self.enable_optimization:
            return {"status": "optimization disabled"}

        logger.info("Starting cache warming...")
        start_time = time.time()

        self.cache_manager.warm_cache(self.popular_queries, search_function)

        warming_time = time.time() - start_time
        cache_stats = self.cache_manager.get_cache_stats()

        return {
            "warming_time": warming_time,
            "queries_warmed": len(self.popular_queries),
            "cache_stats": cache_stats,
            "status": "completed",
        }

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get comprehensive optimization statistics."""
        # Cache statistics
        cache_stats = get_cache_statistics()

        # Query optimization statistics
        query_stats = self.query_optimizer.get_optimization_stats()

        # Ranking optimization statistics
        ranking_stats = self.ranking_optimizer.get_ranking_stats()

        # Session statistics
        total_sessions = len(self.active_sessions)
        cache_hits = sum(1 for s in self.active_sessions.values() if s.cache_hit)
        optimizations = sum(
            1 for s in self.active_sessions.values() if s.optimization_applied
        )

        cache_hit_rate = cache_hits / total_sessions if total_sessions > 0 else 0.0
        optimization_rate = (
            optimizations / total_sessions if total_sessions > 0 else 0.0
        )

        # Performance improvements
        avg_response_time = (
            sum(s.response_time for s in self.active_sessions.values()) / total_sessions
            if total_sessions > 0
            else 0.0
        )

        return {
            "overview": {
                "optimization_enabled": self.enable_optimization,
                "total_sessions": total_sessions,
                "cache_hit_rate": cache_hit_rate,
                "optimization_rate": optimization_rate,
                "avg_response_time": avg_response_time,
            },
            "cache_performance": cache_stats,
            "query_optimization": query_stats,
            "ranking_optimization": ranking_stats,
            "recent_sessions": [
                {
                    "session_id": s.session_id,
                    "original_query": s.original_query,
                    "cache_hit": s.cache_hit,
                    "optimization_applied": s.optimization_applied,
                    "response_time": s.response_time,
                    "result_count": s.result_count,
                    "interactions": len(s.user_interactions),
                }
                for s in list(self.active_sessions.values())[-10:]  # Last 10 sessions
            ],
        }

    def clear_optimization_cache(self) -> Dict[str, str]:
        """Clear all optimization caches."""
        if not self.enable_optimization:
            return {"status": "optimization disabled"}

        self.cache_manager.clear_cache_type("all")
        self.active_sessions.clear()

        return {"status": "caches cleared"}

    def optimize_system_performance(self) -> Dict[str, Any]:
        """
        Perform system-wide optimization based on collected data.

        Returns:
            dict: Optimization results and recommendations
        """
        if not self.enable_optimization:
            return {"status": "optimization disabled"}

        recommendations = []
        actions_taken = []

        # Analyze cache performance
        cache_stats = self.cache_manager.get_cache_stats()
        l1_hit_rate = cache_stats.get("l1_cache", {}).get("hit_rate", 0.0)

        if l1_hit_rate < 0.6:
            recommendations.append(
                "Consider increasing L1 cache size for better hit rates"
            )

        if cache_stats.get("multi_tier", False):
            combined_hit_rate = cache_stats.get("combined_hit_rate", 0.0)
            if combined_hit_rate > 0.8:
                actions_taken.append("Multi-tier caching performing well")

        # Analyze query optimization patterns
        query_stats = self.query_optimizer.get_optimization_stats()
        optimization_count = query_stats.get("total_optimizations", 0)

        if optimization_count > 50:
            avg_improvement = query_stats.get("avg_improvement_score", 0.0)
            if avg_improvement < 0.3:
                recommendations.append(
                    "Query optimization showing limited improvement - review strategies"
                )
            else:
                actions_taken.append("Query optimization providing good results")

        # Analyze ranking optimization
        ranking_stats = self.ranking_optimizer.get_ranking_stats()
        total_interactions = ranking_stats.get("total_interactions", 0)

        if total_interactions > 100:
            avg_relevance = ranking_stats.get("avg_relevance_signal", 0.0)
            if avg_relevance > 0.5:
                actions_taken.append("User interaction learning is improving results")
            else:
                recommendations.append(
                    "Consider adjusting ranking weights based on user feedback"
                )

        # System health recommendations
        stats = self.get_optimization_stats()
        avg_response_time = stats["overview"]["avg_response_time"]

        if avg_response_time > 0.5:
            recommendations.append(
                "Response times are high - consider system optimization"
            )
        elif avg_response_time < 0.1:
            actions_taken.append("Excellent response time performance")

        return {
            "timestamp": datetime.now().isoformat(),
            "actions_taken": actions_taken,
            "recommendations": recommendations,
            "performance_summary": {
                "cache_hit_rate": l1_hit_rate,
                "avg_response_time": avg_response_time,
                "optimization_rate": stats["overview"]["optimization_rate"],
                "total_sessions": stats["overview"]["total_sessions"],
            },
        }

    def _ranking_changed(self, original: List[Dict], optimized: List[Dict]) -> bool:
        """Check if ranking optimization made significant changes."""
        if len(original) != len(optimized):
            return True

        # Check if top 3 results changed order
        for i in range(min(3, len(original))):
            orig_id = str(original[i].get("movie_id", i))
            opt_id = str(optimized[i].get("movie_id", i))
            if orig_id != opt_id:
                return True

        return False


# Global optimization pipeline instance
_optimization_pipeline = None


def get_optimization_pipeline(**kwargs) -> OptimizationPipeline:
    """Get global optimization pipeline instance."""
    global _optimization_pipeline

    if _optimization_pipeline is None:
        _optimization_pipeline = OptimizationPipeline(**kwargs)

    return _optimization_pipeline


# Convenience functions
def optimized_search(
    query: str, search_function: Callable, user_context: Optional[Dict] = None, **kwargs
) -> Dict[str, Any]:
    """
    Execute search with full optimization pipeline.

    Args:
        query: Search query
        search_function: Base search function
        user_context: User preferences
        **kwargs: Additional search parameters

    Returns:
        dict: Optimized search results
    """
    return get_optimization_pipeline().search_with_optimization(
        query, search_function, user_context, **kwargs
    )


def record_search_interaction(
    session_id: str, result: Dict, interaction_type: str
) -> None:
    """Record user interaction for optimization learning."""
    get_optimization_pipeline().record_interaction(session_id, result, interaction_type)


def get_optimization_statistics() -> Dict[str, Any]:
    """Get comprehensive optimization statistics."""
    return get_optimization_pipeline().get_optimization_stats()


def warm_search_cache(search_function: Callable) -> Dict[str, Any]:
    """Warm search cache with popular queries."""
    return get_optimization_pipeline().warm_cache(search_function)
