"""
Performance Metrics

Measures system performance including latency, throughput, resource usage,
and other operational metrics for the RAG pipeline.
"""

import logging
import time
import psutil
import threading
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict, deque
from dataclasses import dataclass, field
import statistics
import json
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Single performance measurement."""

    timestamp: float
    metric_name: str
    value: float
    unit: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchMetrics:
    """Metrics for a single search operation."""

    query: str
    search_time: float
    processing_time: float
    total_time: float
    results_count: int
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """
    Real-time performance monitoring system.

    Tracks system metrics, search performance, and provides
    statistical analysis and alerting capabilities.
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize performance monitor.

        Args:
            max_history: Maximum number of metrics to keep in memory
        """
        self.max_history = max_history
        self.metrics_history = defaultdict(lambda: deque(maxlen=max_history))
        self.search_history = deque(maxlen=max_history)
        self._lock = threading.Lock()

        # Performance thresholds
        self.thresholds = {
            "search_latency_ms": 500,  # 500ms max search time
            "cpu_usage_percent": 80,  # 80% max CPU usage
            "memory_usage_percent": 85,  # 85% max memory usage
            "error_rate_percent": 5,  # 5% max error rate
        }

        # Monitoring state
        self.is_monitoring = False
        self.monitor_thread = None
        self.system_metrics_interval = 5  # seconds

    def start_monitoring(self):
        """Start continuous system monitoring."""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_system_metrics)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info("Performance monitoring started")

    def stop_monitoring(self):
        """Stop continuous system monitoring."""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        logger.info("Performance monitoring stopped")

    def record_metric(
        self, name: str, value: float, unit: str = "", metadata: Optional[Dict] = None
    ):
        """Record a performance metric."""
        metric = PerformanceMetric(
            timestamp=time.time(),
            metric_name=name,
            value=value,
            unit=unit,
            metadata=metadata or {},
        )

        with self._lock:
            self.metrics_history[name].append(metric)

    def record_search_metrics(self, search_metrics: SearchMetrics):
        """Record search operation metrics."""
        with self._lock:
            self.search_history.append(search_metrics)

        # Record individual metrics
        self.record_metric("search_latency", search_metrics.search_time * 1000, "ms")
        self.record_metric(
            "processing_latency", search_metrics.processing_time * 1000, "ms"
        )
        self.record_metric("total_latency", search_metrics.total_time * 1000, "ms")
        self.record_metric("results_count", search_metrics.results_count, "count")

        if search_metrics.error:
            self.record_metric("search_error", 1, "count")
        else:
            self.record_metric("search_success", 1, "count")

    def get_metric_stats(
        self, metric_name: str, time_window_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get statistical summary of a metric."""
        with self._lock:
            metrics = list(self.metrics_history.get(metric_name, []))

        if not metrics:
            return {"error": f"No data for metric: {metric_name}"}

        # Filter by time window if specified
        if time_window_minutes:
            cutoff_time = time.time() - (time_window_minutes * 60)
            metrics = [m for m in metrics if m.timestamp >= cutoff_time]

        if not metrics:
            return {"error": f"No recent data for metric: {metric_name}"}

        values = [m.value for m in metrics]

        return {
            "metric_name": metric_name,
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "percentiles": {
                "p50": statistics.median(values),
                "p95": self._percentile(values, 0.95),
                "p99": self._percentile(values, 0.99),
            },
            "unit": metrics[0].unit if metrics else "",
            "time_window_minutes": time_window_minutes,
        }

    def get_search_performance_summary(
        self, time_window_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get comprehensive search performance summary."""
        with self._lock:
            searches = list(self.search_history)

        if not searches:
            return {"error": "No search data available"}

        # Filter by time window if specified
        if time_window_minutes:
            cutoff_time = time.time() - (time_window_minutes * 60)
            searches = [
                s
                for s in searches
                if hasattr(s, "timestamp")
                or time.time() - time_window_minutes * 60 < time.time()
            ]

        total_searches = len(searches)
        successful_searches = [s for s in searches if not s.error]
        failed_searches = [s for s in searches if s.error]

        if not successful_searches:
            return {"error": "No successful searches in time window"}

        # Calculate metrics
        search_times = [
            s.search_time * 1000 for s in successful_searches
        ]  # Convert to ms
        total_times = [s.total_time * 1000 for s in successful_searches]
        result_counts = [s.results_count for s in successful_searches]

        return {
            "summary": {
                "total_searches": total_searches,
                "successful_searches": len(successful_searches),
                "failed_searches": len(failed_searches),
                "success_rate": (
                    len(successful_searches) / total_searches
                    if total_searches > 0
                    else 0
                ),
                "error_rate": (
                    len(failed_searches) / total_searches if total_searches > 0 else 0
                ),
            },
            "latency_metrics": {
                "search_time_ms": {
                    "min": min(search_times),
                    "max": max(search_times),
                    "mean": statistics.mean(search_times),
                    "median": statistics.median(search_times),
                    "p95": self._percentile(search_times, 0.95),
                    "p99": self._percentile(search_times, 0.99),
                },
                "total_time_ms": {
                    "min": min(total_times),
                    "max": max(total_times),
                    "mean": statistics.mean(total_times),
                    "median": statistics.median(total_times),
                    "p95": self._percentile(total_times, 0.95),
                    "p99": self._percentile(total_times, 0.99),
                },
            },
            "result_metrics": {
                "avg_results_per_search": statistics.mean(result_counts),
                "min_results": min(result_counts),
                "max_results": max(result_counts),
            },
            "errors": {
                "total_errors": len(failed_searches),
                "error_types": self._analyze_error_types(failed_searches),
            },
            "time_window_minutes": time_window_minutes,
        }

    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Get recent error rate
        recent_searches = self.get_search_performance_summary(time_window_minutes=5)
        error_rate = 0
        if not isinstance(recent_searches, dict) or "error" not in recent_searches:
            error_rate = recent_searches.get("summary", {}).get("error_rate", 0) * 100

        # Check thresholds
        alerts = []
        if cpu_percent > self.thresholds["cpu_usage_percent"]:
            alerts.append(f"High CPU usage: {cpu_percent:.1f}%")

        if memory.percent > self.thresholds["memory_usage_percent"]:
            alerts.append(f"High memory usage: {memory.percent:.1f}%")

        if error_rate > self.thresholds["error_rate_percent"]:
            alerts.append(f"High error rate: {error_rate:.1f}%")

        return {
            "timestamp": datetime.now().isoformat(),
            "system_resources": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_free_gb": disk.free / (1024**3),
                "disk_usage_percent": (disk.used / disk.total) * 100,
            },
            "search_performance": {
                "recent_error_rate": error_rate,
                "total_searches_tracked": len(self.search_history),
                "metrics_tracked": len(self.metrics_history),
            },
            "health_status": "HEALTHY" if not alerts else "WARNING",
            "alerts": alerts,
            "thresholds": self.thresholds,
        }

    def benchmark_search_performance(
        self, search_function: Callable, test_queries: List[str], iterations: int = 3
    ) -> Dict[str, Any]:
        """
        Benchmark search performance with test queries.

        Args:
            search_function: Function to test (should accept query string)
            test_queries: List of test queries
            iterations: Number of iterations per query

        Returns:
            dict: Comprehensive benchmark results
        """
        logger.info(
            f"Starting search performance benchmark with {len(test_queries)} queries, {iterations} iterations each"
        )

        benchmark_results = []
        total_start_time = time.time()

        for query in test_queries:
            query_results = []

            for iteration in range(iterations):
                start_time = time.time()

                try:
                    # Execute search
                    result = search_function(query)
                    end_time = time.time()

                    search_time = end_time - start_time
                    results_count = (
                        len(result.get("results", []))
                        if isinstance(result, dict)
                        else 0
                    )

                    query_results.append(
                        {
                            "iteration": iteration + 1,
                            "search_time": search_time,
                            "results_count": results_count,
                            "success": True,
                            "error": None,
                        }
                    )

                except Exception as e:
                    end_time = time.time()
                    query_results.append(
                        {
                            "iteration": iteration + 1,
                            "search_time": end_time - start_time,
                            "results_count": 0,
                            "success": False,
                            "error": str(e),
                        }
                    )

            # Calculate query statistics
            successful_results = [r for r in query_results if r["success"]]

            if successful_results:
                search_times = [r["search_time"] for r in successful_results]
                result_counts = [r["results_count"] for r in successful_results]

                query_stats = {
                    "query": query,
                    "iterations": iterations,
                    "successful_iterations": len(successful_results),
                    "success_rate": len(successful_results) / iterations,
                    "avg_search_time": statistics.mean(search_times),
                    "min_search_time": min(search_times),
                    "max_search_time": max(search_times),
                    "avg_results_count": statistics.mean(result_counts),
                    "errors": [r["error"] for r in query_results if not r["success"]],
                }
            else:
                query_stats = {
                    "query": query,
                    "iterations": iterations,
                    "successful_iterations": 0,
                    "success_rate": 0,
                    "errors": [r["error"] for r in query_results],
                }

            benchmark_results.append(query_stats)

        total_time = time.time() - total_start_time

        # Overall statistics
        all_successful = [r for r in benchmark_results if r["success_rate"] > 0]
        if all_successful:
            all_search_times = []
            for result in all_successful:
                if "avg_search_time" in result:
                    all_search_times.extend(
                        [result["avg_search_time"]] * result["successful_iterations"]
                    )

            overall_stats = {
                "total_queries": len(test_queries),
                "total_iterations": len(test_queries) * iterations,
                "successful_queries": len(all_successful),
                "overall_success_rate": len(all_successful) / len(test_queries),
                "avg_search_time": (
                    statistics.mean(all_search_times) if all_search_times else 0
                ),
                "total_benchmark_time": total_time,
            }
        else:
            overall_stats = {
                "total_queries": len(test_queries),
                "total_iterations": len(test_queries) * iterations,
                "successful_queries": 0,
                "overall_success_rate": 0,
                "total_benchmark_time": total_time,
            }

        return {
            "benchmark_id": f"benchmark_{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            "overall_stats": overall_stats,
            "detailed_results": benchmark_results,
            "performance_grade": self._calculate_performance_grade(overall_stats),
        }

    def _monitor_system_metrics(self):
        """Background thread for monitoring system metrics."""
        while self.is_monitoring:
            try:
                # Record system metrics
                self.record_metric("cpu_usage", psutil.cpu_percent(), "percent")
                memory = psutil.virtual_memory()
                self.record_metric("memory_usage", memory.percent, "percent")
                self.record_metric(
                    "memory_available", memory.available / (1024**3), "GB"
                )

                # Record disk usage
                disk = psutil.disk_usage("/")
                self.record_metric(
                    "disk_usage", (disk.used / disk.total) * 100, "percent"
                )

                time.sleep(self.system_metrics_interval)

            except Exception as e:
                logger.error(f"Error in system monitoring: {str(e)}")
                time.sleep(self.system_metrics_interval)

    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(percentile * len(sorted_values))
        if index >= len(sorted_values):
            return sorted_values[-1]
        return sorted_values[index]

    def _analyze_error_types(
        self, failed_searches: List[SearchMetrics]
    ) -> Dict[str, int]:
        """Analyze types of errors in failed searches."""
        error_counts = defaultdict(int)
        for search in failed_searches:
            if search.error:
                # Simplify error messages for grouping
                error_type = (
                    search.error.split(":")[0] if ":" in search.error else search.error
                )
                error_counts[error_type] += 1
        return dict(error_counts)

    def _calculate_performance_grade(self, stats: Dict[str, Any]) -> str:
        """Calculate overall performance grade."""
        success_rate = stats.get("overall_success_rate", 0)
        avg_search_time = stats.get("avg_search_time", float("inf"))

        if success_rate >= 0.95 and avg_search_time <= 0.1:
            return "A+"
        elif success_rate >= 0.9 and avg_search_time <= 0.2:
            return "A"
        elif success_rate >= 0.8 and avg_search_time <= 0.5:
            return "B"
        elif success_rate >= 0.7 and avg_search_time <= 1.0:
            return "C"
        else:
            return "D"

    def export_metrics(self, filename: Optional[str] = None) -> str:
        """Export metrics to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_metrics_{timestamp}.json"

        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "system_health": self.get_system_health(),
            "search_performance": self.get_search_performance_summary(),
            "metric_summaries": {
                name: self.get_metric_stats(name)
                for name in self.metrics_history.keys()
            },
        }

        with open(filename, "w") as f:
            json.dump(export_data, f, indent=2, default=str)

        logger.info(f"Metrics exported to {filename}")
        return filename


# Global instance
performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    return performance_monitor


# Convenience functions
def record_search_performance(
    query: str,
    search_time: float,
    results_count: int,
    processing_time: float = 0,
    error: Optional[str] = None,
) -> None:
    """Record search performance metrics."""
    metrics = SearchMetrics(
        query=query,
        search_time=search_time,
        processing_time=processing_time,
        total_time=search_time + processing_time,
        results_count=results_count,
        error=error,
    )
    performance_monitor.record_search_metrics(metrics)


def get_current_performance_stats() -> Dict[str, Any]:
    """Get current performance statistics."""
    return {
        "system_health": performance_monitor.get_system_health(),
        "search_performance": performance_monitor.get_search_performance_summary(
            time_window_minutes=30
        ),
        "key_metrics": {
            "search_latency": performance_monitor.get_metric_stats(
                "search_latency", 30
            ),
            "cpu_usage": performance_monitor.get_metric_stats("cpu_usage", 10),
            "memory_usage": performance_monitor.get_metric_stats("memory_usage", 10),
        },
    }
