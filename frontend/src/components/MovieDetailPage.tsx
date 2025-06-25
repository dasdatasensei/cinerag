import React, { useState, useEffect } from "react";
import {
  XMarkIcon,
  PlayIcon,
  PlusIcon,
  HandThumbUpIcon,
  HandThumbDownIcon,
  ShareIcon,
  ChevronLeftIcon,
  StarIcon,
} from "@heroicons/react/24/outline";
import { HandThumbUpIcon as HandThumbUpSolidIcon } from "@heroicons/react/24/solid";
import MovieCard from "./MovieCard";

interface Movie {
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

interface MovieDetailPageProps {
  movie: Movie | null;
  onClose: () => void;
  isOpen: boolean;
  recommendations?: Movie[];
  onMovieSelect?: (movie: Movie) => void;
}

const MovieDetailPage: React.FC<MovieDetailPageProps> = ({
  movie,
  onClose,
  isOpen,
  recommendations = [],
  onMovieSelect,
}) => {
  const [isLiked, setIsLiked] = useState(false);
  const [isInMyList, setIsInMyList] = useState(false);
  const [showFullOverview, setShowFullOverview] = useState(false);

  // Transform Movie to MovieCard format
  const transformMovieForCard = (movie: Movie) => ({
    id: movie.id,
    title: movie.title,
    genres: movie.genres.join("|"),
    year: new Date(movie.release_date).getFullYear(),
    rating: movie.vote_average,
    poster_url: movie.poster_path,
    overview: movie.overview,
  });

  // Mock recommendations if none provided
  const mockRecommendations: Movie[] = [
    {
      id: 1,
      title: "The Matrix",
      overview:
        "A computer hacker learns from mysterious rebels about the true nature of his reality.",
      poster_path:
        "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",
      backdrop_path:
        "https://image.tmdb.org/t/p/w1280/fNG7i7RqMErkcqhohV2a6cV1Ehy.jpg",
      release_date: "1999-03-31",
      vote_average: 8.7,
      vote_count: 23000,
      genres: ["Action", "Sci-Fi"],
      runtime: 136,
      director: "The Wachowskis",
      cast: ["Keanu Reeves", "Laurence Fishburne", "Carrie-Anne Moss"],
      language: "English",
    },
    {
      id: 2,
      title: "Inception",
      overview:
        "A thief who steals corporate secrets through dream-sharing technology.",
      poster_path:
        "https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg",
      backdrop_path:
        "https://image.tmdb.org/t/p/w1280/s3TBrRGB1iav7gFOCNx3H31MoES.jpg",
      release_date: "2010-07-16",
      vote_average: 8.8,
      vote_count: 35000,
      genres: ["Action", "Sci-Fi", "Thriller"],
      runtime: 148,
      director: "Christopher Nolan",
      cast: ["Leonardo DiCaprio", "Marion Cotillard", "Tom Hardy"],
      language: "English",
    },
    {
      id: 3,
      title: "Interstellar",
      overview:
        "A group of explorers make use of a newly discovered wormhole to surpass the limitations on human space travel.",
      poster_path:
        "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
      backdrop_path:
        "https://image.tmdb.org/t/p/w1280/rAiYTfKGqDCRIIqo664sY9XZIvQ.jpg",
      release_date: "2014-11-07",
      vote_average: 8.6,
      vote_count: 32000,
      genres: ["Adventure", "Drama", "Sci-Fi"],
      runtime: 169,
      director: "Christopher Nolan",
      cast: ["Matthew McConaughey", "Anne Hathaway", "Jessica Chastain"],
      language: "English",
    },
  ];

  const displayRecommendations =
    recommendations.length > 0 ? recommendations : mockRecommendations;

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }

    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  const handleBackgroundClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const formatRuntime = (minutes: number): string => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const renderStars = (rating: number) => {
    const stars = [];
    const fullStars = Math.floor(rating / 2);
    const hasHalfStar = rating % 2 >= 1;

    for (let i = 0; i < 5; i++) {
      if (i < fullStars) {
        stars.push(
          <StarIcon key={i} className="h-4 w-4 text-yellow-400 fill-current" />
        );
      } else if (i === fullStars && hasHalfStar) {
        stars.push(
          <div key={i} className="relative">
            <StarIcon className="h-4 w-4 text-gray-600" />
            <StarIcon className="h-4 w-4 text-yellow-400 fill-current absolute top-0 left-0 overflow-hidden w-1/2" />
          </div>
        );
      } else {
        stars.push(<StarIcon key={i} className="h-4 w-4 text-gray-600" />);
      }
    }
    return stars;
  };

  if (!isOpen || !movie) return null;

  const truncatedOverview =
    movie.overview.length > 300
      ? movie.overview.substring(0, 300) + "..."
      : movie.overview;

  return (
    <div
      className={`fixed inset-0 z-50 overflow-y-auto bg-black bg-opacity-75 smooth-scroll ${
        isOpen ? "mobile-detail-page" : ""
      }`}
      onClick={handleBackgroundClick}
    >
      <div className="min-h-screen px-2 sm:px-4 py-4 sm:py-8">
        <div className="mx-auto max-w-4xl bg-[#141414] rounded-lg shadow-xl overflow-hidden">
          {/* Header with backdrop - Mobile Enhanced */}
          <div className="relative h-64 sm:h-80 md:h-96 bg-gradient-to-r from-black to-transparent mobile-detail-header">
            <img
              src={movie.backdrop_path || movie.poster_path}
              alt={movie.title}
              className="w-full h-full object-cover"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.src =
                  "https://via.placeholder.com/1280x720/1f2937/9ca3af?text=No+Image";
              }}
            />
            <div className="absolute inset-0 bg-gradient-to-t from-[#141414] via-transparent to-transparent" />
            <div className="absolute inset-0 bg-gradient-to-r from-black via-transparent to-transparent" />

            {/* Close button - Mobile Friendly */}
            <button
              onClick={onClose}
              className="absolute top-3 right-3 sm:top-4 sm:right-4 p-2 sm:p-3 bg-black bg-opacity-50 rounded-full text-white hover:bg-opacity-75 transition-all duration-200 touch-interactive mobile-tap-target"
              aria-label="Close"
            >
              <XMarkIcon className="h-5 w-5 sm:h-6 sm:w-6" />
            </button>

            {/* Back button - Mobile Enhanced */}
            <button
              onClick={onClose}
              className="absolute top-3 left-3 sm:top-4 sm:left-4 p-2 sm:p-3 bg-black bg-opacity-50 rounded-full text-white hover:bg-opacity-75 transition-all duration-200 flex items-center space-x-1 sm:space-x-2 touch-interactive mobile-tap-target"
              aria-label="Go back"
            >
              <ChevronLeftIcon className="h-4 w-4 sm:h-5 sm:w-5" />
              <span className="text-xs sm:text-sm font-medium hidden sm:inline">
                Back
              </span>
            </button>

            {/* Movie info overlay - Mobile Responsive */}
            <div className="absolute bottom-0 left-0 right-0 p-3 sm:p-6 md:p-8 mobile-detail-content">
              <div className="flex flex-col sm:flex-row items-start space-y-3 sm:space-y-0 sm:space-x-4 md:space-x-6">
                <img
                  src={movie.poster_path}
                  alt={movie.title}
                  className="w-20 h-30 sm:w-28 sm:h-42 md:w-32 md:h-48 object-cover rounded-lg shadow-lg flex-shrink-0 mx-auto sm:mx-0"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.src =
                      "https://via.placeholder.com/300x450/1f2937/9ca3af?text=No+Poster";
                  }}
                />
                <div className="flex-1 min-w-0 text-center sm:text-left">
                  <h1 className="text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-2">
                    {movie.title}
                  </h1>
                  <div className="flex items-center justify-center sm:justify-start space-x-4 mb-3 md:mb-4">
                    <div className="flex items-center space-x-1">
                      {renderStars(movie.vote_average)}
                      <span className="text-gray-300 text-xs sm:text-sm ml-2">
                        {movie.vote_average.toFixed(1)} (
                        {movie.vote_count.toLocaleString()} votes)
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center justify-center sm:justify-start space-x-2 sm:space-x-4 text-gray-300 text-xs sm:text-sm mb-3 md:mb-4">
                    <span>{new Date(movie.release_date).getFullYear()}</span>
                    <span>•</span>
                    <span>{formatRuntime(movie.runtime)}</span>
                    <span>•</span>
                    <span className="bg-gray-700 px-2 py-1 rounded text-xs">
                      HD
                    </span>
                  </div>
                  <div className="flex flex-wrap justify-center sm:justify-start gap-2 mb-3 md:mb-4">
                    {movie.genres.map((genre) => (
                      <span
                        key={genre}
                        className="px-2 sm:px-3 py-1 bg-gray-700 text-gray-300 text-xs sm:text-sm rounded-full"
                      >
                        {genre}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Action buttons - Mobile Enhanced */}
          <div className="px-3 sm:px-6 md:px-8 py-4 sm:py-6 border-b border-gray-800">
            <div className="flex items-center justify-center sm:justify-start space-x-3 sm:space-x-4 overflow-x-auto">
              <button className="btn-netflix-primary touch-interactive mobile-tap-target flex items-center space-x-2 px-4 sm:px-6 py-2 sm:py-3 text-sm sm:text-base whitespace-nowrap">
                <PlayIcon className="h-4 w-4 sm:h-5 sm:w-5" />
                <span>Play</span>
              </button>
              <button
                onClick={() => setIsInMyList(!isInMyList)}
                className={`p-2 sm:p-3 border border-gray-600 rounded-full hover:border-white transition-colors duration-200 touch-interactive mobile-tap-target ${
                  isInMyList ? "bg-white text-black" : "text-white"
                }`}
              >
                <PlusIcon className="h-4 w-4 sm:h-5 sm:w-5" />
              </button>
              <button
                onClick={() => setIsLiked(!isLiked)}
                className="p-2 sm:p-3 border border-gray-600 rounded-full hover:border-white transition-colors duration-200 text-white touch-interactive mobile-tap-target"
              >
                {isLiked ? (
                  <HandThumbUpSolidIcon className="h-4 w-4 sm:h-5 sm:w-5 text-green-500" />
                ) : (
                  <HandThumbUpIcon className="h-4 w-4 sm:h-5 sm:w-5" />
                )}
              </button>
              <button className="p-2 sm:p-3 border border-gray-600 rounded-full hover:border-white transition-colors duration-200 text-white touch-interactive mobile-tap-target">
                <HandThumbDownIcon className="h-4 w-4 sm:h-5 sm:w-5" />
              </button>
              <button className="p-2 sm:p-3 border border-gray-600 rounded-full hover:border-white transition-colors duration-200 text-white touch-interactive mobile-tap-target">
                <ShareIcon className="h-4 w-4 sm:h-5 sm:w-5" />
              </button>
            </div>
          </div>

          {/* Movie details - Mobile Responsive */}
          <div className="px-3 sm:px-6 md:px-8 py-4 sm:py-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 sm:gap-8">
              {/* Main content */}
              <div className="lg:col-span-2">
                <h2 className="text-lg sm:text-xl font-semibold text-white mb-3 sm:mb-4">
                  Synopsis
                </h2>
                <p className="text-gray-300 leading-relaxed mb-4 text-sm sm:text-base">
                  {showFullOverview ? movie.overview : truncatedOverview}
                  {movie.overview.length > 300 && (
                    <button
                      onClick={() => setShowFullOverview(!showFullOverview)}
                      className="text-red-500 hover:text-red-400 ml-2 font-medium touch-interactive"
                    >
                      {showFullOverview ? "Show less" : "Read more"}
                    </button>
                  )}
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6 mt-6 sm:mt-8">
                  <div>
                    <h3 className="text-base sm:text-lg font-semibold text-white mb-2 sm:mb-3">
                      Cast
                    </h3>
                    <div className="space-y-1">
                      {movie.cast.slice(0, 5).map((actor, index) => (
                        <p
                          key={index}
                          className="text-gray-300 text-sm sm:text-base"
                        >
                          {actor}
                        </p>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h3 className="text-base sm:text-lg font-semibold text-white mb-2 sm:mb-3">
                      Details
                    </h3>
                    <div className="space-y-2 text-gray-300 text-sm sm:text-base">
                      <p>
                        <span className="text-gray-400">Director:</span>{" "}
                        {movie.director}
                      </p>
                      <p>
                        <span className="text-gray-400">Language:</span>{" "}
                        {movie.language}
                      </p>
                      <p>
                        <span className="text-gray-400">Runtime:</span>{" "}
                        {formatRuntime(movie.runtime)}
                      </p>
                      {movie.budget && (
                        <p>
                          <span className="text-gray-400">Budget:</span>{" "}
                          {formatCurrency(movie.budget)}
                        </p>
                      )}
                      {movie.revenue && (
                        <p>
                          <span className="text-gray-400">Revenue:</span>{" "}
                          {formatCurrency(movie.revenue)}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Sidebar - Mobile Stack */}
              <div>
                <h3 className="text-base sm:text-lg font-semibold text-white mb-3 sm:mb-4">
                  More Like This
                </h3>
                <div className="space-y-3 sm:space-y-4">
                  {displayRecommendations.slice(0, 3).map((recMovie) => (
                    <div
                      key={recMovie.id}
                      onClick={() => onMovieSelect && onMovieSelect(recMovie)}
                      className="card-netflix touch-interactive cursor-pointer hover:bg-gray-700 transition-colors duration-200 p-3 sm:p-4"
                    >
                      <div className="flex space-x-3">
                        <img
                          src={recMovie.poster_path}
                          alt={recMovie.title}
                          className="w-12 h-18 sm:w-16 sm:h-24 object-cover rounded flex-shrink-0"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.src =
                              "https://via.placeholder.com/150x225/1f2937/9ca3af?text=No+Image";
                          }}
                        />
                        <div className="flex-1 min-w-0">
                          <h4 className="text-white font-medium mb-1 truncate text-sm sm:text-base">
                            {recMovie.title}
                          </h4>
                          <div className="flex items-center space-x-1 mb-2">
                            {renderStars(recMovie.vote_average).slice(0, 5)}
                            <span className="text-gray-400 text-xs ml-1">
                              {recMovie.vote_average.toFixed(1)}
                            </span>
                          </div>
                          <p className="text-gray-400 text-xs sm:text-sm line-clamp-2">
                            {recMovie.overview.substring(0, 80)}...
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Full recommendations section - Mobile Responsive */}
          <div className="px-3 sm:px-6 md:px-8 py-4 sm:py-6 border-t border-gray-800">
            <h2 className="text-xl sm:text-2xl font-bold text-white mb-4 sm:mb-6">
              More Like This
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3 sm:gap-4 mobile-movie-grid">
              {displayRecommendations.map((recMovie) => (
                <div
                  key={recMovie.id}
                  className="touch-interactive card-touch"
                  onClick={() => onMovieSelect && onMovieSelect(recMovie)}
                >
                  <MovieCard
                    movie={transformMovieForCard(recMovie)}
                    onMovieClick={() =>
                      onMovieSelect && onMovieSelect(recMovie)
                    }
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MovieDetailPage;
