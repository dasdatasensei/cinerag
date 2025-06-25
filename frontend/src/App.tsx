import React, { useState, useEffect } from "react";
import {
  Header,
  MovieCard,
  MovieCardSkeleton,
  MovieDetailPage,
  ChatInterface,
  Footer,
} from "./components";
import { ChatBubbleOvalLeftEllipsisIcon } from "@heroicons/react/24/outline";
import useMovieSearch from "./hooks/useMovieSearch";
import CineRagApiService from "./services/api";
import "./App.css";

interface Movie {
  id: number;
  title: string;
  genres: string;
  year?: number;
  rating?: number;
  poster_url?: string;
  overview?: string;
}

interface DetailMovie {
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

function App() {
  const {
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
  } = useMovieSearch();

  const [selectedMovie, setSelectedMovie] = useState<DetailMovie | null>(null);
  const [isDetailPageOpen, setIsDetailPageOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [isChatOpen, setIsChatOpen] = useState(false);

  useEffect(() => {
    // Add initial load animation delay
    const timer = setTimeout(() => {
      setIsInitialLoad(false);
    }, 500);
    return () => clearTimeout(timer);
  }, []);

  const genres = [
    {
      id: "all",
      name: "All Genres",
      emoji: "🎬",
      color: "from-slate-600 to-slate-700",
      description: "Discover all movies",
    },
    {
      id: "action",
      name: "Action",
      emoji: "⚡",
      color: "from-orange-600 to-red-600",
      description: "High-octane thrills",
    },
    {
      id: "comedy",
      name: "Comedy",
      emoji: "😂",
      color: "from-yellow-500 to-orange-500",
      description: "Laugh out loud",
    },
    {
      id: "drama",
      name: "Drama",
      emoji: "🎭",
      color: "from-purple-600 to-pink-600",
      description: "Emotional stories",
    },
    {
      id: "horror",
      name: "Horror",
      emoji: "👻",
      color: "from-gray-700 to-gray-900",
      description: "Spine-chilling fear",
    },
    {
      id: "sci-fi",
      name: "Sci-Fi",
      emoji: "🚀",
      color: "from-blue-600 to-purple-600",
      description: "Future possibilities",
    },
    {
      id: "romance",
      name: "Romance",
      emoji: "💕",
      color: "from-pink-500 to-rose-500",
      description: "Love stories",
    },
  ];

  const handleSearch = (query: string) => {
    setSearchQuery(query);
  };

  const handleClearSearch = () => {
    clearSearch();
  };

  const handleGenreChange = (genreId: string) => {
    setSelectedGenre(genreId);
  };

  const handleMovieClick = async (movie: Movie) => {
    setDetailLoading(true);

    try {
      const detailMovie = await CineRagApiService.getMovieById(movie.id);
      setSelectedMovie(detailMovie);
      setIsDetailPageOpen(true);
    } catch (err) {
      console.error("Error fetching movie details:", err);
      const fallbackMovie = {
        id: movie.id,
        title: movie.title,
        overview: movie.overview || "No overview available for this movie.",
        poster_path:
          movie.poster_url ||
          `https://via.placeholder.com/300x450/1f2937/9ca3af?text=${encodeURIComponent(
            movie.title
          )}`,
        backdrop_path:
          movie.poster_url ||
          `https://via.placeholder.com/1280x720/1f2937/9ca3af?text=${encodeURIComponent(
            movie.title
          )}`,
        release_date: movie.year ? `${movie.year}-01-01` : "2023-01-01",
        vote_average: movie.rating || 7.5,
        vote_count: Math.floor(Math.random() * 50000) + 5000,
        genres: movie.genres ? movie.genres.split("|") : ["Drama"],
        runtime: Math.floor(Math.random() * 60) + 90,
        director: "Unknown Director",
        cast: ["Unknown Actor 1", "Unknown Actor 2", "Unknown Actor 3"],
        language: "English",
        budget: Math.floor(Math.random() * 100000000) + 10000000,
        revenue: Math.floor(Math.random() * 200000000) + 50000000,
      };
      setSelectedMovie(fallbackMovie);
      setIsDetailPageOpen(true);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCloseDetailPage = () => {
    setIsDetailPageOpen(false);
    setSelectedMovie(null);
  };

  const handleMovieSelect = async (movie: DetailMovie) => {
    setSelectedMovie(movie);
  };

  const handleChatOpen = () => {
    setIsChatOpen(true);
  };

  const handleChatClose = () => {
    setIsChatOpen(false);
  };

  const handleChatMovieClick = (movie: any) => {
    handleMovieClick(movie);
    setIsChatOpen(false);
  };

  const isEmpty = !loading && movies.length === 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-black to-gray-950 text-white relative overflow-x-hidden">
      {/* Animated Background Effects */}
      <div className="fixed inset-0 opacity-30 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-red-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-1/3 right-1/4 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl animate-pulse animate-delay-200"></div>
        <div className="absolute bottom-1/4 left-1/3 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl animate-pulse animate-delay-400"></div>
      </div>

      {/* Grain texture overlay */}
      <div className="fixed inset-0 opacity-[0.03] bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZGVmcz48ZmlsdGVyIGlkPSJub2lzZSI+PGZlVHVyYnVsZW5jZSB0eXBlPSJmcmFjdGFsTm9pc2UiIGJhc2VGcmVxdWVuY3k9IjAuOSIgbnVtT2N0YXZlcz0iNCIvPjwvZmlsdGVyPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWx0ZXI9InVybCgjbm9pc2UpIiBvcGFjaXR5PSIwLjEiLz48L3N2Zz4=')] pointer-events-none"></div>

      {/* Header */}
      <Header
        onSearch={handleSearch}
        searchQuery={searchQuery}
        onClearSearch={handleClearSearch}
      />

      <main className="relative z-10">
        {/* Hero Section */}
        <section className="relative pt-20 pb-12 md:pt-28 md:pb-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
            <div
              className={`text-center ${
                isInitialLoad ? "opacity-0" : "animate-fade-in-up"
              }`}
            >
              <div className="mb-8">
                <h1 className="text-4xl md:text-6xl lg:text-7xl font-display font-bold mb-6">
                  <span className="text-gradient">Cine</span>
                  <span className="text-white">RAG</span>
                </h1>
                <p className="text-xl md:text-2xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
                  Discover your next favorite movie with AI-powered
                  recommendations
                </p>
              </div>

              {!hasSearched && (
                <div className="animate-fade-in-up animate-delay-300">
                  <p className="text-gray-400 mb-8 text-lg">
                    Start by searching for a movie or browse by genre
                  </p>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Genre Filters */}
        <section className="relative z-10 pb-8">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="overflow-x-auto pb-4">
              <div className="flex space-x-4 min-w-max">
                {genres.map((genre, index) => (
                  <button
                    key={genre.id}
                    onClick={() => handleGenreChange(genre.id)}
                    className={`
                      flex-shrink-0 group relative overflow-hidden rounded-2xl p-4 min-w-[160px]
                      transition-all duration-300 transform hover:scale-105 hover:shadow-xl
                      animate-fade-in-scale animate-delay-${index * 100 + 200}
                      ${
                        selectedGenre === genre.id
                          ? `bg-gradient-to-r ${genre.color} shadow-lg`
                          : "glass hover:bg-white/10"
                      }
                    `}
                  >
                    <div className="text-center">
                      <div className="text-2xl mb-2 transform group-hover:scale-110 transition-transform duration-200">
                        {genre.emoji}
                      </div>
                      <div className="font-semibold text-white mb-1">
                        {genre.name}
                      </div>
                      <div className="text-xs text-gray-300 opacity-80">
                        {genre.description}
                      </div>
                    </div>

                    {/* Animated border */}
                    <div
                      className={`
                      absolute inset-0 rounded-2xl border-2 border-transparent
                      ${selectedGenre === genre.id ? "border-white/30" : ""}
                      transition-all duration-300
                    `}
                    ></div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Content Area */}
        <section className="relative z-10 pb-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            {/* Search Status */}
            {hasSearched && (
              <div className="mb-8 animate-fade-in-up">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-2">
                      {searchQuery ? (
                        <>Search results for "{searchQuery}"</>
                      ) : (
                        <>
                          {selectedGenre === "all"
                            ? "All Movies"
                            : genres.find((g) => g.id === selectedGenre)
                                ?.name || "Movies"}
                        </>
                      )}
                    </h2>
                    {!loading && (
                      <p className="text-gray-400">
                        {movies.length}{" "}
                        {movies.length === 1 ? "movie" : "movies"} found
                      </p>
                    )}
                  </div>

                  {(searchQuery || selectedGenre !== "all") && (
                    <button
                      onClick={handleClearSearch}
                      className="btn-secondary text-sm"
                    >
                      Clear Filters
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="grid grid-auto-fill gap-6">
                {Array.from({ length: 12 }).map((_, index) => (
                  <div
                    key={index}
                    className={`animate-fade-in-scale animate-delay-${
                      (index % 6) * 100
                    }`}
                  >
                    <MovieCardSkeleton />
                  </div>
                ))}
              </div>
            )}

            {/* Error State */}
            {error && (
              <div className="text-center py-16 animate-fade-in-up">
                <div className="glass rounded-2xl p-8 max-w-md mx-auto">
                  <div className="text-red-400 text-5xl mb-4">⚠️</div>
                  <h3 className="text-xl font-semibold text-white mb-2">
                    Something went wrong
                  </h3>
                  <p className="text-gray-400 mb-6">
                    {error || "Unable to load movies. Please try again."}
                  </p>
                  <button onClick={refetch} className="btn-primary">
                    Try Again
                  </button>
                </div>
              </div>
            )}

            {/* Empty State */}
            {isEmpty && hasSearched && !loading && (
              <div className="text-center py-16 animate-fade-in-up">
                <div className="glass rounded-2xl p-8 max-w-md mx-auto">
                  <div className="text-gray-400 text-5xl mb-4">🎬</div>
                  <h3 className="text-xl font-semibold text-white mb-2">
                    No movies found
                  </h3>
                  <p className="text-gray-400 mb-6">
                    Try searching for a different movie or changing your
                    filters.
                  </p>
                  <button onClick={handleClearSearch} className="btn-secondary">
                    Clear Search
                  </button>
                </div>
              </div>
            )}

            {/* Movies Grid */}
            {!loading && movies.length > 0 && (
              <div className="grid grid-auto-fill gap-6">
                {movies.map((movie, index) => (
                  <div
                    key={movie.id}
                    className={`animate-fade-in-scale animate-delay-${
                      (index % 12) * 50
                    }`}
                  >
                    <MovieCard
                      movie={movie}
                      onMovieClick={() => handleMovieClick(movie)}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* Footer */}
        <Footer />
      </main>

      {/* Floating Chat Button */}
      <button
        onClick={handleChatOpen}
        className={`
          fixed bottom-6 right-6 z-40 p-4 bg-gradient-to-r from-red-600 to-red-700
          text-white rounded-full shadow-xl hover:shadow-2xl
          transform transition-all duration-300 hover:scale-110 active:scale-95
          ${isChatOpen ? "opacity-0 pointer-events-none" : "opacity-100"}
        `}
        aria-label="Open chat"
      >
        <ChatBubbleOvalLeftEllipsisIcon className="w-6 h-6" />

        {/* Pulse animation */}
        <div className="absolute inset-0 rounded-full bg-red-500 animate-ping opacity-20"></div>

        {/* Notification dot */}
        <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-gray-900"></div>
      </button>

      {/* Chat Interface */}
      <ChatInterface
        isOpen={isChatOpen}
        onClose={handleChatClose}
        onMovieClick={handleChatMovieClick}
      />

      {/* Movie Detail Modal */}
      {isDetailPageOpen && selectedMovie && (
        <MovieDetailPage
          movie={selectedMovie}
          onClose={handleCloseDetailPage}
          onMovieSelect={handleMovieSelect}
          isOpen={isDetailPageOpen}
        />
      )}
    </div>
  );
}

export default App;
