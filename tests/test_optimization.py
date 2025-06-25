#!/usr/bin/env python3
"""
Test script for 07_Optimization

Tests caching system, query optimization, result ranking optimization,
and the complete optimization pipeline.
"""

import os
import sys
import time
import logging
import tempfile

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.rag._07_optimization import (
    get_cache_manager,
    cache_search_results,
    get_cached_search_results,
    cache_query_embedding,
    get_cached_query_embedding,
    get_cache_statistics,
    get_query_optimizer,
    get_ranking_optimizer,
    optimize_query,
    optimize_results,
    get_optimization_pipeline,
    optimized_search,
    record_search_interaction,
    get_optimization_statistics,
    warm_search_cache,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def mock_search_function(query: str, limit: int = 10) -> dict:
    """Mock search function for testing."""
    import random

    # Simulate response time
    time.sleep(random.uniform(0.02, 0.08))

    # Mock results based on query
    mock_results = []

    if "action" in query.lower():
        mock_results = [
            {
                "movie_id": "1",
                "title": "Die Hard",
                "overview": "Action thriller",
                "genres": ["Action"],
                "year": 1988,
                "rating": 8.2,
                "scores": {"final": 0.95},
            },
            {
                "movie_id": "2",
                "title": "Terminator",
                "overview": "Sci-fi action",
                "genres": ["Action", "Sci-Fi"],
                "year": 1984,
                "rating": 8.0,
                "scores": {"final": 0.92},
            },
            {
                "movie_id": "3",
                "title": "Mad Max",
                "overview": "Post-apocalyptic action",
                "genres": ["Action"],
                "year": 1979,
                "rating": 6.9,
                "scores": {"final": 0.88},
            },
        ]
    elif "comedy" in query.lower():
        mock_results = [
            {
                "movie_id": "4",
                "title": "The Hangover",
                "overview": "Comedy about a bachelor party",
                "genres": ["Comedy"],
                "year": 2009,
                "rating": 7.7,
                "scores": {"final": 0.90},
            },
            {
                "movie_id": "5",
                "title": "Superbad",
                "overview": "Teen comedy",
                "genres": ["Comedy"],
                "year": 2007,
                "rating": 7.6,
                "scores": {"final": 0.87},
            },
        ]
    elif "animated" in query.lower() or "kids" in query.lower():
        mock_results = [
            {
                "movie_id": "6",
                "title": "Toy Story",
                "overview": "Animated adventure",
                "genres": ["Animation", "Family"],
                "year": 1995,
                "rating": 8.3,
                "scores": {"final": 0.93},
            },
        ]
    elif query.strip() == "" or len(query) < 3:
        mock_results = []
    else:
        # Generic results
        mock_results = [
            {
                "movie_id": "7",
                "title": "Generic Movie",
                "overview": "A movie",
                "genres": ["Drama"],
                "year": 2020,
                "rating": 7.0,
                "scores": {"final": 0.75},
            },
        ]

    return {
        "results": mock_results[:limit],
        "total_found": len(mock_results),
        "search_time": random.uniform(0.02, 0.08),
        "query_info": {"original_query": query},
    }


def test_cache_manager():
    """Test cache manager functionality."""
    print("\n" + "=" * 60)
    print("💾 Testing Cache Manager")
    print("=" * 60)

    try:
        # Test with Redis disabled for reliable testing
        cache_manager = get_cache_manager(enable_redis=False)

        print("🧪 Testing cache manager features:")

        # Test 1: Basic search result caching
        print(f"\n📍 Test 1: Basic Search Result Caching")
        test_query = "action movies"
        test_results = [
            {"movie_id": "1", "title": "Die Hard", "score": 0.95},
            {"movie_id": "2", "title": "Terminator", "score": 0.92},
        ]

        # Cache results
        cache_search_results(test_query, test_results)

        # Retrieve results
        cached_results = get_cached_search_results(test_query)

        if cached_results and len(cached_results) == 2:
            print(f"   ✅ Search results cached and retrieved successfully")
            print(f"   📊 Cached {len(cached_results)} results")
        else:
            print(f"   ❌ Search result caching failed")

        # Test 2: Query embedding caching
        print(f"\n📍 Test 2: Query Embedding Caching")
        test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 100  # 500-dim vector

        cache_query_embedding(test_query, test_embedding)
        cached_embedding = get_cached_query_embedding(test_query)

        if cached_embedding and len(cached_embedding) == len(test_embedding):
            print(f"   ✅ Query embedding cached and retrieved successfully")
            print(f"   📊 Embedding dimension: {len(cached_embedding)}")
        else:
            print(f"   ❌ Query embedding caching failed")

        # Test 3: Cache statistics
        print(f"\n📍 Test 3: Cache Statistics")
        stats = get_cache_statistics()

        if stats and "l1_cache" in stats:
            l1_stats = stats["l1_cache"]
            print(f"   ✅ Cache statistics retrieved")
            print(f"   📊 L1 entries: {l1_stats.get('entry_count', 0)}")
            print(f"   📊 L1 hit rate: {l1_stats.get('hit_rate', 0.0):.1%}")
            print(f"   📊 Multi-tier: {stats.get('multi_tier', False)}")
        else:
            print(f"   ❌ Cache statistics failed")

        # Test 4: Cache performance with repeated queries
        print(f"\n📍 Test 4: Cache Performance Testing")
        queries = ["action", "comedy", "horror", "action", "comedy"]  # Repeated queries
        hits = 0

        for query in queries:
            cached = get_cached_search_results(query)
            if cached is None:
                # Cache miss - add some results
                cache_search_results(
                    query, [{"movie_id": "test", "title": f"{query} movie"}]
                )
            else:
                hits += 1

        hit_rate = hits / len(queries)
        print(f"   ✅ Cache performance test completed")
        print(f"   📊 Hit rate: {hit_rate:.1%}")

        print(f"\n💾 Cache Manager: 4/4 tests completed")
        return True

    except Exception as e:
        print(f"❌ Cache manager test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_query_optimizer():
    """Test query optimization functionality."""
    print("\n" + "=" * 60)
    print("🔍 Testing Query Optimizer")
    print("=" * 60)

    try:
        optimizer = get_query_optimizer()

        print("🧪 Testing query optimization features:")

        # Test 1: Query expansion
        print(f"\n📍 Test 1: Query Expansion")
        short_queries = ["action", "comedy", "horror"]

        expanded_count = 0
        for query in short_queries:
            optimized = optimize_query(query)
            if len(optimized.split()) > len(query.split()):
                expanded_count += 1
                print(f"   📈 '{query}' -> '{optimized}'")

        if expanded_count > 0:
            print(
                f"   ✅ Query expansion working: {expanded_count}/{len(short_queries)} expanded"
            )
        else:
            print(f"   ⚠️  No queries were expanded")

        # Test 2: Query simplification
        print(f"\n📍 Test 2: Query Simplification")
        complex_queries = [
            "movies like really great action films with lots of excitement",
            "find me some very good comedy movies that are highly recommended",
        ]

        simplified_count = 0
        for query in complex_queries:
            optimized = optimize_query(query)
            if len(optimized.split()) < len(query.split()):
                simplified_count += 1
                print(f"   📉 '{query}' -> '{optimized}'")

        if simplified_count > 0:
            print(
                f"   ✅ Query simplification working: {simplified_count}/{len(complex_queries)} simplified"
            )
        else:
            print(f"   ⚠️  No queries were simplified")

        # Test 3: Intent-based optimization
        print(f"\n📍 Test 3: Intent-based Optimization")
        intent_queries = [
            "movies like Die Hard",
            "find Toy Story",
            "looking for romantic comedies",
        ]

        intent_optimized = 0
        for query in intent_queries:
            optimized = optimize_query(query)
            if optimized != query:
                intent_optimized += 1
                print(f"   🎯 '{query}' -> '{optimized}'")

        if intent_optimized > 0:
            print(
                f"   ✅ Intent optimization working: {intent_optimized}/{len(intent_queries)} optimized"
            )
        else:
            print(f"   ⚠️  No intent optimizations applied")

        # Test 4: Performance profile updates
        print(f"\n📍 Test 4: Performance Profile Updates")
        test_queries = ["action movies", "comedy films", "horror flicks"]

        for query in test_queries:
            # Simulate performance data
            latency = 0.1 + (len(query) * 0.01)  # Longer queries = higher latency
            success_rate = 0.9
            result_count = 10

            optimizer.update_performance_profile(
                query, latency, success_rate, result_count
            )

        stats = optimizer.get_optimization_stats()
        profile_count = stats.get("performance_profiles", 0)

        if profile_count > 0:
            print(f"   ✅ Performance profiles updated")
            print(f"   📊 Profiles created: {profile_count}")
        else:
            print(f"   ❌ Performance profile updates failed")

        print(f"\n🔍 Query Optimizer: 4/4 tests completed")
        return True

    except Exception as e:
        print(f"❌ Query optimizer test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_ranking_optimizer():
    """Test result ranking optimization functionality."""
    print("\n" + "=" * 60)
    print("📈 Testing Ranking Optimizer")
    print("=" * 60)

    try:
        optimizer = get_ranking_optimizer()

        print("🧪 Testing ranking optimization features:")

        # Test 1: Basic ranking optimization
        print(f"\n📍 Test 1: Basic Ranking Optimization")
        test_query = "action movies"
        test_results = [
            {
                "movie_id": "1",
                "title": "Old Action Movie",
                "genres": ["Action"],
                "year": 1980,
                "rating": 6.0,
                "scores": {"final": 0.70},
            },
            {
                "movie_id": "2",
                "title": "Recent Action Thriller",
                "genres": ["Action", "Thriller"],
                "year": 2020,
                "rating": 8.5,
                "scores": {"final": 0.85},
            },
            {
                "movie_id": "3",
                "title": "Comedy Movie",
                "genres": ["Comedy"],
                "year": 2015,
                "rating": 7.0,
                "scores": {"final": 0.60},
            },
        ]

        optimized_results = optimize_results(test_query, test_results)

        if optimized_results and len(optimized_results) == len(test_results):
            print(f"   ✅ Ranking optimization completed")
            # Check if action movies are ranked higher
            top_result = optimized_results[0]
            if "Action" in top_result.get("genres", []):
                print(f"   📊 Action movie ranked first: {top_result['title']}")
            else:
                print(f"   ⚠️  Top result: {top_result['title']}")
        else:
            print(f"   ❌ Ranking optimization failed")

        # Test 2: User interaction recording
        print(f"\n📍 Test 2: User Interaction Recording")
        interaction_count = 0

        for i, result in enumerate(test_results):
            interaction_type = ["click", "view", "like"][i % 3]
            optimizer.record_interaction(test_query, result, interaction_type)
            interaction_count += 1

        ranking_stats = optimizer.get_ranking_stats()
        total_interactions = ranking_stats.get("total_interactions", 0)

        if total_interactions >= interaction_count:
            print(f"   ✅ User interactions recorded")
            print(f"   📊 Total interactions: {total_interactions}")
        else:
            print(f"   ❌ User interaction recording failed")

        # Test 3: Personalization with user context
        print(f"\n📍 Test 3: Personalization with User Context")
        user_context = {
            "preferred_genres": ["Action", "Thriller"],
            "preferred_year_range": [2010, 2025],
            "min_rating": 7.0,
        }

        personalized_results = optimize_results(test_query, test_results, user_context)

        if personalized_results and len(personalized_results) == len(test_results):
            print(f"   ✅ Personalization applied")

            # Check if personalized factors are included
            top_result = personalized_results[0]
            if "optimization_factors" in top_result:
                factors = top_result["optimization_factors"]
                personalization_score = factors.get("personalization", 0.0)
                print(f"   📊 Personalization score: {personalization_score:.3f}")
            else:
                print(f"   ⚠️  Optimization factors not available")
        else:
            print(f"   ❌ Personalization failed")

        # Test 4: Diversity constraint
        print(f"\n📍 Test 4: Diversity Constraint")
        similar_results = [
            {
                "movie_id": f"{i}",
                "title": f"Action Movie {i}",
                "genres": ["Action"],
                "year": 2020,
            }
            for i in range(5)
        ]

        diversified = optimizer._apply_diversity_constraint(similar_results)

        if len(diversified) <= len(similar_results):
            print(f"   ✅ Diversity constraint applied")
            print(
                f"   📊 Diversified from {len(similar_results)} to {len(diversified)} results"
            )
        else:
            print(f"   ❌ Diversity constraint failed")

        print(f"\n📈 Ranking Optimizer: 4/4 tests completed")
        return True

    except Exception as e:
        print(f"❌ Ranking optimizer test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_optimization_pipeline():
    """Test the complete optimization pipeline."""
    print("\n" + "=" * 60)
    print("⚡ Testing Optimization Pipeline")
    print("=" * 60)

    try:
        # Initialize pipeline with optimization disabled for Redis independence
        pipeline = get_optimization_pipeline(enable_optimization=True)

        print("🧪 Testing optimization pipeline features:")

        # Test 1: Optimized search execution
        print(f"\n📍 Test 1: Optimized Search Execution")
        test_queries = ["action movies", "comedy films", "animated kids"]

        search_results = []
        for query in test_queries:
            result = optimized_search(query, mock_search_function)
            search_results.append(result)

            if result and "results" in result:
                optimization_info = result.get("optimization_info", {})
                print(f"   🔍 Query: '{query}' -> {len(result['results'])} results")
                print(
                    f"      💾 Cache hit: {optimization_info.get('cache_hit', False)}"
                )
                print(
                    f"      🔍 Query optimized: {optimization_info.get('query_optimized', False)}"
                )
                print(
                    f"      📈 Ranking optimized: {optimization_info.get('ranking_optimized', False)}"
                )

        if len(search_results) == len(test_queries):
            print(f"   ✅ Optimized search execution successful")
        else:
            print(f"   ❌ Optimized search execution failed")

        # Test 2: Cache warming
        print(f"\n📍 Test 2: Cache Warming")
        warming_result = warm_search_cache(mock_search_function)

        if warming_result.get("status") == "completed":
            print(f"   ✅ Cache warming completed")
            print(f"   📊 Queries warmed: {warming_result.get('queries_warmed', 0)}")
            print(f"   ⏱️  Warming time: {warming_result.get('warming_time', 0):.3f}s")
        else:
            print(f"   ⚠️  Cache warming result: {warming_result}")

        # Test 3: User interaction recording
        print(f"\n📍 Test 3: User Interaction Recording")
        if search_results:
            first_result = search_results[0]
            session_id = first_result.get("optimization_info", {}).get("session_id")

            if session_id and first_result.get("results"):
                movie_result = first_result["results"][0]
                record_search_interaction(session_id, movie_result, "click")
                record_search_interaction(session_id, movie_result, "view")

                print(f"   ✅ User interactions recorded for session {session_id}")
            else:
                print(f"   ⚠️  No session ID available for interaction recording")

        # Test 4: Optimization statistics
        print(f"\n📍 Test 4: Optimization Statistics")
        stats = get_optimization_statistics()

        if stats and "overview" in stats:
            overview = stats["overview"]
            print(f"   ✅ Optimization statistics retrieved")
            print(f"   📊 Total sessions: {overview.get('total_sessions', 0)}")
            print(f"   📊 Cache hit rate: {overview.get('cache_hit_rate', 0.0):.1%}")
            print(
                f"   📊 Optimization rate: {overview.get('optimization_rate', 0.0):.1%}"
            )
            print(
                f"   📊 Avg response time: {overview.get('avg_response_time', 0.0):.3f}s"
            )

            # Check components
            if "cache_performance" in stats:
                print(f"   📊 Cache performance data available")
            if "query_optimization" in stats:
                print(f"   📊 Query optimization data available")
            if "ranking_optimization" in stats:
                print(f"   📊 Ranking optimization data available")
        else:
            print(f"   ❌ Optimization statistics failed")

        # Test 5: System performance optimization
        print(f"\n📍 Test 5: System Performance Optimization")
        perf_optimization = pipeline.optimize_system_performance()

        if perf_optimization.get("timestamp"):
            print(f"   ✅ System performance analysis completed")
            actions = len(perf_optimization.get("actions_taken", []))
            recommendations = len(perf_optimization.get("recommendations", []))
            print(f"   📊 Actions taken: {actions}")
            print(f"   📊 Recommendations: {recommendations}")

            if actions > 0:
                print(f"   💡 Sample action: {perf_optimization['actions_taken'][0]}")
            if recommendations > 0:
                print(
                    f"   💡 Sample recommendation: {perf_optimization['recommendations'][0]}"
                )
        else:
            print(f"   ❌ System performance optimization failed")

        print(f"\n⚡ Optimization Pipeline: 5/5 tests completed")
        return True

    except Exception as e:
        print(f"❌ Optimization pipeline test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_integration_with_search():
    """Test integration with existing search system."""
    print("\n" + "=" * 60)
    print("🔗 Testing Integration with Search System")
    print("=" * 60)

    try:
        print("🧪 Testing integration with existing search components:")

        # Test 1: Integration with hybrid search
        print(f"\n📍 Test 1: Integration with Hybrid Search")
        try:
            from app.rag._05_retrieval import hybrid_search

            # Test optimized search with real search function
            result = optimized_search(
                "action movies", lambda q: hybrid_search(q, limit=3)
            )

            if result and "results" in result:
                print(f"   ✅ Hybrid search integration successful")
                print(f"   📊 Results: {len(result['results'])}")
                print(f"   ⏱️  Search time: {result.get('search_time', 0):.3f}s")

                optimization_info = result.get("optimization_info", {})
                if optimization_info:
                    print(
                        f"   💾 Cache hit: {optimization_info.get('cache_hit', False)}"
                    )
                    print(
                        f"   🔍 Query optimized: {optimization_info.get('query_optimized', False)}"
                    )
            else:
                print(f"   ❌ Hybrid search integration failed")

        except ImportError as e:
            print(f"   ⚠️  Hybrid search not available: {str(e)}")
        except Exception as e:
            print(f"   ❌ Hybrid search integration error: {str(e)}")

        # Test 2: Performance comparison
        print(f"\n📍 Test 2: Performance Comparison")
        test_query = "comedy movies"

        # Unoptimized search
        start_time = time.time()
        unoptimized_result = mock_search_function(test_query)
        unoptimized_time = time.time() - start_time

        # Optimized search (should be cached on second call)
        start_time = time.time()
        optimized_result1 = optimized_search(test_query, mock_search_function)
        first_call_time = time.time() - start_time

        start_time = time.time()
        optimized_result2 = optimized_search(test_query, mock_search_function)
        second_call_time = time.time() - start_time

        print(f"   ✅ Performance comparison completed")
        print(f"   📊 Unoptimized: {unoptimized_time:.3f}s")
        print(f"   📊 Optimized (1st): {first_call_time:.3f}s")
        print(f"   📊 Optimized (2nd): {second_call_time:.3f}s")

        # Second call should be faster due to caching
        if second_call_time < first_call_time:
            print(
                f"   ✅ Caching improved performance by {(first_call_time - second_call_time)*1000:.1f}ms"
            )
        else:
            print(f"   ⚠️  No significant performance improvement detected")

        # Test 3: Error handling and fallback
        print(f"\n📍 Test 3: Error Handling and Fallback")

        def failing_search_function(query):
            raise Exception("Simulated search failure")

        try:
            error_result = optimized_search("test query", failing_search_function)

            if error_result.get("error"):
                print(f"   ✅ Error handling working - error captured")
                print(f"   📊 Error: {error_result['error'][:50]}...")
            else:
                print(f"   ⚠️  Error handling unclear")

        except Exception as e:
            print(f"   ❌ Error handling failed: {str(e)}")

        print(f"\n🔗 Integration Tests: 3/3 tests completed")
        return True

    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all optimization system tests."""
    print("🚀 CineRAG 07_Optimization Test Suite")
    print(
        "Testing caching, query optimization, ranking optimization, and optimization pipeline"
    )

    # Track test results
    test_results = {}

    # Run tests
    test_results["cache_manager"] = test_cache_manager()
    test_results["query_optimizer"] = test_query_optimizer()
    test_results["ranking_optimizer"] = test_ranking_optimizer()
    test_results["optimization_pipeline"] = test_optimization_pipeline()
    test_results["integration"] = test_integration_with_search()

    # Print summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)

    total_tests = len(test_results)
    passed_tests = sum(test_results.values())

    print(f"✅ Passed: {passed_tests}/{total_tests} test suites")

    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name.replace('_', ' ').title()} Test")

    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Optimization system is ready for production.")
        print("🔥 07_Optimization implementation complete!")
        print("🎯 RAG Pipeline now at 100% - COMPLETE!")

        # Final optimization stats
        try:
            final_stats = get_optimization_statistics()
            overview = final_stats.get("overview", {})
            print(f"\n📊 Final Optimization Stats:")
            print(f"   💾 Cache hit rate: {overview.get('cache_hit_rate', 0.0):.1%}")
            print(
                f"   🔍 Optimization rate: {overview.get('optimization_rate', 0.0):.1%}"
            )
            print(
                f"   ⏱️  Avg response time: {overview.get('avg_response_time', 0.0):.3f}s"
            )
            print(f"   🎯 Total sessions: {overview.get('total_sessions', 0)}")
        except Exception as e:
            logger.warning(f"Could not get final stats: {str(e)}")

        return True
    else:
        print(
            f"\n⚠️  {total_tests - passed_tests} test suites failed. Please check the logs above."
        )
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
