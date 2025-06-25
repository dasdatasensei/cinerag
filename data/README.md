# 📊 CineRAG Data Directory

This directory contains all datasets, processed data, cache files, and logs for the CineRAG movie recommendation system.

## 🎬 Dataset Overview

CineRAG uses the **MovieLens Latest-Small Dataset** enhanced with **TMDB API** metadata to provide rich movie recommendations with:

- **9,742 movies** with ratings and metadata
- **100,836 ratings** from users
- **Rich metadata** including posters, descriptions, and details from TMDB
- **Vector embeddings** for semantic search capabilities

## 📁 Directory Structure

```
data/
├── raw/                          # 📥 Raw, unprocessed datasets
│   └── latest-small/               # MovieLens latest-small dataset
│       ├── ml-latest-small.zip      # Original downloaded dataset
│       ├── metadata.json            # Dataset metadata
│       └── ml-latest-small/         # Extracted MovieLens files
│           ├── movies.csv             # Movie titles and genres
│           ├── ratings.csv            # User ratings (100,836 ratings)
│           ├── tags.csv               # User-generated tags
│           ├── links.csv              # Movie links (IMDB, TMDB IDs)
│           └── README.txt             # MovieLens documentation
├── processed/                    # 🔄 Processed and enriched data
│   ├── movies_processed.csv         # Cleaned and standardized movies
│   ├── movies_enriched_ml.csv       # Movies enriched with TMDB data
│   ├── ratings_processed.csv        # Cleaned and processed ratings
│   ├── validation_report.json       # Data quality validation results
│   └── embeddings/                  # Generated vector embeddings
│       ├── movie_embeddings.npy       # Sentence transformer embeddings
│       └── embedding_metadata.json   # Embedding generation details
├── cache/                        # 💾 Performance optimization cache
│   └── embeddings/                  # Cached embedding computations
│       └── sentence_transformers/    # Model cache directory
└── logs/                         # 📋 Processing and pipeline logs
    ├── ingestion_pipeline_*.json    # Data ingestion logs
    ├── embedding_pipeline_*.json    # Embedding generation logs
    └── validation_report_*.json     # Data validation logs
```

## 🚀 Data Pipeline Overview

CineRAG implements a comprehensive data pipeline with the following stages:

### **01. Data Ingestion**

- Downloads MovieLens latest-small dataset
- Extracts and validates CSV files
- Integrates with TMDB API for rich metadata

### **02. Data Processing**

- Cleans and standardizes movie data
- Processes user ratings and preferences
- Enriches movies with TMDB posters, descriptions, and details

### **03. Embedding Generation**

- Creates 384-dimensional vector embeddings using Sentence Transformers
- Processes movie descriptions and metadata for semantic search
- Caches embeddings for optimal performance

### **04. Data Validation**

- Quality checks on all processed data
- Generates validation reports with statistics
- Ensures data integrity throughout the pipeline

## 📈 Dataset Statistics

| Metric                   | Value                       |
| ------------------------ | --------------------------- |
| **Total Movies**         | 9,742                       |
| **Total Ratings**        | 100,836                     |
| **Unique Users**         | 610                         |
| **Genres**               | 17 distinct genres          |
| **Time Range**           | 1995-2018                   |
| **Embedding Dimensions** | 384 (Sentence Transformers) |
| **Vector Database**      | Qdrant with HNSW indexing   |

## 🔧 Data Access & Usage

### **Programmatic Access**

```python
from app.rag._01_ingestion.data_loader import MovieLensDataLoader

# Load processed data
loader = MovieLensDataLoader()
movies = loader.load_movies()
ratings = loader.load_ratings()

# Get popular movies
popular = loader.get_popular_movies(limit=10)

# Search by genre
action_movies = loader.get_movies_by_genre("Action", limit=20)
```

### **Direct File Access**

```python
import pandas as pd

# Load processed movies with TMDB enrichment
movies = pd.read_csv('data/processed/movies_enriched_ml.csv')

# Load processed ratings
ratings = pd.read_csv('data/processed/ratings_processed.csv')

# Load embeddings
import numpy as np
embeddings = np.load('data/processed/embeddings/movie_embeddings.npy')
```

## 🎯 Data Quality & Validation

CineRAG implements comprehensive data validation:

- **Completeness**: Ensures all required fields are present
- **Consistency**: Validates data types and value ranges
- **Enrichment**: Verifies TMDB API integration success
- **Embeddings**: Validates vector generation and dimensions

**Latest Validation Report**: `data/processed/validation_report.json`

## 🔄 Data Updates & Maintenance

### **Refreshing Data**

```bash
# Re-download and process MovieLens data
python app/rag/_01_ingestion/data_loader.py

# Regenerate embeddings
python app/rag/_02_embeddings/embedding_generator.py

# Validate processed data
python app/rag/_01_ingestion/ingestion_service.py --validate
```

### **Cache Management**

```bash
# Clear embedding cache
rm -rf data/cache/embeddings/*

# Clear processing logs (keep latest 10)
find data/logs/ -name "*.json" -type f | head -n -10 | xargs rm
```

## 📚 External Data Sources

### **MovieLens Dataset**

- **Source**: [MovieLens Latest-Small](https://grouplens.org/datasets/movielens/latest/)
- **License**: Open source for academic and personal use
- **Citation**: F. Maxwell Harper and Joseph A. Konstan. 2015. The MovieLens Datasets

### **TMDB (The Movie Database)**

- **Source**: [TMDB API](https://www.themoviedb.org/documentation/api)
- **Purpose**: Movie posters, descriptions, and rich metadata
- **Rate Limits**: 40 requests per 10 seconds
- **API Key Required**: Set `TMDB_API_KEY` in environment

## 🔒 Data Privacy & Compliance

- **MovieLens**: Anonymized user data, no personal information
- **TMDB**: Public movie metadata only
- **Local Storage**: All data stored locally, no external sharing
- **Caching**: Respects API rate limits and terms of service

## 🚀 Performance Optimization

- **Embedding Cache**: Prevents regeneration of unchanged embeddings
- **Processed Files**: Pre-computed datasets for fast loading
- **Vector Database**: Optimized for sub-100ms search performance
- **Batch Processing**: Efficient data pipeline with progress tracking

---

**🎬 This data infrastructure supports production-ready RAG recommendations with comprehensive quality assurance and performance optimization.**
