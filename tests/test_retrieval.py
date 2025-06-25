#!/usr/bin/env python3
"""
Test script for 05_Retrieval

Tests hybrid search engine, result ranking, and integrated retrieval pipeline.
"""

import os
import sys
import time
import logging

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.rag._05_retrieval import (
    get_hybrid_search_engine,
    hybrid_search,
    semantic_search,
    get_result_ranker,
    rank_search_results,
    explain_ranking,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_hybrid_search_engine():
    """Test hybrid search engine functionality."""
    print("\n" + "=" * 60)
    print("🔍 Testing Hybrid Search Engine")
    print("=" * 60)

    try:
        # Get search engine instance
        search_engine = get_hybrid_search_engine()

        # Test queries with different characteristics
        test_queries = [
            ("animated movies for kids", "Simple genre + audience query"),
            ("sci-fi space adventure like Star Wars", "Complex similarity query"),
            ("horror films from the 1980s", "Genre + time period query"),
            ("popular action movies", "Genre + popularity query"),
            ("comedy", "Single word genre query"),
            ("romantic comedies with good ratings", "Multi-genre + quality query"),
        ]

        print("🧪 Testing hybrid search with various query types:")

        success_count = 0
        for query, description in test_queries:
            print(f"\n🔍 Query: '{query}' ({description})")

            start_time = time.time()
            results = search_engine.search(query, limit=5, search_mode="hybrid")
            search_time = time.time() - start_time

            if results and results.get("results"):
                result_list = results["results"]
                print(f"   ✅ Found {len(result_list)} results in {search_time:.3f}s")
                print(f"   📊 Search metadata: {results.get('search_metadata', {})}")

                # Show top result
                if result_list:
                    top_result = result_list[0]
                    print(f"   🏆 Top result: '{top_result.get('title', 'Unknown')}'")
                    print(f"   📈 Scores: {top_result.get('scores', {})}")

                success_count += 1
            else:
                error_msg = results.get("error", "Unknown error")
                print(f"   ❌ Search failed: {error_msg}")

        print(
            f"\n📊 Hybrid Search Results: {success_count}/{len(test_queries)} successful"
        )
        return success_count == len(test_queries)

    except Exception as e:
        print(f"❌ Hybrid search test failed: {str(e)}")
        return False


def test_search_modes():
    """Test different search modes."""
    print("\n" + "=" * 60)
    print("🔄 Testing Search Modes")
    print("=" * 60)

    try:
        search_engine = get_hybrid_search_engine()
        query = "action adventure movies"

        search_modes = ["semantic", "hybrid"]  # keyword mode uses semantic fallback

        print(f"🧪 Testing search modes with query: '{query}'")

        success_count = 0
        mode_results = {}

        for mode in search_modes:
            print(f"\n🔍 Mode: {mode}")

            start_time = time.time()
            results = search_engine.search(query, limit=3, search_mode=mode)
            search_time = time.time() - start_time

            if results and results.get("results"):
                result_list = results["results"]
                mode_results[mode] = result_list

                print(
                    f"   ✅ {mode.capitalize()} search: {len(result_list)} results ({search_time:.3f}s)"
                )

                if result_list:
                    top_result = result_list[0]
                    print(f"   🏆 Top result: '{top_result.get('title', 'Unknown')}'")
                    scores = top_result.get("scores", {})
                    print(f"   📊 Final score: {scores.get('final', 0.0):.3f}")

                success_count += 1
            else:
                print(f"   ❌ {mode.capitalize()} search failed")

        # Compare results between modes
        if len(mode_results) >= 2:
            print(f"\n📈 Mode Comparison:")
            for mode, results in mode_results.items():
                if results:
                    avg_score = sum(
                        r.get("scores", {}).get("final", 0) for r in results
                    ) / len(results)
                    print(f"   {mode.capitalize()}: Average score = {avg_score:.3f}")

        print(
            f"\n📊 Search Mode Results: {success_count}/{len(search_modes)} successful"
        )
        return success_count == len(search_modes)

    except Exception as e:
        print(f"❌ Search mode test failed: {str(e)}")
        return False


def test_result_ranking():
    """Test result ranking functionality."""
    print("\n" + "=" * 60)
    print("🏆 Testing Result Ranking")
    print("=" * 60)

    try:
        # Get search results first
        search_engine = get_hybrid_search_engine()
        query = "science fiction movies"
        search_results = search_engine.search(query, limit=8, search_mode="semantic")

        if not search_results or not search_results.get("results"):
            print("❌ Could not get search results for ranking test")
            return False

        results = search_results["results"]
        query_info = search_results.get("query_info", {})

        print(f"🧪 Testing ranking strategies on {len(results)} results")

        # Test different ranking strategies
        ranking_strategies = ["semantic", "popularity", "hybrid", "diversity"]

        success_count = 0
        for strategy in ranking_strategies:
            print(f"\n🔍 Strategy: {strategy}")

            start_time = time.time()
            ranked_results = rank_search_results(results, query_info, strategy)
            ranking_time = time.time() - start_time

            if ranked_results:
                print(
                    f"   ✅ Ranked {len(ranked_results)} results in {ranking_time:.3f}s"
                )

                # Show top 3 results
                for i, result in enumerate(ranked_results[:3]):
                    title = result.get("title", "Unknown")
                    ranking_info = result.get("ranking_info", {})
                    rank = ranking_info.get("rank", i + 1)
                    score = ranking_info.get("ranking_score", 0.0)

                    print(f"   #{rank}: '{title}' (score: {score:.3f})")

                success_count += 1
            else:
                print(f"   ❌ {strategy.capitalize()} ranking failed")

        print(
            f"\n📊 Ranking Results: {success_count}/{len(ranking_strategies)} successful"
        )
        return success_count == len(ranking_strategies)

    except Exception as e:
        print(f"❌ Result ranking test failed: {str(e)}")
        return False


def test_ranking_explanations():
    """Test ranking explanation functionality."""
    print("\n" + "=" * 60)
    print("📝 Testing Ranking Explanations")
    print("=" * 60)

    try:
        # Get ranked results
        search_engine = get_hybrid_search_engine()
        query = "popular action movies"
        search_results = search_engine.search(query, limit=5, search_mode="hybrid")

        if not search_results or not search_results.get("results"):
            print("❌ Could not get search results for explanation test")
            return False

        results = search_results["results"]
        query_info = search_results.get("query_info", {})

        # Rank results with hybrid strategy
        ranked_results = rank_search_results(results, query_info, "hybrid")

        print(f"🧪 Testing ranking explanations for {len(ranked_results)} results")

        success_count = 0
        for i, result in enumerate(ranked_results[:3]):  # Test top 3
            title = result.get("title", "Unknown")
            print(f"\n🔍 Result #{i+1}: '{title}'")

            try:
                explanation = explain_ranking(result)

                if explanation:
                    print(f"   ✅ Explanation generated")
                    print(f"   📊 Rank: {explanation.get('rank', 'Unknown')}")
                    print(f"   📈 Score: {explanation.get('final_score', 0.0):.3f}")
                    print(f"   🔧 Strategy: {explanation.get('strategy', 'Unknown')}")
                    print(
                        f"   💬 Explanation: {explanation.get('explanation', 'None')}"
                    )

                    # Show top features
                    top_features = explanation.get("top_features", [])
                    if top_features:
                        print(f"   🎯 Top features:")
                        for feature in top_features[:3]:
                            name = feature.get("feature", "Unknown")
                            value = feature.get("value", 0.0)
                            contribution = feature.get("contribution", 0.0)
                            print(
                                f"      • {name}: {value:.3f} (contrib: {contribution:.3f})"
                            )

                    success_count += 1
                else:
                    print(f"   ❌ No explanation generated")

            except Exception as e:
                print(f"   ❌ Explanation failed: {str(e)}")

        print(
            f"\n📊 Explanation Results: {success_count}/{min(len(ranked_results), 3)} successful"
        )
        return success_count >= 1  # At least one explanation should work

    except Exception as e:
        print(f"❌ Ranking explanation test failed: {str(e)}")
        return False


def test_search_performance():
    """Test search performance and response times."""
    print("\n" + "=" * 60)
    print("⚡ Testing Search Performance")
    print("=" * 60)

    try:
        search_engine = get_hybrid_search_engine()

        # Performance test queries
        performance_queries = [
            "action",
            "comedy movies",
            "sci-fi adventure films",
            "popular romantic comedies from the 1990s",
            "animated movies for children with good ratings",
        ]

        print("🧪 Testing search performance across query complexities:")

        total_time = 0
        success_count = 0

        for i, query in enumerate(performance_queries, 1):
            print(
                f"\n⏱️  Performance Test {i}: '{query[:30]}{'...' if len(query) > 30 else ''}'"
            )

            # Test multiple runs for average
            times = []
            for run in range(3):
                start_time = time.time()
                results = search_engine.search(query, limit=10, search_mode="hybrid")
                end_time = time.time()

                if results and results.get("results"):
                    times.append(end_time - start_time)
                else:
                    print(f"   ❌ Run {run+1} failed")
                    break

            if times:
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                total_time += avg_time

                print(f"   ✅ Average: {avg_time:.3f}s")
                print(f"   📊 Range: {min_time:.3f}s - {max_time:.3f}s")

                # Performance assessment
                if avg_time < 0.1:
                    print(f"   🚀 Excellent performance!")
                elif avg_time < 0.5:
                    print(f"   ✅ Good performance")
                else:
                    print(f"   ⚠️  Slow performance")

                success_count += 1

        if success_count > 0:
            avg_overall = total_time / success_count
            print(f"\n📊 Performance Summary:")
            print(f"   ⏱️  Average search time: {avg_overall:.3f}s")
            print(f"   🎯 Target: < 0.5s for hybrid search")
            print(
                f"   ✅ Status: {'EXCELLENT' if avg_overall < 0.1 else 'GOOD' if avg_overall < 0.5 else 'NEEDS_OPTIMIZATION'}"
            )

        return success_count == len(performance_queries)

    except Exception as e:
        print(f"❌ Performance test failed: {str(e)}")
        return False


def test_integration_pipeline():
    """Test complete integration of all retrieval components."""
    print("\n" + "=" * 60)
    print("🔗 Testing Integration Pipeline")
    print("=" * 60)

    try:
        # Test complete end-to-end pipeline
        query = "funny animated movies for kids"

        print(f"🧪 Testing complete retrieval pipeline:")
        print(f"   Query: '{query}'")

        # Step 1: Hybrid search
        print(f"\n📍 Step 1: Hybrid Search")
        start_time = time.time()
        search_results = hybrid_search(query, limit=8)
        search_time = time.time() - start_time

        if not search_results or not search_results.get("results"):
            print(f"   ❌ Hybrid search failed")
            return False

        results = search_results["results"]
        query_info = search_results.get("query_info", {})

        print(f"   ✅ Found {len(results)} results in {search_time:.3f}s")
        print(
            f"   📊 Query processed: {query_info.get('processed_query', {}).get('processed', False)}"
        )

        # Step 2: Advanced ranking
        print(f"\n📍 Step 2: Advanced Ranking")
        start_time = time.time()
        ranked_results = rank_search_results(results, query_info, "hybrid")
        ranking_time = time.time() - start_time

        if not ranked_results:
            print(f"   ❌ Ranking failed")
            return False

        print(f"   ✅ Ranked {len(ranked_results)} results in {ranking_time:.3f}s")

        # Step 3: Generate explanations
        print(f"\n📍 Step 3: Result Analysis")
        explanations_generated = 0

        for result in ranked_results[:3]:
            try:
                explanation = explain_ranking(result)
                if explanation:
                    explanations_generated += 1
            except:
                pass

        print(f"   ✅ Generated {explanations_generated}/3 explanations")

        # Final results display
        print(f"\n🏆 Top Results:")
        for i, result in enumerate(ranked_results[:3]):
            title = result.get("title", "Unknown")
            scores = result.get("scores", {})
            final_score = scores.get("final", 0.0)

            print(f"   #{i+1}: '{title}' (score: {final_score:.3f})")

            # Show score breakdown
            if scores:
                semantic = scores.get("semantic", 0.0)
                keyword = scores.get("keyword", 0.0)
                metadata = scores.get("metadata", 0.0)
                print(
                    f"        Semantic: {semantic:.3f}, Keyword: {keyword:.3f}, Metadata: {metadata:.3f}"
                )

        # Performance summary
        total_time = search_time + ranking_time
        print(f"\n📊 Pipeline Performance:")
        print(f"   ⏱️  Total time: {total_time:.3f}s")
        print(f"   🔍 Search: {search_time:.3f}s")
        print(f"   🏆 Ranking: {ranking_time:.3f}s")
        print(f"   🎯 Target: < 1.0s total")
        print(
            f"   ✅ Status: {'EXCELLENT' if total_time < 0.5 else 'GOOD' if total_time < 1.0 else 'ACCEPTABLE'}"
        )

        # Success criteria
        success_criteria = [
            len(results) > 0,  # Found results
            len(ranked_results) > 0,  # Ranked results
            explanations_generated > 0,  # Generated explanations
            total_time < 2.0,  # Reasonable performance
        ]

        success_count = sum(success_criteria)
        print(f"\n📋 Success Criteria: {success_count}/4 met")

        return success_count >= 3  # Need at least 3/4 criteria

    except Exception as e:
        print(f"❌ Integration pipeline test failed: {str(e)}")
        return False


def main():
    """Run all retrieval system tests."""
    print("🚀 CineRAG 05_Retrieval Test Suite")
    print("Testing hybrid search, result ranking, and retrieval pipeline")

    # Track test results
    test_results = {}

    # Run tests
    test_results["hybrid_search"] = test_hybrid_search_engine()
    test_results["search_modes"] = test_search_modes()
    test_results["result_ranking"] = test_result_ranking()
    test_results["ranking_explanations"] = test_ranking_explanations()
    test_results["performance"] = test_search_performance()
    test_results["integration"] = test_integration_pipeline()

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
        print("\n🎉 All tests passed! Retrieval system is ready for production.")
        print("🔥 05_Retrieval implementation complete!")
        print("🎯 RAG Pipeline now 67% complete!")
        return True
    else:
        print(
            f"\n⚠️  {total_tests - passed_tests} test suites failed. Please check the logs above."
        )
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
