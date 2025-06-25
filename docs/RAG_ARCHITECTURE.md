# 🏗️ CineRAG Architecture Documentation

## 🎯 System Overview

CineRAG implements a complete **Retrieval-Augmented Generation (RAG)** pipeline for intelligent movie recommendations, following industry-standard patterns and best practices.

![CineRAG System Architecture](../assets/cinerag_system_architecture.png)
_Visual overview of the complete CineRAG system architecture and data flow_

## 📊 RAG Pipeline Architecture

```mermaid
graph TD
    %% Data Sources
    ML[MovieLens Dataset<br/>📊 9,742 Movies<br/>100,836 Ratings]
    TMDB[TMDB API<br/>🎬 Rich Metadata<br/>Posters & Details]

    %% Stage 01: Ingestion
    subgraph "01_INGESTION 📥"
        DL[Data Loader<br/>🔄 CSV Processing]
        TMDB_SVC[TMDB Service<br/>🌐 API Integration]
        IS[Ingestion Service<br/>📋 Data Orchestration]
    end

    %% Stage 02: Embeddings
    subgraph "02_EMBEDDINGS 🧠"
        TP[Text Preprocessor<br/>✂️ Text Cleaning]
        EG[Embedding Generator<br/>🔮 Sentence Transformers]
        EP[Embedding Pipeline<br/>⚡ Batch Processing]
    end

    %% Stage 03: VectorStore
    subgraph "03_VECTORSTORE 🗄️"
        QC[Qdrant Client<br/>📡 Vector DB Connection]
        VO[Vector Operations<br/>📤 Upload & Search]
        SS[Semantic Search<br/>🎯 Similarity Queries]
    end

    %% Stage 04: Query Processing
    subgraph "04_QUERY_PROCESSING 🔍"
        QP[Query Preprocessor<br/>✨ Text Normalization]
        QE[Query Enhancer<br/>🚀 Intent Detection]
        QC2[Query Processor<br/>🎛️ Query Orchestration]
        CS[Chat Service<br/>💬 LLM Integration]
    end

    %% Stage 05: Retrieval
    subgraph "05_RETRIEVAL 🎯"
        HS[Hybrid Search<br/>🔀 Semantic + Keyword]
        RR[Result Ranker<br/>📈 Score Optimization]
        RS[Recommendation Service<br/>🎪 Business Logic]
    end

    %% Stage 06: Evaluation
    subgraph "06_EVALUATION 📊"
        QM[Quality Metrics<br/>📏 Precision, Recall, NDCG]
        PM[Performance Metrics<br/>⏱️ Latency, Throughput]
        EP2[Evaluation Pipeline<br/>🔬 Automated Assessment]
    end

    %% Stage 07: Optimization
    subgraph "07_OPTIMIZATION 🔄"
        CM[Cache Manager<br/>💾 Multi-tier Caching]
        PO[Performance Optimizer<br/>⚡ Query & Ranking Tuning]
        OP[Optimization Pipeline<br/>🎛️ System Enhancement]
    end

    %% External Services
    QDRANT[(Qdrant Vector DB<br/>🗄️ 384-dim Vectors)]
    OPENAI[OpenAI API<br/>🤖 GPT-4 Chat]
    REDIS[(Redis Cache<br/>💾 Fast Storage)]

    %% API Layer
    subgraph "API LAYER 🚀"
        FASTAPI[FastAPI<br/>⚡ REST Endpoints]
        ENDPOINTS["/api/movies/search<br/>/api/chat<br/>/api/recommendations"]
    end

    %% Frontend
    FRONTEND[React Frontend<br/>🎨 Netflix-style UI]

    %% Data Flow Connections
    ML --> DL
    TMDB --> TMDB_SVC
    DL --> IS
    TMDB_SVC --> IS

    IS --> TP
    TP --> EG
    EG --> EP

    EP --> QC
    QC --> VO
    VO --> SS
    VO --> QDRANT

    QP --> QE
    QE --> QC2
    QC2 --> CS
    CS --> OPENAI

    SS --> HS
    HS --> RR
    RR --> RS

    RS --> QM
    QM --> PM
    PM --> EP2

    HS --> CM
    CM --> REDIS
    CM --> PO
    PO --> OP

    RS --> FASTAPI
    FASTAPI --> ENDPOINTS
    ENDPOINTS --> FRONTEND

    %% Styling
    classDef ingestion fill:#ff6b6b
    classDef embeddings fill:#4ecdc4
    classDef vectorstore fill:#45b7d1
    classDef query fill:#96ceb4
    classDef retrieval fill:#ffeaa7
    classDef evaluation fill:#dda0dd
    classDef optimization fill:#fab1a0
    classDef external fill:#a8e6cf
    classDef api fill:#ffaaa5

    class DL,TMDB_SVC,IS ingestion
    class TP,EG,EP embeddings
    class QC,VO,SS vectorstore
    class QP,QE,QC2,CS query
    class HS,RR,RS retrieval
    class QM,PM,EP2 evaluation
    class CM,PO,OP optimization
    class QDRANT,OPENAI,REDIS external
    class FASTAPI,ENDPOINTS api
```

## 🔄 Data Flow Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant API as FastAPI
    participant QP as Query Processor
    participant V as Vector Store
    participant C as Cache
    participant LLM as OpenAI

    U->>F: Search Query
    F->>API: /api/movies/search
    API->>QP: Process Query
    QP->>QP: Clean & Enhance
    QP->>C: Check Cache

    alt Cache Hit
        C-->>API: Cached Results
    else Cache Miss
        QP->>V: Vector Search
        V->>V: Similarity Search
        V-->>QP: Similar Movies
        QP->>C: Store Results
    end

    API->>API: Rank & Filter
    API-->>F: Movie Results
    F-->>U: Display Movies

    opt Chat Request
        U->>F: Chat Message
        F->>API: /api/chat
        API->>LLM: Generate Response
        LLM-->>API: AI Response
        API-->>F: Chat Reply
        F-->>U: Display Reply
    end
```

## 🧩 Component Interactions

### **Core Interactions**

1. **Ingestion → Embeddings**: Raw data → Processed vectors
2. **Embeddings → VectorStore**: Vectors → Searchable index
3. **Query Processing → Retrieval**: Enhanced queries → Relevant results
4. **Retrieval → Optimization**: Search results → Cached & optimized
5. **Evaluation → Optimization**: Performance metrics → System improvements

### **External Service Integration**

```mermaid
graph LR
    subgraph "CineRAG System"
        RAG[RAG Pipeline]
        CACHE[Cache Layer]
    end

    subgraph "External Services"
        TMDB_API[TMDB API<br/>Movie Metadata]
        QDRANT_DB[Qdrant<br/>Vector Database]
        OPENAI_API[OpenAI<br/>LLM Chat]
        REDIS_DB[Redis<br/>Caching]
    end

    RAG <--> TMDB_API
    RAG <--> QDRANT_DB
    RAG <--> OPENAI_API
    CACHE <--> REDIS_DB

    classDef external fill:#a8e6cf
    class TMDB_API,QDRANT_DB,OPENAI_API,REDIS_DB external
```

## 📈 Performance Characteristics

### **Latency Targets**

- **Search Response**: < 100ms (achieved: 19-45ms)
- **Vector Similarity**: < 50ms
- **Cache Hit**: < 10ms
- **Full Pipeline**: < 200ms

### **Throughput Capacity**

- **Concurrent Users**: 100+
- **Search QPS**: 1000+
- **Vector Operations**: 10,000/sec
- **Cache Operations**: 100,000/sec

### **Optimization Features**

- **Multi-tier Caching**: LRU + Redis
- **Query Enhancement**: Intent detection + expansion
- **Result Ranking**: Personalization + diversity
- **Performance Monitoring**: Real-time metrics

## 🔧 Technical Stack

| Component           | Technology            | Purpose                                   |
| ------------------- | --------------------- | ----------------------------------------- |
| **Vector DB**       | Qdrant                | High-performance vector similarity search |
| **Embeddings**      | Sentence Transformers | Text-to-vector conversion                 |
| **API Framework**   | FastAPI               | High-performance async REST API           |
| **Frontend**        | React + TypeScript    | Modern, responsive UI                     |
| **Caching**         | Redis + LRU           | Multi-tier performance optimization       |
| **LLM Integration** | OpenAI GPT-4          | Conversational recommendations            |
| **Data Source**     | MovieLens + TMDB      | Rich movie dataset                        |
| **Deployment**      | Docker + Compose      | Containerized deployment                  |

## 🎯 RAG Engineering Highlights

### **Industry Best Practices**

✅ **Modular Architecture**: 7-stage pipeline for maintainability
✅ **Performance Optimization**: Sub-100ms search with caching
✅ **Quality Evaluation**: Comprehensive IR metrics (NDCG, MAP, MRR)
✅ **Continuous Improvement**: Automated optimization pipeline
✅ **Production Ready**: Docker deployment, health checks, monitoring

### **Advanced Features**

🚀 **Hybrid Search**: Combines semantic + keyword search
🧠 **Query Enhancement**: Intent detection and expansion
📊 **Real-time Evaluation**: Performance and quality monitoring
💾 **Intelligent Caching**: Multi-tier optimization strategy
🎯 **Personalization**: User interaction learning

---

_This architecture demonstrates production-ready RAG engineering with industry-standard patterns, performance optimization, and comprehensive evaluation._
