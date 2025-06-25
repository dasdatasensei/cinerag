"""
Evaluation Pipeline

Orchestrates comprehensive evaluation of the RAG system including
performance monitoring, quality assessment, and automated testing.
"""

import logging
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import json

from .performance_metrics import get_performance_monitor, record_search_performance
from .quality_metrics import (
    get_quality_evaluator,
    evaluate_search_quality,
    add_manual_relevance_judgments,
)

# Configure logging
logger = logging.getLogger(__name__)


class EvaluationPipeline:
    """
    Comprehensive evaluation pipeline for RAG system assessment.

    Combines performance monitoring, quality evaluation, and automated
    testing to provide holistic system evaluation.
    """

    def __init__(self):
        """Initialize evaluation pipeline."""
        self.performance_monitor = get_performance_monitor()
        self.quality_evaluator = get_quality_evaluator()

        # Test scenarios
        self.test_scenarios = {
            "basic_search": {
                "queries": [
                    "action movies",
                    "comedy films",
                    "horror",
                    "romance",
                    "sci-fi",
                ],
                "description": "Basic genre-based search queries",
            },
            "complex_search": {
                "queries": [
                    "funny animated movies for kids",
                    "sci-fi space adventure like Star Wars",
                    "romantic comedies from the 1990s",
                    "horror films with good ratings",
                    "popular action movies with explosions",
                ],
                "description": "Complex multi-faceted search queries",
            },
            "edge_cases": {
                "queries": [
                    "",
                    "a",
                    "the the the",
                    "xyznonexistentmovie123",
                    "movies from 2050",
                ],
                "description": "Edge cases and error conditions",
            },
            "specific_movies": {
                "queries": [
                    "Toy Story",
                    "The Matrix",
                    "Pulp Fiction",
                    "Forrest Gump",
                    "The Godfather",
                ],
                "description": "Specific movie title searches",
            },
        }

        # Sample relevance judgments for testing
        self.sample_judgments = {
            "action movies": {
                "1": 0.9,  # Die Hard
                "2": 0.8,  # Terminator
                "3": 0.2,  # Romantic comedy
            },
            "comedy films": {
                "4": 0.9,  # Comedy movie
                "5": 0.8,  # Comedy-drama
                "1": 0.1,  # Action movie
            },
        }

    def run_comprehensive_evaluation(
        self, search_function: Callable, enable_monitoring: bool = True
    ) -> Dict[str, Any]:
        """
        Run comprehensive evaluation of the RAG system.

        Args:
            search_function: Function to test (should accept query string and return results)
            enable_monitoring: Whether to enable performance monitoring

        Returns:
            dict: Comprehensive evaluation results
        """
        logger.info("Starting comprehensive RAG system evaluation")

        evaluation_start_time = time.time()
        results = {}

        try:
            # Start performance monitoring
            if enable_monitoring:
                self.performance_monitor.start_monitoring()

            # Run performance benchmarks
            logger.info("Running performance benchmarks...")
            performance_results = self._run_performance_evaluation(search_function)
            results["performance"] = performance_results

            # Run quality evaluation
            logger.info("Running quality evaluation...")
            quality_results = self._run_quality_evaluation(search_function)
            results["quality"] = quality_results

            # Run scenario testing
            logger.info("Running scenario testing...")
            scenario_results = self._run_scenario_testing(search_function)
            results["scenarios"] = scenario_results

            # Generate overall assessment
            logger.info("Generating overall assessment...")
            overall_assessment = self._generate_overall_assessment(results)
            results["overall_assessment"] = overall_assessment

            # System health check
            system_health = self.performance_monitor.get_system_health()
            results["system_health"] = system_health

            evaluation_time = time.time() - evaluation_start_time
            results["evaluation_metadata"] = {
                "total_evaluation_time": evaluation_time,
                "timestamp": datetime.now().isoformat(),
                "evaluation_id": f"eval_{int(time.time())}",
            }

            logger.info(f"Comprehensive evaluation completed in {evaluation_time:.2f}s")

        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}")
            results["error"] = str(e)

        finally:
            # Stop monitoring
            if enable_monitoring:
                self.performance_monitor.stop_monitoring()

        return results

    def _run_performance_evaluation(self, search_function: Callable) -> Dict[str, Any]:
        """Run performance evaluation tests."""
        # Get all test queries
        all_queries = []
        for scenario in self.test_scenarios.values():
            all_queries.extend(scenario["queries"])

        # Remove duplicates and empty queries
        test_queries = list(set([q for q in all_queries if q.strip()]))

        # Run benchmark
        benchmark_results = self.performance_monitor.benchmark_search_performance(
            search_function, test_queries, iterations=2
        )

        # Get current performance stats
        current_stats = self.performance_monitor.get_search_performance_summary(
            time_window_minutes=10
        )

        # Get system health
        system_health = self.performance_monitor.get_system_health()

        return {
            "benchmark": benchmark_results,
            "current_stats": current_stats,
            "system_health": system_health,
        }

    def _run_quality_evaluation(self, search_function: Callable) -> Dict[str, Any]:
        """Run quality evaluation tests."""
        # Add sample relevance judgments
        for query, judgments in self.sample_judgments.items():
            add_manual_relevance_judgments(query, judgments)

        # Evaluate specific queries
        quality_test_queries = [
            "action movies",
            "comedy films",
            "animated movies for kids",
            "sci-fi space adventure",
            "romantic comedies",
        ]

        query_results = {}
        for query in quality_test_queries:
            try:
                search_results = search_function(query)
                if isinstance(search_results, dict) and "results" in search_results:
                    results_list = search_results["results"]
                else:
                    results_list = (
                        search_results if isinstance(search_results, list) else []
                    )

                query_results[query] = results_list

            except Exception as e:
                logger.error(f"Quality evaluation failed for query '{query}': {str(e)}")
                query_results[query] = []

        # Convert to SearchResult format and evaluate
        evaluation_results = {}
        for query, results in query_results.items():
            if results:
                evaluation_results[query] = evaluate_search_quality(query, results)

        # Generate quality report
        if evaluation_results:
            # Aggregate results for reporting
            aggregate_evaluation = self.quality_evaluator.evaluate_query_set(
                {
                    query: self._convert_to_search_results(results)
                    for query, results in query_results.items()
                    if results
                }
            )

            quality_report = self.quality_evaluator.generate_evaluation_report(
                aggregate_evaluation
            )

            return {
                "individual_evaluations": evaluation_results,
                "aggregate_evaluation": aggregate_evaluation,
                "quality_report": quality_report,
            }
        else:
            return {
                "error": "No successful quality evaluations",
                "attempted_queries": quality_test_queries,
            }

    def _convert_to_search_results(self, results: List[Dict]) -> List:
        """Convert search results to SearchResult format."""
        from .quality_metrics import SearchResult

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

        return search_results

    def _run_scenario_testing(self, search_function: Callable) -> Dict[str, Any]:
        """Run scenario-based testing."""
        scenario_results = {}

        for scenario_name, scenario_config in self.test_scenarios.items():
            logger.info(f"Testing scenario: {scenario_name}")

            scenario_result = {
                "description": scenario_config["description"],
                "queries": scenario_config["queries"],
                "results": [],
                "success_count": 0,
                "error_count": 0,
                "avg_response_time": 0.0,
            }

            total_time = 0.0

            for query in scenario_config["queries"]:
                start_time = time.time()

                try:
                    result = search_function(query)
                    response_time = time.time() - start_time
                    total_time += response_time

                    # Analyze result
                    if isinstance(result, dict) and "results" in result:
                        results_count = len(result["results"])
                        success = True
                    elif isinstance(result, list):
                        results_count = len(result)
                        success = True
                    else:
                        results_count = 0
                        success = False

                    scenario_result["results"].append(
                        {
                            "query": query,
                            "success": success,
                            "response_time": response_time,
                            "results_count": results_count,
                            "error": None,
                        }
                    )

                    if success:
                        scenario_result["success_count"] += 1

                    # Record performance
                    record_search_performance(
                        query,
                        response_time,
                        results_count,
                        error=None if success else "No results returned",
                    )

                except Exception as e:
                    response_time = time.time() - start_time
                    total_time += response_time

                    scenario_result["results"].append(
                        {
                            "query": query,
                            "success": False,
                            "response_time": response_time,
                            "results_count": 0,
                            "error": str(e),
                        }
                    )

                    scenario_result["error_count"] += 1

                    # Record performance
                    record_search_performance(query, response_time, 0, error=str(e))

            # Calculate averages
            total_queries = len(scenario_config["queries"])
            scenario_result["success_rate"] = (
                scenario_result["success_count"] / total_queries
            )
            scenario_result["avg_response_time"] = (
                total_time / total_queries if total_queries > 0 else 0.0
            )

            scenario_results[scenario_name] = scenario_result

        return scenario_results

    def _generate_overall_assessment(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall system assessment."""
        assessment = {
            "timestamp": datetime.now().isoformat(),
            "overall_grade": "D",
            "summary": {},
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
        }

        # Performance assessment
        performance_grade = "D"
        if "performance" in results and "benchmark" in results["performance"]:
            benchmark = results["performance"]["benchmark"]
            perf_grade = benchmark.get("performance_grade", "D")
            avg_search_time = benchmark.get("overall_stats", {}).get(
                "avg_search_time", float("inf")
            )
            success_rate = benchmark.get("overall_stats", {}).get(
                "overall_success_rate", 0
            )

            if success_rate >= 0.9 and avg_search_time <= 0.2:
                performance_grade = "A"
            elif success_rate >= 0.8 and avg_search_time <= 0.5:
                performance_grade = "B"
            elif success_rate >= 0.7 and avg_search_time <= 1.0:
                performance_grade = "C"

            assessment["summary"]["performance_grade"] = performance_grade
            assessment["summary"]["avg_search_time"] = avg_search_time
            assessment["summary"]["search_success_rate"] = success_rate

        # Quality assessment
        quality_grade = "D"
        if "quality" in results and "quality_report" in results["quality"]:
            quality_report = results["quality"]["quality_report"]
            quality_grade = quality_report.get("overall_grade", "D")

            assessment["summary"]["quality_grade"] = quality_grade
            assessment["summary"]["avg_ndcg_at_5"] = quality_report.get(
                "key_metrics", {}
            ).get("avg_ndcg_at_5", 0.0)
            assessment["summary"]["avg_precision_at_5"] = quality_report.get(
                "key_metrics", {}
            ).get("avg_precision_at_5", 0.0)

        # Scenario assessment
        scenario_success_rate = 0.0
        if "scenarios" in results:
            total_success = 0
            total_queries = 0

            for scenario_result in results["scenarios"].values():
                total_success += scenario_result.get("success_count", 0)
                total_queries += len(scenario_result.get("queries", []))

            scenario_success_rate = (
                total_success / total_queries if total_queries > 0 else 0.0
            )
            assessment["summary"]["scenario_success_rate"] = scenario_success_rate

        # Overall grade calculation
        grade_scores = {"A": 4, "B": 3, "C": 2, "D": 1}
        avg_grade_score = (
            grade_scores.get(performance_grade, 1) + grade_scores.get(quality_grade, 1)
        ) / 2

        if avg_grade_score >= 3.5:
            assessment["overall_grade"] = "A"
        elif avg_grade_score >= 2.5:
            assessment["overall_grade"] = "B"
        elif avg_grade_score >= 1.5:
            assessment["overall_grade"] = "C"
        else:
            assessment["overall_grade"] = "D"

        # Generate strengths and weaknesses
        if performance_grade in ["A", "B"]:
            assessment["strengths"].append(
                "Excellent search performance and response times"
            )
        else:
            assessment["weaknesses"].append("Search performance needs improvement")

        if quality_grade in ["A", "B"]:
            assessment["strengths"].append("High quality search results and relevance")
        else:
            assessment["weaknesses"].append(
                "Search result quality and relevance needs improvement"
            )

        if scenario_success_rate >= 0.9:
            assessment["strengths"].append("Robust handling of various query types")
        else:
            assessment["weaknesses"].append("Some query types not handled well")

        # Generate recommendations
        if performance_grade == "D":
            assessment["recommendations"].append(
                "Optimize search algorithms and infrastructure for better performance"
            )

        if quality_grade == "D":
            assessment["recommendations"].append(
                "Improve ranking algorithms and query understanding"
            )

        if scenario_success_rate < 0.8:
            assessment["recommendations"].append(
                "Enhance error handling and edge case management"
            )

        return assessment

    def export_evaluation_results(
        self, results: Dict[str, Any], filename: Optional[str] = None
    ) -> str:
        """Export evaluation results to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rag_evaluation_{timestamp}.json"

        # Create exportable format
        export_data = {
            "evaluation_metadata": results.get("evaluation_metadata", {}),
            "overall_assessment": results.get("overall_assessment", {}),
            "performance_summary": self._extract_performance_summary(results),
            "quality_summary": self._extract_quality_summary(results),
            "scenario_summary": self._extract_scenario_summary(results),
            "system_health": results.get("system_health", {}),
        }

        with open(filename, "w") as f:
            json.dump(export_data, f, indent=2, default=str)

        logger.info(f"Evaluation results exported to {filename}")
        return filename

    def _extract_performance_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract performance summary for export."""
        if "performance" not in results:
            return {}

        perf = results["performance"]
        summary = {}

        if "benchmark" in perf:
            benchmark = perf["benchmark"]
            summary["benchmark_grade"] = benchmark.get("performance_grade", "Unknown")
            summary["overall_stats"] = benchmark.get("overall_stats", {})

        if "current_stats" in perf:
            current = perf["current_stats"]
            if not isinstance(current, dict) or "error" not in current:
                summary["current_performance"] = current

        return summary

    def _extract_quality_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract quality summary for export."""
        if "quality" not in results:
            return {}

        quality = results["quality"]
        summary = {}

        if "quality_report" in quality:
            report = quality["quality_report"]
            summary["overall_grade"] = report.get("overall_grade", "Unknown")
            summary["key_metrics"] = report.get("key_metrics", {})
            summary["recommendations"] = report.get("recommendations", [])

        return summary

    def _extract_scenario_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract scenario summary for export."""
        if "scenarios" not in results:
            return {}

        scenarios = results["scenarios"]
        summary = {}

        for name, scenario in scenarios.items():
            summary[name] = {
                "success_rate": scenario.get("success_rate", 0.0),
                "avg_response_time": scenario.get("avg_response_time", 0.0),
                "total_queries": len(scenario.get("queries", [])),
                "successful_queries": scenario.get("success_count", 0),
            }

        return summary


# Global instance
evaluation_pipeline = EvaluationPipeline()


def get_evaluation_pipeline() -> EvaluationPipeline:
    """Get global evaluation pipeline instance."""
    return evaluation_pipeline


# Convenience functions
def run_full_evaluation(search_function: Callable) -> Dict[str, Any]:
    """
    Run comprehensive evaluation of RAG system.

    Args:
        search_function: Search function to evaluate

    Returns:
        dict: Comprehensive evaluation results
    """
    return evaluation_pipeline.run_comprehensive_evaluation(search_function)


def quick_evaluation(search_function: Callable) -> Dict[str, Any]:
    """
    Run quick evaluation for development purposes.

    Args:
        search_function: Search function to evaluate

    Returns:
        dict: Quick evaluation results
    """
    # Just run a few basic tests
    test_queries = ["action movies", "comedy", "sci-fi adventure"]

    results = {}
    for query in test_queries:
        start_time = time.time()
        try:
            search_result = search_function(query)
            response_time = time.time() - start_time

            if isinstance(search_result, dict) and "results" in search_result:
                results_count = len(search_result["results"])
            elif isinstance(search_result, list):
                results_count = len(search_result)
            else:
                results_count = 0

            results[query] = {
                "success": True,
                "response_time": response_time,
                "results_count": results_count,
            }

        except Exception as e:
            results[query] = {
                "success": False,
                "response_time": time.time() - start_time,
                "error": str(e),
            }

    # Calculate summary
    successful_queries = [r for r in results.values() if r.get("success", False)]
    success_rate = len(successful_queries) / len(test_queries)
    avg_response_time = (
        sum(r["response_time"] for r in successful_queries) / len(successful_queries)
        if successful_queries
        else 0
    )

    return {
        "query_results": results,
        "summary": {
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "total_queries": len(test_queries),
            "successful_queries": len(successful_queries),
        },
    }
