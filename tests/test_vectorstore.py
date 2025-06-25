#!/usr/bin/env python3
"""
Test script for 03_VectorStore - Qdrant Integration

Tests Qdrant connection, embedding upload, and semantic search functionality.
"""

import os
import sys
import time
import logging

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.rag._03_vectorstore.qdrant_client import get_qdrant_manager
from app.rag._03_vectorstore.vector_operations import get_movie_vector_operations
from app.rag._03_vectorstore.semantic_search import get_semantic_search

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_qdrant_connection():
    """Test basic Qdrant connection."""
    print("\n" + "=" * 60)
    print("🔗 Testing Qdrant Connection")
    print("=" * 60)

    try:
        # Get Qdrant manager
        qdrant_manager = get_qdrant_manager()

        # Test connection
        connection_info = qdrant_manager.get_connection_info()
        print(f"✅ Connection Status: {connection_info}")

        # List existing collections
        collections = qdrant_manager.list_collections()
        print(f"📂 Existing Collections: {collections}")

        return qdrant_manager.is_connected

    except Exception as e:
        print(f"❌ Connection test failed: {str(e)}")
        return False


def test_embeddings_upload():
    """Test uploading movie embeddings to Qdrant."""
    print("\n" + "=" * 60)
    print("📤 Testing Embeddings Upload")
    print("=" * 60)

    try:
        # Get vector operations instance
        vector_ops = get_movie_vector_operations()

        # Check if embeddings file exists
        embeddings_path = "data/processed/embeddings/movie_embeddings.parquet"
        if not os.path.exists(embeddings_path):
            print(f"❌ Embeddings file not found: {embeddings_path}")
            print("   Please run the 02_embeddings pipeline first")
            return False

        print(f"📁 Found embeddings file: {embeddings_path}")

        # Upload embeddings
        print("🚀 Starting embeddings upload...")
        start_time = time.time()

        upload_result = vector_ops.upload_movie_embeddings(
            embeddings_path="data/processed/embeddings", batch_size=50
        )

        upload_time = time.time() - start_time

        if upload_result.get("success"):
            print(f"✅ Upload successful!")
            print(f"   - Total processed: {upload_result['total_processed']}")
            print(f"   - Successfully uploaded: {upload_result['uploaded_count']}")
            print(f"   - Failed: {upload_result['failed_count']}")
            print(f"   - Upload time: {upload_time:.2f} seconds")
            print(f"   - Collection info: {upload_result['collection_info']}")
            return True
        else:
            print(f"❌ Upload failed: {upload_result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"❌ Upload test failed: {str(e)}")
        return False


def test_semantic_search():
    """Test semantic search functionality."""
    print("\n" + "=" * 60)
    print("🔍 Testing Semantic Search")
    print("=" * 60)

    try:
        # Get semantic search instance
        semantic_search = get_semantic_search()

        # Test queries
        test_queries = [
            "animated movies for kids",
            "sci-fi space adventure",
            "romantic comedy",
            "dark thriller movie",
            "superhero action film",
        ]

        print("🎬 Testing various movie search queries:")

        for query in test_queries:
            print(f"\n🔎 Query: '{query}'")

            start_time = time.time()
            results = semantic_search.search_movies(
                query=query, limit=5, score_threshold=0.3
            )
            search_time = time.time() - start_time

            if results:
                print(f"   ✅ Found {len(results)} results in {search_time:.3f}s:")
                for i, result in enumerate(results[:3], 1):
                    print(
                        f"      {i}. {result['title']} ({result['genres']}) - Score: {result['similarity_score']:.3f}"
                    )
            else:
                print(f"   ❌ No results found")

        return len(results) > 0

    except Exception as e:
        print(f"❌ Semantic search test failed: {str(e)}")
        return False


def test_movie_similarity():
    """Test finding similar movies by movie ID."""
    print("\n" + "=" * 60)
    print("🎭 Testing Movie Similarity Search")
    print("=" * 60)

    try:
        # Get semantic search instance
        semantic_search = get_semantic_search()

        # Test with some popular movie IDs (assuming they exist in MovieLens dataset)
        test_movie_ids = [1, 2, 3, 5, 10]  # Common movie IDs

        for movie_id in test_movie_ids:
            print(f"\n🎬 Finding movies similar to movie ID {movie_id}:")

            start_time = time.time()
            similar_movies = semantic_search.find_similar_movies(
                movie_id=movie_id, limit=5
            )
            search_time = time.time() - start_time

            if similar_movies:
                print(
                    f"   ✅ Found {len(similar_movies)} similar movies in {search_time:.3f}s:"
                )
                for i, movie in enumerate(similar_movies[:3], 1):
                    print(
                        f"      {i}. {movie['title']} ({movie['genres']}) - Score: {movie['similarity_score']:.3f}"
                    )
                return True
            else:
                print(f"   ❌ No similar movies found for movie ID {movie_id}")

        return False

    except Exception as e:
        print(f"❌ Movie similarity test failed: {str(e)}")
        return False


def test_collection_stats():
    """Test getting collection statistics."""
    print("\n" + "=" * 60)
    print("📊 Testing Collection Statistics")
    print("=" * 60)

    try:
        # Get vector operations instance
        vector_ops = get_movie_vector_operations()

        # Get collection stats
        stats = vector_ops.get_collection_stats()

        print("📈 Collection Statistics:")
        print(f"   - Total movies: {stats.get('total_movies', 0)}")
        print(f"   - Collection info: {stats.get('collection_info', {})}")

        if stats.get("sample_movies"):
            print(f"   - Sample movies:")
            for movie in stats["sample_movies"][:5]:
                print(f"     • {movie['title']} ({movie['genres']})")

        # Get search system stats
        semantic_search = get_semantic_search()
        search_stats = semantic_search.get_search_stats()

        print("\n🔍 Search System Statistics:")
        print(
            f"   - Model: {search_stats.get('model_info', {}).get('model_name', 'Unknown')}"
        )
        print(
            f"   - Embedding dimension: {search_stats.get('model_info', {}).get('embedding_dimension', 'Unknown')}"
        )
        print(f"   - Capabilities: {search_stats.get('search_capabilities', {})}")

        return True

    except Exception as e:
        print(f"❌ Statistics test failed: {str(e)}")
        return False


def main():
    """Run all vector store tests."""
    print("🚀 CineRAG 03_VectorStore Test Suite")
    print("Testing Qdrant integration and semantic search functionality")

    # Track test results
    test_results = {}

    # Run tests
    test_results["connection"] = test_qdrant_connection()

    if test_results["connection"]:
        test_results["upload"] = test_embeddings_upload()
        test_results["search"] = test_semantic_search()
        test_results["similarity"] = test_movie_similarity()
        test_results["stats"] = test_collection_stats()
    else:
        print("\n❌ Skipping other tests due to connection failure")
        print("   Make sure Qdrant is running: docker compose up -d")
        return False

    # Print summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)

    total_tests = len(test_results)
    passed_tests = sum(test_results.values())

    print(f"✅ Passed: {passed_tests}/{total_tests} tests")

    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {test_name.title()} Test")

    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Vector store is ready for production.")
        print("🔥 03_VectorStore implementation complete!")
        return True
    else:
        print(
            f"\n⚠️  {total_tests - passed_tests} tests failed. Please check the logs above."
        )
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
