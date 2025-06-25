"""
Embedding Generator for Movie Semantic Search

Uses Sentence Transformers to generate high-quality embeddings for movie data.
Handles batch processing, caching, and memory-efficient generation.
"""

import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import json
import pickle
from datetime import datetime
import torch

from sentence_transformers import SentenceTransformer
from .text_preprocessor import MovieTextPreprocessor, create_text_preprocessor

logger = logging.getLogger(__name__)


class MovieEmbeddingGenerator:
    """Generates embeddings for movie data using Sentence Transformers"""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        cache_dir: str = "data/cache/embeddings",
        device: Optional[str] = None,
    ):
        """
        Initialize embedding generator

        Args:
            model_name: Name of the sentence transformer model
            cache_dir: Directory for caching embeddings
            device: Device to use for computation ('cuda', 'cpu', or None for auto)
        """
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.text_preprocessor = create_text_preprocessor()
        self.model = None
        self.device = device

        # Statistics
        self.generation_stats = {
            "total_movies": 0,
            "embeddings_generated": 0,
            "cache_hits": 0,
            "processing_time": 0,
            "batch_count": 0,
        }

    def initialize_model(self) -> None:
        """Initialize the sentence transformer model"""
        if self.model is not None:
            return

        logger.info(f"Initializing Sentence Transformer model: {self.model_name}")

        try:
            # Set device
            if self.device is None:
                self.device = "cuda" if torch.cuda.is_available() else "cpu"

            logger.info(f"Using device: {self.device}")

            # Load model
            self.model = SentenceTransformer(self.model_name, device=self.device)

            # Log model info
            logger.info(f"Model loaded successfully")
            logger.info(
                f"Embedding dimension: {self.model.get_sentence_embedding_dimension()}"
            )
            logger.info(f"Max sequence length: {self.model.get_max_seq_length()}")

        except Exception as e:
            logger.error(f"Failed to initialize model {self.model_name}: {e}")
            raise

    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embeddings"""
        if self.model is None:
            self.initialize_model()
        return self.model.get_sentence_embedding_dimension()

    def generate_embeddings_batch(
        self, texts: List[str], batch_size: int = 32
    ) -> np.ndarray:
        """
        Generate embeddings for a batch of texts

        Args:
            texts: List of text strings to embed
            batch_size: Batch size for processing

        Returns:
            Array of embeddings (n_texts, embedding_dim)
        """
        if self.model is None:
            self.initialize_model()

        if not texts:
            return np.array([])

        logger.info(
            f"Generating embeddings for {len(texts)} texts in batches of {batch_size}"
        )

        try:
            # Generate embeddings
            start_time = datetime.now()
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=True,
                convert_to_numpy=True,
                normalize_embeddings=True,  # L2 normalization for better similarity
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            # Update statistics
            self.generation_stats["embeddings_generated"] += len(texts)
            self.generation_stats["processing_time"] += processing_time
            self.generation_stats["batch_count"] += 1

            logger.info(
                f"Generated {len(embeddings)} embeddings in {processing_time:.2f}s"
            )
            logger.info(f"Embedding shape: {embeddings.shape}")

            return embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def process_movie_dataframe(
        self,
        df: pd.DataFrame,
        batch_size: int = 32,
        use_cache: bool = True,
        save_embeddings: bool = True,
    ) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Process entire dataframe of movies to generate embeddings

        Args:
            df: DataFrame with movie data
            batch_size: Batch size for embedding generation
            use_cache: Whether to use cached embeddings
            save_embeddings: Whether to save embeddings to disk

        Returns:
            Tuple of (processed_dataframe, embeddings_array)
        """
        logger.info(f"Processing {len(df)} movies for embeddings...")
        start_time = datetime.now()

        # Initialize model
        if self.model is None:
            self.initialize_model()

        # Preprocess text data
        processed_df = self.text_preprocessor.preprocess_movie_dataframe(df)

        # Check for cached embeddings
        cache_file = (
            self.cache_dir
            / f"embeddings_{len(df)}_{self.model_name.replace('/', '_')}.pkl"
        )

        if use_cache and cache_file.exists():
            logger.info(f"Loading cached embeddings from {cache_file}")
            try:
                with open(cache_file, "rb") as f:
                    cached_data = pickle.load(f)
                    embeddings = cached_data["embeddings"]
                    self.generation_stats["cache_hits"] += len(df)
                    logger.info(f"Loaded {len(embeddings)} cached embeddings")
                    return processed_df, embeddings
            except Exception as e:
                logger.warning(f"Failed to load cached embeddings: {e}")

        # Generate embeddings for main text
        texts = processed_df["embedding_text"].tolist()
        embeddings = self.generate_embeddings_batch(texts, batch_size)

        # Add embedding info to dataframe
        processed_df["embedding_dimension"] = self.get_embedding_dimension()
        processed_df["embedding_model"] = self.model_name
        processed_df["embedding_timestamp"] = datetime.now().isoformat()

        # Save embeddings if requested
        if save_embeddings:
            self._save_embeddings_cache(embeddings, processed_df, cache_file)

        # Update statistics
        self.generation_stats["total_movies"] = len(df)
        total_time = (datetime.now() - start_time).total_seconds()
        self.generation_stats["processing_time"] = total_time

        logger.info(f"Completed embedding generation in {total_time:.2f}s")
        logger.info(f"Generated embeddings shape: {embeddings.shape}")

        return processed_df, embeddings

    def _save_embeddings_cache(
        self, embeddings: np.ndarray, df: pd.DataFrame, cache_file: Path
    ) -> None:
        """Save embeddings and metadata to cache"""
        try:
            cache_data = {
                "embeddings": embeddings,
                "model_name": self.model_name,
                "embedding_dimension": self.get_embedding_dimension(),
                "num_movies": len(df),
                "generation_timestamp": datetime.now().isoformat(),
                "movie_ids": df["movieId"].tolist() if "movieId" in df.columns else [],
            }

            with open(cache_file, "wb") as f:
                pickle.dump(cache_data, f)

            logger.info(f"Saved embeddings cache to {cache_file}")

        except Exception as e:
            logger.warning(f"Failed to save embeddings cache: {e}")

    def generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Generate embedding for a search query

        Args:
            query: Search query string

        Returns:
            Query embedding vector
        """
        if self.model is None:
            self.initialize_model()

        # Clean query text
        cleaned_query = self.text_preprocessor.clean_text(query)

        if not cleaned_query:
            logger.warning("Empty query after cleaning")
            return np.zeros(self.get_embedding_dimension())

        # Generate embedding
        embedding = self.model.encode(
            [cleaned_query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )[0]

        return embedding

    def compute_similarities(
        self, query_embedding: np.ndarray, movie_embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Compute cosine similarities between query and movie embeddings

        Args:
            query_embedding: Query embedding vector
            movie_embeddings: Array of movie embeddings

        Returns:
            Array of similarity scores
        """
        # Ensure query embedding is 2D
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)

        # Compute cosine similarity (embeddings are already normalized)
        similarities = np.dot(movie_embeddings, query_embedding.T).flatten()

        return similarities

    def get_generation_stats(self) -> Dict[str, Any]:
        """Get embedding generation statistics"""
        stats = self.generation_stats.copy()

        if stats["processing_time"] > 0:
            stats["embeddings_per_second"] = (
                stats["embeddings_generated"] / stats["processing_time"]
            )
        else:
            stats["embeddings_per_second"] = 0

        return stats

    def save_embeddings_to_file(
        self,
        embeddings: np.ndarray,
        df: pd.DataFrame,
        output_path: str,
        format: str = "numpy",
    ) -> None:
        """
        Save embeddings to file in various formats

        Args:
            embeddings: Embeddings array
            df: Associated dataframe
            output_path: Output file path
            format: Output format ('numpy', 'parquet', 'json')
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if format == "numpy":
                np.save(output_path, embeddings)
                # Save metadata
                metadata = {
                    "model_name": self.model_name,
                    "embedding_dimension": self.get_embedding_dimension(),
                    "num_embeddings": len(embeddings),
                    "movie_ids": (
                        df["movieId"].tolist() if "movieId" in df.columns else []
                    ),
                    "generation_timestamp": datetime.now().isoformat(),
                }
                with open(output_path.with_suffix(".json"), "w") as f:
                    json.dump(metadata, f, indent=2)

            elif format == "parquet":
                # Create DataFrame with embeddings
                embedding_df = pd.DataFrame(
                    embeddings, columns=[f"emb_{i}" for i in range(embeddings.shape[1])]
                )

                # Add movie metadata
                if "movieId" in df.columns:
                    embedding_df["movieId"] = df["movieId"].values

                embedding_df.to_parquet(output_path)

            else:
                raise ValueError(f"Unsupported format: {format}")

            logger.info(f"Saved embeddings to {output_path} in {format} format")

        except Exception as e:
            logger.error(f"Failed to save embeddings: {e}")
            raise


def create_embedding_generator(
    model_name: str = "all-MiniLM-L6-v2",
    cache_dir: str = "data/cache/embeddings",
    device: Optional[str] = None,
) -> MovieEmbeddingGenerator:
    """Factory function to create embedding generator"""
    return MovieEmbeddingGenerator(model_name, cache_dir, device)


# Testing and example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Test with sample data
    sample_df = pd.DataFrame(
        [
            {
                "movieId": 1,
                "clean_title": "Toy Story",
                "year": 1995,
                "genres_list": "['Adventure', 'Animation', 'Children', 'Comedy', 'Fantasy']",
                "avg_rating": 3.92,
                "num_ratings": 215,
                "popularity_score": 21.07,
            },
            {
                "movieId": 2,
                "clean_title": "Jumanji",
                "year": 1995,
                "genres_list": "['Adventure', 'Children', 'Fantasy']",
                "avg_rating": 3.43,
                "num_ratings": 110,
                "popularity_score": 16.15,
            },
        ]
    )

    # Generate embeddings
    generator = create_embedding_generator()
    processed_df, embeddings = generator.process_movie_dataframe(
        sample_df, batch_size=2
    )

    print(f"Generated embeddings shape: {embeddings.shape}")
    print(f"Sample embedding text: {processed_df['embedding_text'].iloc[0]}")

    # Test query embedding
    query_embedding = generator.generate_query_embedding("animated toy movie")
    similarities = generator.compute_similarities(query_embedding, embeddings)
    print(f"Query similarities: {similarities}")
