# CineRAG Pipeline Architecture

## 📋 **Overview**

This directory contains the complete RAG (Retrieval-Augmented Generation) pipeline for the CineRAG movie recommendation system. The pipeline is organized into seven distinct stages, each handling a specific aspect of the movie recommendation process.

## 🏗️ **Pipeline Structure**

### **Stage 1: Data Ingestion** (`_01_ingestion/`)

**Purpose**: Raw data loading and external API enrichment

- **`data_loader.py`** - MovieLens dataset loading and preprocessing
- **`tmdb_service.py`** - TMDB API integration for movie metadata enrichment
- **`ingestion_service.py`** - Orchestrates data ingestion into vector database

**Key Features**:

- MovieLens data parsing and cleaning
- TMDB API integration with rate limiting and caching
- Batch movie enrichment with rich metadata
- Data format conversion for vector storage

### **Stage 2: Embeddings** (`_02_embeddings/`)

**Purpose**: Text-to-vector conversion and embedding management

- _Currently integrated into vector service - may be expanded for custom embedding models_

### **Stage 3: Vector Store** (`_03_vectorstore/`)

**Purpose**: Semantic vector storage and similarity search

- **`vector_service.py`** - Qdrant vector database implementation

**Key Features**:

- Sentence transformer embeddings (all-MiniLM-L6-v2)
- Qdrant collection management
- Semantic similarity search with filters
- Vector health monitoring and statistics

### **Stage 4: Query Processing** (`_04_query_processing/`)

**Purpose**: Natural language query understanding and enhancement

- **`query_enhancer.py`** - Advanced query enhancement and optimization
- **`chat_service.py`** - Conversational interface for movie recommendations

**Key Features**:

- Intent detection and query enhancement
- Spelling correction and synonym expansion
- Mood-to-genre mapping
- Conversational movie recommendations

### **Stage 5: Retrieval** (`_05_retrieval/`)

**Purpose**: Multi-strategy movie recommendation generation

- **`recommendation_service.py`** - Core recommendation engine

**Key Features**:

- Semantic vector search recommendations
- Genre-based filtering
- Mood-based recommendations
- Similar movie discovery

### **Stage 6: Evaluation** (`_06_evaluation/`)

**Purpose**: System performance assessment and metrics

- _Reserved for future implementation of recommendation quality metrics_

### **Stage 7: Optimization** (`_07_optimization/`)

**Purpose**: Performance tuning and system optimization

- _Reserved for future implementation of search optimization and A/B testing_

## 🔄 **Data Flow**

```
Raw Data → Ingestion → Embeddings → Vector Store
                                        ↓
User Query → Query Processing → Retrieval → Response
                                        ↑
                              Evaluation ← Optimization
```

## 🛠️ **Service Dependencies**

### **Internal Dependencies**

- All services import from `app.models` for shared data structures
- Cross-stage imports follow the pipeline flow direction
- Vector service is used by both ingestion and retrieval stages

### **External Dependencies**

- **Qdrant**: Vector database for semantic search
- **TMDB API**: Movie metadata enrichment
- **Sentence Transformers**: Text embedding generation
- **aiohttp**: Async HTTP client for API calls

## 📊 **Configuration**

### **Environment Variables**

```bash
TMDB_API_KEY=your_tmdb_api_key_here
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### **Vector Configuration**

- **Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Distance**: Cosine similarity
- **Collection**: movies

## 🚀 **Usage Examples**

### **Basic Movie Search**

```python
from app.rag._03_vectorstore.vector_service import VectorService

vector_service = VectorService()
movies = vector_service.search_similar_movies("action adventure space", limit=10)
```

### **Conversational Recommendations**

```python
from app.rag._04_query_processing.chat_service import ChatService

chat_service = ChatService()
response = await chat_service.chat_recommendation(
    ChatRequest(message="I want something funny to watch tonight")
)
```

### **Data Ingestion**

```python
from app.rag._01_ingestion.ingestion_service import DataIngestionService

ingestion_service = DataIngestionService()
result = await ingestion_service.ingest_popular_movies(limit=1000)
```

## 🔧 **Development Guidelines**

### **Adding New Services**

1. Place services in the appropriate pipeline stage directory
2. Follow the existing naming conventions (`*_service.py`)
3. Implement proper error handling and logging
4. Add comprehensive docstrings and type hints

### **Pipeline Stage Guidelines**

- **Stateless**: Services should be stateless when possible
- **Async**: Use async/await for I/O operations
- **Error Handling**: Graceful degradation on failures
- **Logging**: Structured logging with appropriate levels

### **Import Conventions**

```python
# Internal RAG imports use relative paths
from .._03_vectorstore.vector_service import VectorService

# Models are imported from app root
from ...models import Movie, ChatRequest

# External dependencies use absolute imports
import asyncio
from typing import List, Dict, Any
```

## 📈 **Performance Considerations**

### **Vector Search**

- Embedding model is loaded once per service instance
- Qdrant queries use connection pooling
- Search results are filtered at the database level

### **TMDB Integration**

- API responses are cached for 24 hours
- Rate limiting respects TMDB limits (4 req/sec)
- Batch processing for multiple movie enrichment

### **Memory Management**

- Embedding model: ~90MB in memory
- Query cache: Configurable with TTL
- Connection pooling for external APIs

## 🎯 **Future Enhancements**

### **Stage 6: Evaluation**

- Recommendation accuracy metrics
- User feedback integration
- A/B testing framework

### **Stage 7: Optimization**

- Query optimization based on performance metrics
- Embedding model fine-tuning
- Cache optimization strategies

### **Additional Features**

- Multi-language support
- Real-time recommendation updates
- Advanced personalization algorithms

## 📚 **Architecture Benefits**

1. **Modularity**: Each stage can be developed and tested independently
2. **Scalability**: Individual services can be scaled based on demand
3. **Maintainability**: Clear separation of concerns and responsibilities
4. **Extensibility**: Easy to add new services or modify existing ones
5. **Testability**: Each service can be unit tested in isolation

---

This RAG pipeline provides a robust foundation for semantic movie recommendations while maintaining flexibility for future enhancements and optimizations.
