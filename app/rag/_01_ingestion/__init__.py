"""
Data Ingestion Pipeline

This module handles data loading and preprocessing for the RAG system.
Includes MovieLens data loading and TMDB API integration.
"""

from .data_loader import MovieLensDataLoader, load_movielens_data
from .tmdb_service import TMDBService
from .ingestion_service import DataIngestionService

__all__ = [
    "MovieLensDataLoader",
    "load_movielens_data",
    "TMDBService",
    "DataIngestionService",
]
