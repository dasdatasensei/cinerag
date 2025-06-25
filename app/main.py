"""
CineRAG - Main FastAPI Application

RAG-powered movie recommendation system with semantic search,
"""

import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from pydantic import BaseModel

# Import models and services (using new RAG folder structure)
from .models import (
    Movie,
    RecommendationRequest,
    RecommendationResponse,
    SearchRequest,
    ChatRequest,
    ChatResponse,
)
from .rag._05_retrieval.recommendation_service import RecommendationService
from .rag._01_ingestion.data_loader import MovieLensDataLoader
from .rag._01_ingestion.tmdb_service import TMDBService
from .rag._03_vectorstore.vector_service import VectorService
from .rag._04_query_processing.query_enhancer import QueryEnhancer
from .rag._01_ingestion.ingestion_service import DataIngestionService
from .rag._04_query_processing.chat_service import ChatService

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="CineRAG",
    description="RAG-Powered Movie Recommendations with Semantic Search",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
data_loader = MovieLensDataLoader()
tmdb_service = TMDBService()
vector_service = VectorService()
query_enhancer = QueryEnhancer()
recommendation_service = RecommendationService()
data_ingestion_service = DataIngestionService()
chat_service = ChatService()


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "CineRAG API with RAG", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    vector_info = vector_service.get_collection_info()
    return {
        "status": "healthy",
        "service": "CineRAG API",
        "rag_enabled": "error" not in vector_info,
        "vector_count": vector_info.get("points_count", 0),
    }


@app.post("/api/recommendations", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """Get movie recommendations using RAG, collaborative filtering, or LLM."""
    try:
        response = await recommendation_service.get_recommendations(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting recommendations: {str(e)}"
        )


@app.get("/api/movies/popular", response_model=List[Movie])
async def get_popular_movies(
    limit: int = Query(20, ge=1, le=50, description="Number of movies to return"),
    genre: str = Query(None, description="Filter by genre"),
):
    """Get popular movies."""
    try:
        if genre:
            movies = data_loader.get_movies_by_genre(genre, limit)
        else:
            movies = data_loader.get_popular_movies(limit)

        # Enrich with TMDB data
        titles = [movie.title for movie in movies]
        enriched_movies = await tmdb_service.batch_enrich_movies(movies, titles)

        return enriched_movies
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting popular movies: {str(e)}"
        )


@app.get("/api/movies/search", response_model=List[Movie])
async def search_movies(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return"),
    semantic: bool = Query(False, description="Use semantic search (RAG)"),
):
    """Search for movies using text search or semantic RAG search."""
    try:
        if semantic:
            # Use RAG vector search
            similar_movies_data = vector_service.search_similar_movies(q, limit)
            movies = []
            for movie_data in similar_movies_data:
                movie = Movie(**movie_data)
                movies.append(movie)
            return movies
        else:
            # Use traditional text search
            movies = data_loader.search_movies(q, limit)

            # Enrich with TMDB data
            titles = [movie.title for movie in movies]
            enriched_movies = await tmdb_service.batch_enrich_movies(movies, titles)

            return enriched_movies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching movies: {str(e)}")


@app.get("/api/movies/{movie_id}", response_model=Movie)
async def get_movie(movie_id: int):
    """Get movie details by ID."""
    try:
        movie = data_loader.get_movie_by_id(movie_id)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")

        # Enrich with TMDB data
        enriched_movie = await tmdb_service.enrich_movie_with_tmdb_data(
            movie, movie.title
        )

        return enriched_movie
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting movie: {str(e)}")


@app.get("/api/movies/{movie_id}/similar", response_model=List[Movie])
async def get_similar_movies(
    movie_id: int,
    limit: int = Query(
        10, ge=1, le=20, description="Number of similar movies to return"
    ),
):
    """Get movies similar to a specific movie using RAG vector search."""
    try:
        # Check if movie exists
        movie = data_loader.get_movie_by_id(movie_id)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")

        similar_movies = await recommendation_service.get_similar_movies(
            movie_id, limit
        )
        return similar_movies
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting similar movies: {str(e)}"
        )


@app.get("/api/genres", response_model=List[str])
async def get_genres():
    """Get all available genres."""
    try:
        genres = data_loader.get_genres()
        return genres
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting genres: {str(e)}")


@app.get("/api/movies/genre/{genre}", response_model=List[Movie])
async def get_movies_by_genre(
    genre: str,
    limit: int = Query(20, ge=1, le=50, description="Number of movies to return"),
):
    """Get movies by genre."""
    try:
        movies = data_loader.get_movies_by_genre(genre, limit)

        # Enrich with TMDB data
        titles = [movie.title for movie in movies]
        enriched_movies = await tmdb_service.batch_enrich_movies(movies, titles)

        return enriched_movies
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting movies by genre: {str(e)}"
        )


@app.post("/api/chat", response_model=ChatResponse)
async def chat_recommendation(request: ChatRequest):
    """Conversational movie recommendations."""
    try:
        response = await chat_service.chat_recommendation(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in chat: {str(e)}")


@app.get("/api/user/{user_id}/recommendations", response_model=RecommendationResponse)
async def get_user_recommendations(
    user_id: int,
    limit: int = Query(20, ge=1, le=50, description="Number of recommendations"),
):
    """Get personalized recommendations for a user."""
    try:
        request = RecommendationRequest(user_id=user_id, limit=limit)
        response = await recommendation_service.get_recommendations(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting user recommendations: {str(e)}"
        )


@app.get("/api/user/{user_id}/ratings")
async def get_user_ratings(user_id: int):
    """Get user's movie ratings."""
    try:
        ratings = data_loader.get_user_ratings(user_id)
        return {"user_id": user_id, "ratings": ratings, "total": len(ratings)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting user ratings: {str(e)}"
        )


@app.get("/api/vector/info")
async def get_vector_database_info():
    """Get vector database information."""
    try:
        info = vector_service.get_collection_info()
        return info
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting vector database info: {str(e)}"
        )


@app.post("/api/vector/search", response_model=List[Movie])
async def vector_search(
    query: str = Query(..., min_length=1, description="Semantic search query"),
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
    genre: str = Query(None, description="Filter by genre"),
):
    """Direct semantic search using RAG vector database."""
    try:
        similar_movies_data = vector_service.search_similar_movies(query, limit, genre)
        movies = []
        for movie_data in similar_movies_data:
            movie = Movie(**movie_data)
            movies.append(movie)
        return movies
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in vector search: {str(e)}")


# Vector Database Management Endpoints
@app.post("/api/admin/ingest/popular")
async def ingest_popular_movies(
    limit: int = Query(
        500, ge=1, le=2000, description="Number of popular movies to ingest"
    )
):
    """Ingest popular movies into the vector database."""
    try:
        result = await data_ingestion_service.ingest_popular_movies(limit)
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during ingestion: {str(e)}")


@app.post("/api/admin/ingest/genre/{genre}")
async def ingest_movies_by_genre(
    genre: str,
    limit: int = Query(200, ge=1, le=1000, description="Number of movies per genre"),
):
    """Ingest movies of a specific genre."""
    try:
        result = await data_ingestion_service.ingest_movies_by_genre(genre, limit)
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error ingesting {genre} movies: {str(e)}"
        )


@app.post("/api/admin/ingest/all")
async def ingest_all_movies(
    limit_per_genre: int = Query(150, ge=10, le=500, description="Movies per genre")
):
    """Ingest movies from all genres into the vector database."""
    try:
        result = await data_ingestion_service.ingest_all_genres(limit_per_genre)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error during full ingestion: {str(e)}"
        )


@app.get("/api/admin/ingestion/status")
async def get_ingestion_status():
    """Get the current ingestion status and vector database info."""
    try:
        status = data_ingestion_service.get_ingestion_status()
        return status
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting ingestion status: {str(e)}"
        )


@app.post("/api/admin/ingest/reingest")
async def reingest_database():
    """Completely reingest the entire vector database (use with caution)."""
    try:
        result = await data_ingestion_service.reingest_database()
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error during reingestion: {str(e)}"
        )


@app.get("/api/vector/health")
async def vector_health_check():
    """Comprehensive health check of the vector service."""
    try:
        health_status = vector_service.health_check()
        return health_status
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error in vector health check: {str(e)}"
        )


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not found",
            "detail": (
                str(exc.detail) if hasattr(exc, "detail") else "Resource not found"
            ),
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "Something went wrong"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "True").lower() == "true",
    )
