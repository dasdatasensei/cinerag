"""
Embedding Pipeline

Main orchestration module for the embedding generation process.
Coordinates text preprocessing, model initialization, and embedding generation.
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional, Any
import json
from datetime import datetime

from .text_preprocessor import create_text_preprocessor
from .embedding_generator import create_embedding_generator

logger = logging.getLogger(__name__)


class EmbeddingPipeline:
    """Complete embedding generation pipeline"""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        cache_dir: str = "data/cache/embeddings",
        output_dir: str = "data/processed/embeddings",
        log_dir: str = "data/logs",
        device: Optional[str] = None,
    ):
        """
        Initialize embedding pipeline

        Args:
            model_name: Sentence transformer model name
            cache_dir: Directory for caching
            output_dir: Directory for outputs
            log_dir: Directory for logs
            device: Device for model computation
        """
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.output_dir = Path(output_dir)
        self.log_dir = Path(log_dir)

        # Create directories
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.text_preprocessor = create_text_preprocessor()
        self.embedding_generator = create_embedding_generator(
            model_name=model_name, cache_dir=str(cache_dir), device=device
        )

        # Pipeline state
        self.processed_df = None
        self.embeddings = None
        self.pipeline_report = None

    def run_pipeline(
        self,
        input_data: pd.DataFrame,
        batch_size: int = 32,
        use_cache: bool = True,
        save_outputs: bool = True,
        validate_embeddings: bool = True,
    ) -> Dict[str, Any]:
        """
        Run complete embedding pipeline

        Args:
            input_data: DataFrame with movie data
            batch_size: Batch size for embedding generation
            use_cache: Whether to use cached embeddings
            save_outputs: Whether to save outputs
            validate_embeddings: Whether to validate generated embeddings

        Returns:
            Pipeline execution report
        """
        logger.info("Starting embedding generation pipeline...")
        start_time = datetime.now()

        pipeline_report = {
            "status": "RUNNING",
            "stages_completed": [],
            "errors": [],
            "statistics": {},
            "start_time": start_time.isoformat(),
        }

        try:
            # Stage 1: Text Preprocessing
            logger.info("Stage 1: Text preprocessing...")
            self._stage_text_preprocessing(input_data, pipeline_report)

            # Stage 2: Embedding Generation
            logger.info("Stage 2: Embedding generation...")
            self._stage_embedding_generation(batch_size, use_cache, pipeline_report)

            # Stage 3: Validation
            if validate_embeddings:
                logger.info("Stage 3: Embedding validation...")
                self._stage_validation(pipeline_report)
            else:
                logger.info("Skipping embedding validation")
                pipeline_report["stages_completed"].append("validation_skipped")

            # Stage 4: Save Outputs
            if save_outputs:
                logger.info("Stage 4: Saving outputs...")
                self._stage_save_outputs(pipeline_report)
            else:
                logger.info("Skipping output save")
                pipeline_report["stages_completed"].append("save_skipped")

            # Final statistics
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()

            pipeline_report["status"] = "COMPLETED"
            pipeline_report["end_time"] = end_time.isoformat()
            pipeline_report["total_time"] = total_time

            logger.info(f"Pipeline completed successfully in {total_time:.2f}s!")

        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            logger.error(error_msg)
            pipeline_report["status"] = "FAILED"
            pipeline_report["errors"].append(error_msg)
            pipeline_report["end_time"] = datetime.now().isoformat()

        # Save pipeline report
        self._save_pipeline_report(pipeline_report)
        self.pipeline_report = pipeline_report

        return pipeline_report

    def _stage_text_preprocessing(self, input_data: pd.DataFrame, report: Dict):
        """Text preprocessing stage"""
        try:
            logger.info(f"Preprocessing text for {len(input_data)} movies...")

            # Preprocess the data
            self.processed_df = self.text_preprocessor.preprocess_movie_dataframe(
                input_data
            )

            # Validation
            validation_report = self.text_preprocessor.validate_preprocessed_data(
                self.processed_df
            )

            # Add statistics to report
            report["statistics"]["text_preprocessing"] = {
                "input_movies": len(input_data),
                "processed_movies": len(self.processed_df),
                "validation": validation_report,
            }

            report["stages_completed"].append("text_preprocessing")
            logger.info(
                f"Text preprocessing completed for {len(self.processed_df)} movies"
            )

        except Exception as e:
            error_msg = f"Text preprocessing failed: {str(e)}"
            report["errors"].append(error_msg)
            raise Exception(error_msg)

    def _stage_embedding_generation(
        self, batch_size: int, use_cache: bool, report: Dict
    ):
        """Embedding generation stage"""
        try:
            logger.info(f"Generating embeddings with batch size {batch_size}...")

            # Generate embeddings
            self.processed_df, self.embeddings = (
                self.embedding_generator.process_movie_dataframe(
                    self.processed_df,
                    batch_size=batch_size,
                    use_cache=use_cache,
                    save_embeddings=True,
                )
            )

            # Get generation statistics
            generation_stats = self.embedding_generator.get_generation_stats()

            # Add statistics to report
            report["statistics"]["embedding_generation"] = {
                "embeddings_shape": list(self.embeddings.shape),
                "embedding_dimension": self.embedding_generator.get_embedding_dimension(),
                "model_name": self.model_name,
                "generation_stats": generation_stats,
            }

            report["stages_completed"].append("embedding_generation")
            logger.info(f"Generated embeddings with shape {self.embeddings.shape}")

        except Exception as e:
            error_msg = f"Embedding generation failed: {str(e)}"
            report["errors"].append(error_msg)
            raise Exception(error_msg)

    def _stage_validation(self, report: Dict):
        """Embedding validation stage"""
        try:
            validation_results = self._validate_embeddings()

            report["statistics"]["validation"] = validation_results
            report["stages_completed"].append("validation")

            # Check for critical issues
            if validation_results["null_embeddings"] > 0:
                logger.warning(
                    f"Found {validation_results['null_embeddings']} null embeddings"
                )

            if validation_results["dimension_mismatch"]:
                raise Exception("Embedding dimension mismatch detected")

            logger.info(f"Embedding validation completed: {validation_results}")

        except Exception as e:
            error_msg = f"Embedding validation failed: {str(e)}"
            report["errors"].append(error_msg)
            raise Exception(error_msg)

    def _stage_save_outputs(self, report: Dict):
        """Save outputs stage"""
        try:
            saved_files = []

            # Save processed DataFrame
            df_path = self.output_dir / "movies_with_embeddings.csv"
            self.processed_df.to_csv(df_path, index=False)
            saved_files.append(str(df_path))

            # Save embeddings in multiple formats
            embeddings_numpy_path = self.output_dir / "movie_embeddings.npy"
            self.embedding_generator.save_embeddings_to_file(
                self.embeddings, self.processed_df, embeddings_numpy_path, "numpy"
            )
            saved_files.append(str(embeddings_numpy_path))

            embeddings_parquet_path = self.output_dir / "movie_embeddings.parquet"
            self.embedding_generator.save_embeddings_to_file(
                self.embeddings, self.processed_df, embeddings_parquet_path, "parquet"
            )
            saved_files.append(str(embeddings_parquet_path))

            # Save embedding metadata
            metadata = {
                "model_name": self.model_name,
                "embedding_dimension": self.embedding_generator.get_embedding_dimension(),
                "num_movies": len(self.processed_df),
                "generation_timestamp": datetime.now().isoformat(),
                "saved_files": saved_files,
            }

            metadata_path = self.output_dir / "embeddings_metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
            saved_files.append(str(metadata_path))

            report["statistics"]["saved_files"] = saved_files
            report["stages_completed"].append("save_outputs")

            logger.info(f"Saved outputs: {saved_files}")

        except Exception as e:
            error_msg = f"Save outputs failed: {str(e)}"
            report["errors"].append(error_msg)
            raise Exception(error_msg)

    def _validate_embeddings(self) -> Dict[str, Any]:
        """Validate generated embeddings"""
        if self.embeddings is None:
            return {"error": "No embeddings to validate"}

        validation = {
            "total_embeddings": len(self.embeddings),
            "embedding_dimension": self.embeddings.shape[1],
            "expected_dimension": self.embedding_generator.get_embedding_dimension(),
            "null_embeddings": 0,
            "zero_norm_embeddings": 0,
            "dimension_mismatch": False,
            "mean_norm": 0,
            "std_norm": 0,
        }

        # Check dimensions
        if self.embeddings.shape[1] != validation["expected_dimension"]:
            validation["dimension_mismatch"] = True

        # Check for null/invalid embeddings
        validation["null_embeddings"] = np.isnan(self.embeddings).any(axis=1).sum()

        # Check embedding norms (should be ~1.0 since we normalize)
        norms = np.linalg.norm(self.embeddings, axis=1)
        validation["zero_norm_embeddings"] = (norms < 1e-6).sum()
        validation["mean_norm"] = float(norms.mean())
        validation["std_norm"] = float(norms.std())

        return validation

    def _save_pipeline_report(self, report: Dict):
        """Save pipeline execution report"""
        try:
            report_path = (
                self.log_dir
                / f"embedding_pipeline_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Saved pipeline report to {report_path}")
        except Exception as e:
            logger.warning(f"Failed to save pipeline report: {e}")

    def get_processed_data(self) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Get processed data and embeddings

        Returns:
            Tuple of (processed_dataframe, embeddings_array)
        """
        if self.processed_df is None or self.embeddings is None:
            raise ValueError("Pipeline not yet run or failed")

        return self.processed_df, self.embeddings

    def search_similar_movies(
        self, query: str, top_k: int = 10
    ) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Search for similar movies using the generated embeddings

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            Tuple of (results_dataframe, similarity_scores)
        """
        if self.embeddings is None:
            raise ValueError("No embeddings available. Run pipeline first.")

        # Generate query embedding
        query_embedding = self.embedding_generator.generate_query_embedding(query)

        # Compute similarities
        similarities = self.embedding_generator.compute_similarities(
            query_embedding, self.embeddings
        )

        # Get top-k results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        top_similarities = similarities[top_indices]

        results_df = self.processed_df.iloc[top_indices].copy()
        results_df["similarity_score"] = top_similarities

        return results_df, top_similarities

    def get_pipeline_summary(self) -> Dict[str, Any]:
        """Get summary of pipeline execution"""
        if self.pipeline_report is None:
            return {"error": "Pipeline not yet run"}

        summary = {
            "status": self.pipeline_report["status"],
            "stages_completed": len(self.pipeline_report["stages_completed"]),
            "total_stages": 4,
            "completion_percentage": (len(self.pipeline_report["stages_completed"]) / 4)
            * 100,
            "errors": len(self.pipeline_report["errors"]),
            "model_name": self.model_name,
        }

        if "statistics" in self.pipeline_report:
            stats = self.pipeline_report["statistics"]
            if "embedding_generation" in stats:
                summary["embeddings_generated"] = stats["embedding_generation"][
                    "embeddings_shape"
                ][0]
                summary["embedding_dimension"] = stats["embedding_generation"][
                    "embedding_dimension"
                ]

        return summary


def run_embedding_pipeline(
    input_data: pd.DataFrame,
    model_name: str = "all-MiniLM-L6-v2",
    batch_size: int = 32,
    use_cache: bool = True,
    save_outputs: bool = True,
    device: Optional[str] = None,
) -> Tuple[Dict[str, Any], EmbeddingPipeline]:
    """
    Run the complete embedding pipeline

    Args:
        input_data: DataFrame with movie data
        model_name: Sentence transformer model name
        batch_size: Batch size for embedding generation
        use_cache: Whether to use cached embeddings
        save_outputs: Whether to save outputs
        device: Device for computation

    Returns:
        Tuple of (pipeline_report, pipeline_instance)
    """
    pipeline = EmbeddingPipeline(
        model_name=model_name,
        device=device,
    )

    report = pipeline.run_pipeline(
        input_data=input_data,
        batch_size=batch_size,
        use_cache=use_cache,
        save_outputs=save_outputs,
    )

    return report, pipeline


# Example usage and testing
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

    # Run pipeline
    report, pipeline = run_embedding_pipeline(
        input_data=sample_df,
        batch_size=2,
        use_cache=False,
    )

    print(f"Pipeline status: {report['status']}")
    print(f"Stages completed: {report['stages_completed']}")

    # Test search
    if report["status"] == "COMPLETED":
        results, scores = pipeline.search_similar_movies(
            "animated adventure movie", top_k=2
        )
        print(f"\nSearch results:")
        print(results[["clean_title", "genres_list", "similarity_score"]])
