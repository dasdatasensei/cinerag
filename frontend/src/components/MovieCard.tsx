import React, { useState } from "react";
import {
  PlayIcon,
  PlusIcon,
  HeartIcon,
  CalendarIcon,
} from "@heroicons/react/24/outline";
import {
  StarIcon as StarSolidIcon,
  HeartIcon as HeartSolidIcon,
} from "@heroicons/react/24/solid";

interface Movie {
  id: number;
  title: string;
  genres: string;
  year?: number;
  rating?: number;
  poster_url?: string;
  overview?: string;
}

interface MovieCardProps {
  movie: Movie;
  onMovieClick: (movie: Movie) => void;
}

const MovieCard: React.FC<MovieCardProps> = ({ movie, onMovieClick }) => {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [isLiked, setIsLiked] = useState(false);
  const [isAdded, setIsAdded] = useState(false);

  const getPosterUrl = (movie: Movie): string => {
    if (movie.poster_url && !imageError) {
      return movie.poster_url;
    }

    // Modern gradient colors for placeholders - using SVG for better quality
    return `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="450" viewBox="0 0 300 450"><defs><linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:%23374151"/><stop offset="100%" style="stop-color:%230F172A"/></linearGradient></defs><rect width="300" height="450" fill="url(%23grad)"/><text x="150" y="225" text-anchor="middle" font-family="Inter, system-ui, sans-serif" font-size="16" font-weight="600" fill="%239CA3AF">${encodeURIComponent(
      movie.title.length > 25
        ? movie.title.substring(0, 22) + "..."
        : movie.title
    )}</text></svg>`;
  };

  const handleClick = () => {
    onMovieClick(movie);
  };

  const handleImageLoad = () => {
    setImageLoaded(true);
  };

  const handleImageError = () => {
    setImageError(true);
    setImageLoaded(true);
  };

  const handleLike = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsLiked(!isLiked);
  };

  const handleAddToList = (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsAdded(!isAdded);
  };

  const getRatingColor = (rating: number) => {
    if (rating >= 8) return "from-emerald-400 to-emerald-500";
    if (rating >= 7) return "from-yellow-400 to-yellow-500";
    if (rating >= 6) return "from-orange-400 to-orange-500";
    return "from-red-400 to-red-500";
  };

  const getGenreColor = (genre: string) => {
    const colors = {
      Action: "from-red-500 to-red-600",
      Comedy: "from-yellow-500 to-orange-500",
      Drama: "from-purple-500 to-purple-600",
      Horror: "from-gray-600 to-gray-800",
      "Sci-Fi": "from-blue-500 to-blue-600",
      Romance: "from-pink-500 to-rose-500",
      Thriller: "from-gray-500 to-gray-700",
      Fantasy: "from-indigo-500 to-purple-600",
      Adventure: "from-green-500 to-teal-600",
    };
    return colors[genre as keyof typeof colors] || "from-gray-500 to-gray-600";
  };

  const primaryGenre = movie.genres ? movie.genres.split("|")[0] : "Drama";

  return (
    <div
      className="group relative cursor-pointer transform transition-all duration-500 hover-lift"
      onClick={handleClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Main Card Container */}
      <div className="relative card-hover rounded-2xl overflow-hidden shadow-xl group-hover:shadow-2xl">
        {/* Poster Container */}
        <div className="relative aspect-[2/3] overflow-hidden bg-gray-900">
          {/* Background Image */}
          <img
            src={getPosterUrl(movie)}
            alt={movie.title}
            className={`
              w-full h-full object-cover transition-all duration-700
              ${imageLoaded ? "opacity-100 scale-100" : "opacity-0 scale-110"}
              group-hover:scale-110
            `}
            onLoad={handleImageLoad}
            onError={handleImageError}
            loading="lazy"
          />

          {/* Loading State */}
          {!imageLoaded && (
            <div className="absolute inset-0 flex items-center justify-center bg-gray-800">
              <div className="loading-spin w-8 h-8 border-2 border-gray-600 border-t-red-500 rounded-full"></div>
            </div>
          )}

          {/* Gradient Overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-60"></div>

          {/* Top Badges */}
          <div className="absolute top-3 left-0 right-0 flex justify-between items-start px-3">
            {/* Quality Badge */}
            <div className="bg-gradient-to-r from-red-600 to-red-700 text-white text-xs font-bold px-2 py-1 rounded-md shadow-lg">
              HD
            </div>

            {/* Rating Badge */}
            {movie.rating && (
              <div
                className={`
                bg-gradient-to-r ${getRatingColor(
                  movie.rating
                )} text-white text-xs font-bold
                px-2 py-1 rounded-md flex items-center space-x-1 shadow-lg
              `}
              >
                <StarSolidIcon className="w-3 h-3" />
                <span>{movie.rating.toFixed(1)}</span>
              </div>
            )}
          </div>

          {/* Hover Actions */}
          <div
            className={`
            absolute inset-0 flex items-center justify-center transition-all duration-300
            ${isHovered ? "opacity-100" : "opacity-0"}
          `}
          >
            <div className="flex space-x-3">
              {/* Play Button */}
              <button
                onClick={handleClick}
                className="
                  group/btn p-4 bg-white/90 hover:bg-white rounded-full
                  transition-all duration-300 transform hover:scale-110 shadow-xl
                "
              >
                <PlayIcon className="h-6 w-6 text-black group-hover/btn:scale-110 transition-transform duration-200" />
              </button>

              {/* Add to List */}
              <button
                onClick={handleAddToList}
                className={`
                  group/btn p-3 rounded-full transition-all duration-300 transform hover:scale-110 shadow-xl
                  ${
                    isAdded
                      ? "bg-green-500/90 hover:bg-green-500"
                      : "bg-black/70 hover:bg-black/80"
                  }
                `}
              >
                <PlusIcon
                  className={`
                  h-5 w-5 transition-all duration-200
                  ${
                    isAdded
                      ? "text-white rotate-45"
                      : "text-white group-hover/btn:scale-110"
                  }
                `}
                />
              </button>

              {/* Like Button */}
              <button
                onClick={handleLike}
                className="
                  group/btn p-3 bg-black/70 hover:bg-black/80 rounded-full
                  transition-all duration-300 transform hover:scale-110 shadow-xl
                "
              >
                {isLiked ? (
                  <HeartSolidIcon className="h-5 w-5 text-red-500" />
                ) : (
                  <HeartIcon className="h-5 w-5 text-white group-hover/btn:scale-110 transition-transform duration-200" />
                )}
              </button>
            </div>
          </div>

          {/* New/Popular Indicator */}
          {movie.year && movie.year >= 2024 && (
            <div className="absolute bottom-3 right-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-xs font-bold px-3 py-1 rounded-full animate-pulse">
              NEW
            </div>
          )}
        </div>

        {/* Movie Information */}
        <div className="p-4 space-y-3 bg-gradient-to-b from-gray-900/95 to-black/95">
          {/* Title */}
          <h3
            className="
            text-white font-bold text-base leading-tight transition-all duration-300
            group-hover:text-gradient line-clamp-2
          "
          >
            {movie.title}
          </h3>

          {/* Metadata Row */}
          <div className="flex items-center justify-between text-xs">
            {/* Year */}
            <div className="flex items-center space-x-1 text-gray-400">
              <CalendarIcon className="w-3 h-3" />
              <span>{movie.year || "N/A"}</span>
            </div>

            {/* Genre */}
            <div
              className={`
              bg-gradient-to-r ${getGenreColor(primaryGenre)}
              text-white px-2 py-1 rounded-md text-xs font-medium
            `}
            >
              {primaryGenre}
            </div>
          </div>

          {/* Overview Preview (on hover) */}
          {movie.overview && (
            <div
              className={`
              transition-all duration-300 overflow-hidden
              ${isHovered ? "max-h-20 opacity-100" : "max-h-0 opacity-0"}
            `}
            >
              <p className="text-gray-300 text-xs leading-relaxed line-clamp-3">
                {movie.overview}
              </p>
            </div>
          )}

          {/* Action Bar */}
          <div
            className={`
            flex items-center justify-between pt-2 border-t border-gray-800/50 transition-all duration-300
            ${isHovered ? "opacity-100" : "opacity-60"}
          `}
          >
            {/* Rating Stars */}
            {movie.rating && (
              <div className="flex items-center space-x-1">
                {[...Array(5)].map((_, index) => (
                  <StarSolidIcon
                    key={index}
                    className={`
                      w-3 h-3 transition-colors duration-200
                      ${
                        index < Math.floor(movie.rating! / 2)
                          ? "text-yellow-400"
                          : "text-gray-600"
                      }
                    `}
                  />
                ))}
                <span className="text-xs text-gray-400 ml-1">
                  ({movie.rating.toFixed(1)})
                </span>
              </div>
            )}

            {/* Quick Actions */}
            <div className="flex items-center space-x-2">
              <button
                onClick={handleLike}
                className="p-1 hover:bg-white/10 rounded transition-colors duration-200"
              >
                {isLiked ? (
                  <HeartSolidIcon className="w-4 h-4 text-red-500" />
                ) : (
                  <HeartIcon className="w-4 h-4 text-gray-400 hover:text-white" />
                )}
              </button>

              <button
                onClick={handleAddToList}
                className={`
                  p-1 rounded transition-colors duration-200
                  ${
                    isAdded
                      ? "text-green-500 bg-green-500/20"
                      : "text-gray-400 hover:text-white hover:bg-white/10"
                  }
                `}
              >
                <PlusIcon
                  className={`w-4 h-4 ${
                    isAdded ? "rotate-45" : ""
                  } transition-transform duration-200`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* Glow Effect on Hover */}
        <div
          className={`
          absolute inset-0 rounded-2xl transition-all duration-300 pointer-events-none
          ${
            isHovered
              ? "shadow-2xl shadow-red-500/20 ring-1 ring-red-500/30"
              : ""
          }
        `}
        ></div>
      </div>
    </div>
  );
};

export default MovieCard;
