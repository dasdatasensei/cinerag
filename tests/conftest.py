"""
Pytest configuration and shared fixtures for CineRAG tests.
"""

import os
import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from config/.env
env_path = project_root / "config" / ".env"
if env_path.exists():
    load_dotenv(env_path)


@pytest.fixture(scope="session")
def project_root_path():
    """Get the project root path."""
    return project_root


@pytest.fixture(scope="session")
def data_loader():
    """Get MovieLens data loader instance."""
    from app.rag._01_ingestion.data_loader import MovieLensDataLoader

    return MovieLensDataLoader()


@pytest.fixture(scope="session")
def tmdb_service():
    """Get TMDB service instance."""
    from app.rag._01_ingestion.tmdb_service import TMDBService

    return TMDBService()


@pytest.fixture(scope="session")
def query_preprocessor():
    """Get query preprocessor instance."""
    from app.rag._04_query_processing import get_query_preprocessor

    return get_query_preprocessor()


@pytest.fixture(scope="session")
def query_enhancer():
    """Get query enhancer instance."""
    from app.rag._04_query_processing import get_query_enhancer

    return get_query_enhancer()


@pytest.fixture(scope="session")
def query_processor():
    """Get query processor instance."""
    from app.rag._04_query_processing import get_query_processor

    return get_query_processor()


@pytest.fixture(scope="session")
def recommendation_service():
    """Get recommendation service instance."""
    from app.rag._05_retrieval.recommendation_service import RecommendationService

    return RecommendationService()


@pytest.fixture
def chat_service():
    """Create a ChatService instance for testing."""
    from app.rag._04_query_processing.chat_service import ChatService

    return ChatService()


@pytest.fixture
def client():
    """Create a test client for API endpoint testing."""
    from starlette.testclient import TestClient
    from app.main import app

    return TestClient(app)


# Test data fixtures
@pytest.fixture
def sample_queries():
    """Sample queries for testing."""
    return [
        "Find me some good Sci-Fi movies like Star Wars",
        "I want funny comedies from the 1990s",
        "Show me scary horror films",
        "animated movies for kids",
        "action thriller movies",
    ]


@pytest.fixture
def spelling_error_queries():
    """Queries with spelling errors for testing enhancement."""
    return ["commedy movei", "scifi filems", "horrer films", "acton movies"]


@pytest.fixture
def edge_case_queries():
    """Edge case queries for testing error handling."""
    return ["", "   ", "a", "123", "!@#$%", "x" * 600, None]


# Performance testing fixtures
@pytest.fixture
def performance_queries():
    """Complex queries for performance testing."""
    return [
        "action movies",
        "romantic comedy films from the 1990s",
        "animated movies for kids with good animation",
        "sci-fi space adventure movies like Star Wars with great special effects",
    ]


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")


def pytest_collection_modifyitems(config, items):
    """Modify test items during collection."""
    # Add markers to tests based on their names/paths
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "performance" in item.name:
            item.add_marker(pytest.mark.slow)
        else:
            item.add_marker(pytest.mark.unit)
