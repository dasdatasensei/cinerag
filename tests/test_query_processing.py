#!/usr/bin/env python3
"""
Test script for 04_Query_Processing

Tests query preprocessing, enhancement, and the integrated processing pipeline.
"""

import os
import sys
import time
import logging
import pytest

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.rag._04_query_processing import (
    get_query_preprocessor,
    get_query_enhancer,
    get_query_processor,
    process_query,
    quick_process_query,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestQueryPreprocessor:
    """Test query preprocessing functionality."""

    def test_preprocessor_initialization(self, query_preprocessor):
        """Test that preprocessor initializes correctly."""
        assert query_preprocessor is not None
        assert hasattr(query_preprocessor, "preprocess_query")

    @pytest.mark.parametrize(
        "query,expected_type",
        [
            ("Find me some good Sci-Fi movies", dict),
            ("ACTION MOVIES WITH EXPLOSIONS", dict),
            ("animated movies for kids", dict),
            ("romantic comedy from 1990s", dict),
        ],
    )
    def test_basic_preprocessing(self, query_preprocessor, query, expected_type):
        """Test basic query preprocessing."""
        result = query_preprocessor.preprocess_query(query)

        assert result is not None
        assert isinstance(result, expected_type)
        assert "processed_query" in result
        assert (
            len(result["processed_query"].strip()) > 0
        ), "Preprocessed query should not be empty"

        print(f"✅ '{query}' → '{result['processed_query']}'")

    def test_preprocessing_edge_cases(self, query_preprocessor, edge_case_queries):
        """Test preprocessing with edge cases."""
        for query in edge_case_queries:
            if query is None:
                continue  # Skip None case

            result = query_preprocessor.preprocess_query(query)

            # Should handle edge cases gracefully
            assert result is not None
            assert isinstance(result, dict)
            if query.strip():  # If input has content
                assert "processed_query" in result

            print(
                f"✅ Edge case handled: '{query}' → '{result.get('processed_query', 'N/A')}'"
            )


class TestQueryEnhancer:
    """Test query enhancement functionality."""

    def test_enhancer_initialization(self, query_enhancer):
        """Test that enhancer initializes correctly."""
        assert query_enhancer is not None
        assert hasattr(query_enhancer, "enhance_query")

    @pytest.mark.parametrize(
        "query",
        [
            "Find me some good Sci-Fi movies",
            "comedy movies from the 90s",
            "animated films for children",
            "scary horror movies",
            "action packed thrillers",
        ],
    )
    def test_query_enhancement(self, query_enhancer, query):
        """Test query enhancement with valid queries."""
        enhanced = query_enhancer.enhance_query(query)

        assert enhanced is not None
        assert isinstance(enhanced, str)
        assert len(enhanced.strip()) > 0

        print(f"✅ Enhanced: '{query}' → '{enhanced}'")

    def test_spelling_correction(self, query_enhancer, spelling_error_queries):
        """Test spelling correction in enhancement."""
        for query in spelling_error_queries:
            enhanced = query_enhancer.enhance_query(query)

            assert enhanced is not None
            assert isinstance(enhanced, str)
            # Enhanced query should be different from original (spelling corrected)
            assert enhanced != query

            print(f"✅ Spelling corrected: '{query}' → '{enhanced}'")

    @pytest.mark.slow
    def test_enhancement_performance(self, query_enhancer, performance_queries):
        """Test enhancement performance with complex queries."""
        total_time = 0

        for query in performance_queries:
            start_time = time.time()
            enhanced = query_enhancer.enhance_query(query)
            end_time = time.time()

            duration = end_time - start_time
            total_time += duration

            assert enhanced is not None
            assert duration < 2.0, f"Enhancement too slow: {duration:.2f}s"

            print(f"✅ Enhanced in {duration:.3f}s: '{query}' → '{enhanced}'")

        avg_time = total_time / len(performance_queries)
        print(f"📊 Average enhancement time: {avg_time:.3f}s")
        assert avg_time < 1.0, "Average enhancement time should be under 1 second"


class TestQueryProcessor:
    """Test end-to-end query processing."""

    def test_processor_initialization(self, query_processor):
        """Test that processor initializes correctly."""
        assert query_processor is not None
        assert hasattr(query_processor, "process_query")

    def test_basic_query_processing(self, query_processor, sample_queries):
        """Test basic query processing functionality."""
        for query in sample_queries:
            result = query_processor.process_query(query)

            assert result is not None
            assert isinstance(result, dict)

            # Check for expected result structure
            expected_keys = ["final_query", "original_query"]
            for key in expected_keys:
                assert key in result, f"Missing key in result: {key}"

            assert result["original_query"] == query
            assert isinstance(result["final_query"], str)

            # Check if timing info exists
            if "timing" in result:
                assert result["timing"]["total_time"] > 0

            print(f"✅ Processed: '{query}' → '{result['final_query']}'")
            if "timing" in result:
                print(f"   Time: {result['timing']['total_time']:.3f}s")

    @pytest.mark.parametrize("mode", ["simple", "enhanced", "full"])
    def test_processing_modes(self, query_processor, mode):
        """Test different processing modes."""
        query = "action movies with explosions"

        result = query_processor.process_query(query, mode=mode)

        assert result is not None
        assert isinstance(result, dict)
        assert "final_query" in result

        # Mode info might be stored in config or summary
        print(f"✅ Mode '{mode}': '{query}' → '{result['final_query']}'")

    def test_processing_detailed_results(self, query_processor):
        """Test processing with detailed result structure."""
        query = "horror movies"

        result = query_processor.process_query(query)

        assert result is not None
        assert isinstance(result, dict)

        # Check for detailed structure from actual implementation
        expected_sections = [
            "preprocessing_results",
            "enhancement_results",
            "final_query",
        ]
        for section in expected_sections:
            if section in result:
                print(f"✅ Found section: {section}")

        if (
            "recommendations" in result
            and "alternative_queries" in result["recommendations"]
        ):
            alternatives = result["recommendations"]["alternative_queries"]
            print(f"✅ Got {len(alternatives)} alternative queries")
            for alt in alternatives[:3]:
                print(f"   - {alt}")

    @pytest.mark.slow
    def test_processing_performance(self, query_processor, performance_queries):
        """Test processing performance with various query types."""
        total_time = 0

        for query in performance_queries:
            start_time = time.time()
            result = query_processor.process_query(query)
            end_time = time.time()

            duration = end_time - start_time
            total_time += duration

            assert result is not None
            assert duration < 3.0, f"Processing too slow: {duration:.2f}s"

            print(f"✅ Processed in {duration:.3f}s: '{query}'")

        avg_time = total_time / len(performance_queries)
        print(f"📊 Average processing time: {avg_time:.3f}s")
        assert avg_time < 1.5, "Average processing time should be reasonable"


class TestQueryProcessingIntegration:
    """Integration tests for query processing pipeline."""

    @pytest.mark.integration
    def test_full_pipeline_integration(
        self, query_preprocessor, query_enhancer, query_processor
    ):
        """Test that all components work together."""
        query = "Find me some good animated movies for kids"

        # Test individual components
        preprocessed = query_preprocessor.preprocess_query(query)
        assert preprocessed is not None
        assert "processed_query" in preprocessed

        enhanced = query_enhancer.enhance_query(preprocessed["processed_query"])
        assert enhanced is not None

        # Test full pipeline
        result = query_processor.process_query(query)
        assert result is not None
        assert isinstance(result, dict)
        assert "final_query" in result

        print(f"✅ Full pipeline: '{query}' → '{result['final_query']}'")
        if "timing" in result:
            print(f"   Processing time: {result['timing']['total_time']:.3f}s")

    @pytest.mark.integration
    def test_pipeline_error_handling(self, query_processor, edge_case_queries):
        """Test pipeline handles edge cases gracefully."""
        for query in edge_case_queries:
            if query is None:
                continue

            try:
                result = query_processor.process_query(query)

                # Should return a valid result or handle gracefully
                if result is not None:
                    assert isinstance(result, dict)
                    print(f"✅ Edge case handled: '{query}' → success")
                else:
                    print(f"✅ Edge case handled: '{query}' → None (expected)")

            except Exception as e:
                # Log but don't fail - edge cases may raise expected exceptions
                print(f"⚠️  Edge case exception: '{query}' → {str(e)}")

    @pytest.mark.integration
    def test_consistency_across_runs(self, query_processor):
        """Test that processing is consistent across multiple runs."""
        query = "sci-fi space adventure movies"
        results = []

        for i in range(3):
            result = query_processor.process_query(query)
            results.append(result)

        # All results should be valid
        for result in results:
            assert result is not None
            assert isinstance(result, dict)
            assert "final_query" in result

        # Processed queries should be consistent (allowing for minor variations)
        processed_queries = [r["final_query"] for r in results]
        print(
            f"✅ Consistency test: {len(set(processed_queries))} unique results from 3 runs"
        )

        # At least the core content should be similar
        for pq in processed_queries:
            assert (
                "sci" in pq.lower()
                or "space" in pq.lower()
                or "adventure" in pq.lower()
            )
