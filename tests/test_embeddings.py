#!/usr/bin/env python3
"""
Test script for the 02_Embeddings pipeline
"""

import sys
import logging
from pathlib import Path

import pandas as pd

# Add parent directory to path so we can import from app
sys.path.append(str(Path(__file__).parent.parent))

from app.rag._02_embeddings.pipeline import run_embedding_pipeline


def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Load a small subset of our processed data for testing
    print("Loading processed movie data...")
    movies_df = pd.read_csv("data/processed/movies_processed.csv")
    print(f"Loaded {len(movies_df)} movies")

    # Test with first 50 movies for speed
    test_df = movies_df.head(50)
    print(f"Testing with {len(test_df)} movies")

    # Run the embedding pipeline
    print("Running embedding pipeline...")
    report, pipeline = run_embedding_pipeline(
        input_data=test_df,
        batch_size=16,
        use_cache=True,
        save_outputs=True,
    )

    print(f'Pipeline status: {report["status"]}')
    print(f'Stages completed: {report["stages_completed"]}')

    if report["status"] == "COMPLETED":
        # Test search functionality
        print("\nTesting search functionality...")
        results, scores = pipeline.search_similar_movies("animated toy movie", top_k=5)
        print("Top 5 results:")
        for i, (_, row) in enumerate(results.iterrows()):
            print(
                f'{i+1}. {row["clean_title"]} ({row["year"]}) - Score: {row["similarity_score"]:.3f}'
            )

        # Get summary
        summary = pipeline.get_pipeline_summary()
        print(f"\nPipeline Summary:")
        print(f'- Embeddings generated: {summary.get("embeddings_generated", "N/A")}')
        print(f'- Embedding dimension: {summary.get("embedding_dimension", "N/A")}')
        print(f'- Model: {summary.get("model_name", "N/A")}')

        # Test with different queries
        print("\nTesting different search queries:")
        queries = [
            "action thriller movie",
            "romantic comedy",
            "sci-fi adventure",
            "horror film",
            "drama about family",
        ]

        for query in queries:
            results, _ = pipeline.search_similar_movies(query, top_k=3)
            print(f'\nQuery: "{query}"')
            for i, (_, row) in enumerate(results.iterrows()):
                genres = row["genres_list"].strip("[]").replace("'", "")
                print(f'  {i+1}. {row["clean_title"]} - Genres: {genres}')
    else:
        print("Pipeline failed!")
        print(f'Errors: {report.get("errors", [])}')


if __name__ == "__main__":
    main()
