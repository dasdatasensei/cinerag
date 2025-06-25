"""
Optimization & Tuning

Advanced optimization system for RAG pipeline performance improvement.
Includes intelligent caching, query optimization, result ranking optimization,
and comprehensive performance monitoring.
"""

from .cache_manager import (
    CacheManager,
    get_cache_manager,
    cache_search_results,
    get_cached_search_results,
    cache_query_embedding,
    get_cached_query_embedding,
    get_cache_statistics,
)

from .performance_optimizer import (
    QueryOptimizer,
    ResultRankingOptimizer,
    get_query_optimizer,
    get_ranking_optimizer,
    optimize_query,
    optimize_results,
    record_user_interaction,
)

from .optimization_pipeline import (
    OptimizationPipeline,
    get_optimization_pipeline,
    optimized_search,
    record_search_interaction,
    get_optimization_statistics,
    warm_search_cache,
)

__all__ = [
    # Cache Management
    "CacheManager",
    "get_cache_manager",
    "cache_search_results",
    "get_cached_search_results",
    "cache_query_embedding",
    "get_cached_query_embedding",
    "get_cache_statistics",
    # Performance Optimization
    "QueryOptimizer",
    "ResultRankingOptimizer",
    "get_query_optimizer",
    "get_ranking_optimizer",
    "optimize_query",
    "optimize_results",
    "record_user_interaction",
    # Optimization Pipeline
    "OptimizationPipeline",
    "get_optimization_pipeline",
    "optimized_search",
    "record_search_interaction",
    "get_optimization_statistics",
    "warm_search_cache",
]
