const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// Backend API Movie interface (matches your Pydantic model)
export interface ApiMovie {
  id: number;
  title: string;
  overview: string;
  poster_path: string | null;
  backdrop_path: string | null;
  release_date: string | null;
  vote_average: number;
  vote_count: number;
  genres: string[];
  runtime: number | null;
  tmdb_id: number | null;
  imdb_id: string | null;
}

// Frontend Movie interface
export interface Movie {
  id: number;
  title: string;
  genres: string;
  year?: number;
  rating?: number;
  poster_url?: string;
  overview?: string;
}

// Frontend DetailMovie interface
export interface DetailMovie {
  id: number;
  title: string;
  overview: string;
  poster_path: string;
  backdrop_path: string;
  release_date: string;
  vote_average: number;
  vote_count: number;
  genres: string[];
  runtime: number;
  director: string;
  cast: string[];
  language: string;
  budget?: number;
  revenue?: number;
}

// Chat interfaces
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  movies?: Movie[];
}

export interface ChatRequest {
  message: string;
  user_id?: number;
  conversation_history: Array<{
    role: string;
    content: string;
  }>;
}

export interface ChatResponse {
  response: string;
  movies: ApiMovie[];
  suggestions: string[];
}

// Transform API movie data to frontend format
export const transformApiMovie = (apiMovie: ApiMovie): Movie => ({
  id: apiMovie.id,
  title: apiMovie.title,
  genres: apiMovie.genres.join("|"),
  year: apiMovie.release_date
    ? new Date(apiMovie.release_date).getFullYear()
    : undefined,
  rating: apiMovie.vote_average,
  poster_url: apiMovie.poster_path || undefined,
  overview: apiMovie.overview,
});

// Transform API movie to detailed movie format
export const transformToDetailMovie = (apiMovie: ApiMovie): DetailMovie => ({
  id: apiMovie.id,
  title: apiMovie.title,
  overview: apiMovie.overview || "No overview available for this movie.",
  poster_path:
    apiMovie.poster_path ||
    `https://via.placeholder.com/300x450/1f2937/9ca3af?text=${encodeURIComponent(
      apiMovie.title
    )}`,
  backdrop_path:
    apiMovie.backdrop_path ||
    apiMovie.poster_path ||
    `https://via.placeholder.com/1280x720/1f2937/9ca3af?text=${encodeURIComponent(
      apiMovie.title
    )}`,
  release_date: apiMovie.release_date || "2023-01-01",
  vote_average: apiMovie.vote_average,
  vote_count: apiMovie.vote_count,
  genres: apiMovie.genres,
  runtime: apiMovie.runtime || Math.floor(Math.random() * 60) + 90,
  director: "Unknown Director", // These would come from TMDB enrichment
  cast: ["Unknown Actor 1", "Unknown Actor 2", "Unknown Actor 3"],
  language: "English",
  budget: Math.floor(Math.random() * 100000000) + 10000000,
  revenue: Math.floor(Math.random() * 200000000) + 50000000,
});

// API Error handling
export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

// Generic API request helper
const apiRequest = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Unknown error" }));
      throw new ApiError(
        response.status,
        errorData.detail || `HTTP ${response.status}`
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    // Network or other errors
    throw new ApiError(
      0,
      `Network error: ${
        error instanceof Error ? error.message : "Unknown error"
      }`
    );
  }
};

// API Service class
export class CineRagApiService {
  // Health check
  static async healthCheck(): Promise<{
    status: string;
    rag_enabled: boolean;
  }> {
    return apiRequest("/health");
  }

  // Get popular movies
  static async getPopularMovies(
    limit: number = 20,
    genre?: string
  ): Promise<Movie[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      ...(genre && genre !== "all" && { genre }),
    });

    const apiMovies: ApiMovie[] = await apiRequest(
      `/api/movies/popular?${params}`
    );
    return apiMovies.map(transformApiMovie);
  }

  // Search movies (with semantic search option)
  static async searchMovies(
    query: string,
    limit: number = 20,
    semantic: boolean = true
  ): Promise<Movie[]> {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString(),
      semantic: semantic.toString(),
    });

    const apiMovies: ApiMovie[] = await apiRequest(
      `/api/movies/search?${params}`
    );
    return apiMovies.map(transformApiMovie);
  }

  // Get movie by ID
  static async getMovieById(id: number): Promise<DetailMovie> {
    const apiMovie: ApiMovie = await apiRequest(`/api/movies/${id}`);
    return transformToDetailMovie(apiMovie);
  }

  // Get similar movies
  static async getSimilarMovies(
    movieId: number,
    limit: number = 10
  ): Promise<DetailMovie[]> {
    const apiMovies: ApiMovie[] = await apiRequest(
      `/api/movies/${movieId}/similar?limit=${limit}`
    );
    return apiMovies.map(transformToDetailMovie);
  }

  // Get movies by genre
  static async getMoviesByGenre(
    genre: string,
    limit: number = 20
  ): Promise<Movie[]> {
    const apiMovies: ApiMovie[] = await apiRequest(
      `/api/movies/genre/${genre}?limit=${limit}`
    );
    return apiMovies.map(transformApiMovie);
  }

  // Get available genres
  static async getGenres(): Promise<string[]> {
    return apiRequest("/api/genres");
  }

  // Vector search with filters
  static async vectorSearch(
    query: string,
    limit: number = 20,
    genre?: string
  ): Promise<Movie[]> {
    const params = new URLSearchParams({
      query,
      limit: limit.toString(),
      ...(genre && genre !== "all" && { genre }),
    });

    const apiMovies: ApiMovie[] = await apiRequest(
      `/api/vector/search?${params}`
    );
    return apiMovies.map(transformApiMovie);
  }

  // Chat with AI assistant
  static async sendChatMessage(
    message: string,
    conversationHistory: Array<{ role: string; content: string }> = [],
    userId?: number
  ): Promise<ChatResponse> {
    const chatRequest: ChatRequest = {
      message,
      conversation_history: conversationHistory,
      ...(userId && { user_id: userId }),
    };

    return apiRequest("/api/chat", {
      method: "POST",
      body: JSON.stringify(chatRequest),
    });
  }
}

export default CineRagApiService;
