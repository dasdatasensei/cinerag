"""
Evaluation & Monitoring

This module provides performance measurement and monitoring tools.
Includes metrics for retrieval accuracy, response quality, and system performance.
"""

from .performance_metrics import (
    PerformanceMonitor,
    get_performance_monitor,
    record_search_performance,
    get_current_performance_stats,
)

from .quality_metrics import (
    QualityEvaluator,
    get_quality_evaluator,
    evaluate_search_quality,
    add_manual_relevance_judgments,
)

from .evaluation_pipeline import (
    EvaluationPipeline,
    get_evaluation_pipeline,
    run_full_evaluation,
    quick_evaluation,
)

__all__ = [
    "PerformanceMonitor",
    "get_performance_monitor",
    "record_search_performance",
    "get_current_performance_stats",
    "QualityEvaluator",
    "get_quality_evaluator",
    "evaluate_search_quality",
    "add_manual_relevance_judgments",
    "EvaluationPipeline",
    "get_evaluation_pipeline",
    "run_full_evaluation",
    "quick_evaluation",
]
