"""
Pydantic models for the Netflix-clone MVP.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Movie(BaseModel):
    """Movie model with TMDB metadata."""

    id: int
    title: str
    overview: str = ""
    poster_path: Optional[str] = None
    backdrop_path: Optional[str] = None
    release_date: Optional[str] = None
    vote_average: float = 0.0
    vote_count: int = 0
    genres: List[str] = []
    runtime: Optional[int] = None
    tmdb_id: Optional[int] = None
    imdb_id: Optional[str] = None


class UserRating(BaseModel):
    """User rating model."""

    user_id: int
    movie_id: int
    rating: float
    timestamp: Optional[int] = None


class RecommendationRequest(BaseModel):
    """Request model for getting recommendations."""

    user_id: Optional[int] = None
    query: Optional[str] = Field(
        None, description="Natural language query for recommendations"
    )
    limit: int = Field(
        10, ge=1, le=50, description="Number of recommendations to return"
    )
    genre: Optional[str] = None
    min_rating: Optional[float] = Field(None, ge=0, le=10)
    include_watched: bool = Field(
        False, description="Include movies the user has already rated"
    )


class RecommendationResponse(BaseModel):
    """Response model for recommendations."""

    movies: List[Movie]
    explanation: str = ""
    total_count: int
    query_used: Optional[str] = None


class SearchRequest(BaseModel):
    """Request model for movie search."""

    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(10, ge=1, le=50)
    year: Optional[int] = None
    genre: Optional[str] = None


class ChatRequest(BaseModel):
    """Request model for conversational recommendations."""

    message: str = Field(..., min_length=1, description="User message")
    user_id: Optional[int] = None
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Response model for conversational recommendations."""

    response: str
    movies: List[Movie] = []
    suggestions: List[str] = []
