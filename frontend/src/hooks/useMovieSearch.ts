import { useState, useEffect, useCallback, useRef } from "react";
import CineRagApiService, { Movie, ApiError } from "../services/api";

interface UseMovieSearchReturn {
  movies: Movie[];
  loading: boolean;
  error: string | null;
  searchQuery: string;
  selectedGenre: string;
  hasSearched: boolean;

  setSearchQuery: (query: string) => void;
  setSelectedGenre: (genre: string) => void;
  clearSearch: () => void;
  refetch: () => Promise<void>;
}

const useMovieSearch = (): UseMovieSearchReturn => {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedGenre, setSelectedGenre] = useState("all");
  const [hasSearched, setHasSearched] = useState(false);

  // Debounce timeout ref
  const debounceRef = useRef<NodeJS.Timeout | null>(null);

  const fetchMovies = useCallback(async (query: string, genre: string) => {
    try {
      setLoading(true);
      setError(null);

      let fetchedMovies: Movie[];

      if (query.trim()) {
        // Use semantic search for queries
        fetchedMovies = await CineRagApiService.searchMovies(query, 20, true);
        setHasSearched(true);
      } else if (genre !== "all") {
        // Get movies by genre
        fetchedMovies = await CineRagApiService.getMoviesByGenre(genre, 20);
      } else {
        // Get popular movies
        fetchedMovies = await CineRagApiService.getPopularMovies(20);
      }

      setMovies(fetchedMovies);
    } catch (err) {
      console.error("Error fetching movies:", err);
      if (err instanceof ApiError) {
        if (err.status === 0) {
          setError(
            "Unable to connect to server. Please check that the backend is running."
          );
        } else {
          setError(`Server error: ${err.message}`);
        }
      } else {
        setError("An unexpected error occurred. Please try again.");
      }
      setMovies([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial load effect
  useEffect(() => {
    fetchMovies("", "all");
  }, [fetchMovies]);

  // Debounced search effect
  useEffect(() => {
    // Clear any existing timeout
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    // If we have a search query, debounce the search
    if (searchQuery.trim()) {
      debounceRef.current = setTimeout(() => {
        fetchMovies(searchQuery, selectedGenre);
      }, 300); // 300ms debounce
    } else if (selectedGenre !== "all") {
      // If no search query but genre is selected, fetch immediately
      fetchMovies(searchQuery, selectedGenre);
    }

    // Cleanup timeout on unmount
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [searchQuery, selectedGenre, fetchMovies]);

  // Clear search function
  const clearSearch = useCallback(() => {
    setSearchQuery("");
    setHasSearched(false);
  }, []);

  // Refetch function for manual retries
  const refetch = useCallback(async () => {
    return fetchMovies(searchQuery, selectedGenre);
  }, [searchQuery, selectedGenre, fetchMovies]);

  return {
    movies,
    loading,
    error,
    searchQuery,
    selectedGenre,
    hasSearched,
    setSearchQuery,
    setSelectedGenre,
    clearSearch,
    refetch,
  };
};

export default useMovieSearch;
