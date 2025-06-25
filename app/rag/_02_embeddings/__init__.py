"""
02_Embeddings - Vector Generation Module

Converts movie data into high-quality embeddings for semantic search.
Uses Sentence Transformers to generate normalized vector representations.
"""

from .text_preprocessor import MovieTextPreprocessor, create_text_preprocessor
from .embedding_generator import MovieEmbeddingGenerator, create_embedding_generator
from .pipeline import EmbeddingPipeline, run_embedding_pipeline

__all__ = [
    # Text preprocessing
    "MovieTextPreprocessor",
    "create_text_preprocessor",
    # Embedding generation
    "MovieEmbeddingGenerator",
    "create_embedding_generator",
    # Pipeline orchestration
    "EmbeddingPipeline",
    "run_embedding_pipeline",
]

# Version and metadata
__version__ = "1.0.0"
__author__ = "Dr. Jody-Ann S. Jones <jody@thedatasensei.com>"
__description__ = "Movie embedding generation using Sentence Transformers"
