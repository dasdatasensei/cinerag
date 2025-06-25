"""
Chat Service for Conversational Movie Recommendations

This service handles natural language conversations about movies,
leveraging the RAG pipeline for intelligent responses.
"""

import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from ...models import ChatRequest, ChatResponse, Movie
from .._01_ingestion.data_loader import MovieLensDataLoader
from .._03_vectorstore.vector_service import VectorService
from .._01_ingestion.tmdb_service import TMDBService


class ChatService:
    """Service for handling conversational movie recommendations."""

    def __init__(self):
        self.data_loader = MovieLensDataLoader()
        self.vector_service = VectorService()
        self.tmdb_service = TMDBService()

        # Conversation patterns for intent recognition
        self.intent_patterns = {
            "recommendation": [
                r"recommend.*movie",
                r"suggest.*film",
                r"what.*should.*watch",
                r"find.*movie",
                r"good.*movie",
                r"best.*film",
                r"movies.*like",
                r"similar.*to",
            ],
            "genre_query": [
                r"(action|comedy|drama|horror|sci-fi|romance|thriller|fantasy|adventure).*movies?",
                r"movies.*in.*(action|comedy|drama|horror|sci-fi|romance|thriller|fantasy|adventure)",
                r"(action|comedy|drama|horror|sci-fi|romance|thriller|fantasy|adventure).*films?",
            ],
            "mood_based": [
                r"feeling.*sad",
                r"want.*funny",
                r"need.*laugh",
                r"romantic.*mood",
                r"scared.*tonight",
                r"action.*packed",
                r"something.*light",
                r"mind.*bending",
            ],
            "specific_movie": [
                r"tell.*about.*",
                r"what.*is.*about",
                r"plot.*of",
                r"summary.*of",
            ],
            "trending": [
                r"trending.*now",
                r"popular.*movies",
                r"what.*hot",
                r"latest.*releases",
            ],
        }

        # Mood to genre mapping
        self.mood_to_genre = {
            "sad": ["Drama", "Romance"],
            "funny": ["Comedy"],
            "laugh": ["Comedy"],
            "romantic": ["Romance"],
            "scared": ["Horror", "Thriller"],
            "action": ["Action", "Adventure"],
            "light": ["Comedy", "Romance", "Animation"],
            "mind": ["Sci-Fi", "Thriller", "Mystery"],
        }

    def detect_intent(self, message: str) -> str:
        """Detect user intent from message."""
        message_lower = message.lower()

        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent

        return "general"

    def extract_genre(self, message: str) -> Optional[str]:
        """Extract genre from message."""
        message_lower = message.lower()
        genres = [
            "action",
            "comedy",
            "drama",
            "horror",
            "sci-fi",
            "romance",
            "thriller",
            "fantasy",
            "adventure",
            "animation",
            "crime",
            "mystery",
        ]

        for genre in genres:
            if genre in message_lower:
                return genre.title()

        return None

    def extract_mood(self, message: str) -> List[str]:
        """Extract mood-based genres from message."""
        message_lower = message.lower()
        detected_genres = []

        for mood, genres in self.mood_to_genre.items():
            if mood in message_lower:
                detected_genres.extend(genres)

        return list(set(detected_genres))

    def extract_movie_title(self, message: str) -> Optional[str]:
        """Extract movie title from message."""
        # Look for quotes or specific patterns
        quote_match = re.search(r'["\']([^"\']+)["\']', message)
        if quote_match:
            return quote_match.group(1)

        # Look for "about X" patterns
        about_match = re.search(r"about\s+([^?]+)", message, re.IGNORECASE)
        if about_match:
            return about_match.group(1).strip()

        return None

    async def process_recommendation_request(
        self, message: str, limit: int = 6
    ) -> tuple[str, List[Movie]]:
        """Process a recommendation request and return response with movies."""

        # Extract genre and mood information
        genre = self.extract_genre(message)
        mood_genres = self.extract_mood(message)

        # Determine search strategy
        movies = []
        explanation = ""

        if "similar" in message.lower():
            # Handle similarity requests
            movie_title = self.extract_movie_title(message)
            if movie_title:
                # Use vector search for similar movies
                similar_movies_data = self.vector_service.search_similar_movies(
                    f"movies like {movie_title}", limit
                )
                movies = [Movie(**movie_data) for movie_data in similar_movies_data]
                explanation = f"Here are movies similar to '{movie_title}':"
            else:
                explanation = "I couldn't identify the specific movie you mentioned. Could you try again with the movie title in quotes?"

        elif genre:
            # Genre-based recommendations
            movies_data = self.data_loader.get_movies_by_genre(genre, limit)
            titles = [movie.title for movie in movies_data]
            movies = await self.tmdb_service.batch_enrich_movies(movies_data, titles)
            explanation = f"Here are some great {genre.lower()} movies I recommend:"

        elif mood_genres:
            # Mood-based recommendations
            genre_to_use = mood_genres[0]  # Use first detected mood genre
            movies_data = self.data_loader.get_movies_by_genre(genre_to_use, limit)
            titles = [movie.title for movie in movies_data]
            movies = await self.tmdb_service.batch_enrich_movies(movies_data, titles)
            explanation = (
                f"Based on your mood, here are some {genre_to_use.lower()} movies:"
            )

        else:
            # Use semantic search with the full message
            similar_movies_data = self.vector_service.search_similar_movies(
                message, limit
            )
            movies = [Movie(**movie_data) for movie_data in similar_movies_data]
            explanation = (
                "Based on your request, here are some movies I think you'll enjoy:"
            )

        if not movies:
            explanation = "I couldn't find specific movies for your request. Here are some popular recommendations:"
            movies_data = self.data_loader.get_popular_movies(limit)
            titles = [movie.title for movie in movies_data]
            movies = await self.tmdb_service.batch_enrich_movies(movies_data, titles)

        return explanation, movies

    async def process_trending_request(self, limit: int = 6) -> tuple[str, List[Movie]]:
        """Get trending/popular movies."""
        movies_data = self.data_loader.get_popular_movies(limit)
        titles = [movie.title for movie in movies_data]
        movies = await self.tmdb_service.batch_enrich_movies(movies_data, titles)
        explanation = "Here are the most popular movies right now:"
        return explanation, movies

    async def process_specific_movie_query(
        self, message: str
    ) -> tuple[str, List[Movie]]:
        """Handle queries about specific movies."""
        movie_title = self.extract_movie_title(message)
        if not movie_title:
            return (
                "I couldn't identify the specific movie you're asking about. Could you mention the title more clearly?",
                [],
            )

        # Search for the specific movie
        movies_data = self.data_loader.search_movies(movie_title, 1)
        if not movies_data:
            return (
                f"I couldn't find information about '{movie_title}'. Could you check the spelling?",
                [],
            )

        movie = movies_data[0]
        enriched_movies = await self.tmdb_service.batch_enrich_movies(
            [movie], [movie.title]
        )

        if enriched_movies:
            enriched_movie = enriched_movies[0]
            explanation = f"'{enriched_movie.title}' ({enriched_movie.release_date[:4] if enriched_movie.release_date else 'N/A'}) - {enriched_movie.overview[:200]}..."
            return explanation, [enriched_movie]

        return (
            f"I found '{movie.title}' but couldn't get detailed information about it.",
            [movie],
        )

    def generate_suggestions(self, intent: str, message: str) -> List[str]:
        """Generate follow-up suggestions based on intent."""
        base_suggestions = [
            "What are some good comedy movies?",
            "Recommend movies like Inception",
            "I want something scary to watch",
            "What's trending this week?",
            "Find me a romantic movie",
        ]

        if intent == "recommendation":
            return [
                "Can you recommend movies in a specific genre?",
                "What about movies similar to this one?",
                "Show me what's trending now",
            ]
        elif intent == "genre_query":
            return [
                "What about movies in other genres?",
                "Can you recommend based on my mood?",
                "Show me similar movies to these",
            ]
        elif intent == "trending":
            return [
                "What about classic movies?",
                "Recommend based on a specific genre",
                "Find movies similar to these",
            ]

        return base_suggestions[:3]

    async def chat_recommendation(self, request: ChatRequest) -> ChatResponse:
        """Main chat processing method."""
        try:
            message = request.message.strip()
            intent = self.detect_intent(message)

            # Process based on intent
            if (
                intent == "recommendation"
                or intent == "mood_based"
                or intent == "genre_query"
            ):
                explanation, movies = await self.process_recommendation_request(message)
            elif intent == "trending":
                explanation, movies = await self.process_trending_request()
            elif intent == "specific_movie":
                explanation, movies = await self.process_specific_movie_query(message)
            else:
                # General/fallback response
                explanation = "I can help you find great movies! You can ask me to recommend movies by genre, mood, or find something similar to movies you like. What are you in the mood for?"
                movies = []

            # Generate suggestions
            suggestions = self.generate_suggestions(intent, message)

            return ChatResponse(
                response=explanation, movies=movies, suggestions=suggestions
            )

        except Exception as e:
            # Fallback response on error
            return ChatResponse(
                response="I apologize, I'm having some technical difficulties. Please try asking about movie recommendations again!",
                movies=[],
                suggestions=[
                    "Recommend me a good action movie",
                    "What are the best comedies?",
                    "What's trending now?",
                ],
            )
