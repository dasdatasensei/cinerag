import React, { useState, useEffect } from "react";
import {
  MagnifyingGlassIcon,
  ClockIcon,
  FireIcon,
} from "@heroicons/react/24/outline";

interface SearchSuggestionsProps {
  query: string;
  onSuggestionSelect: (suggestion: string) => void;
  onClose: () => void;
  isVisible: boolean;
}

const SearchSuggestions: React.FC<SearchSuggestionsProps> = ({
  query,
  onSuggestionSelect,
  onClose,
  isVisible,
}) => {
  const [selectedIndex, setSelectedIndex] = useState(-1);

  // Popular search suggestions
  const popularSuggestions = [
    "action movies",
    "comedy films",
    "horror movies",
    "romantic comedies",
    "sci-fi adventure",
    "animated movies",
    "thriller films",
    "drama movies",
    "superhero movies",
    "fantasy films",
  ];

  // Genre suggestions
  const genreSuggestions = [
    { name: "Action", emoji: "🔥", query: "action" },
    { name: "Comedy", emoji: "😂", query: "comedy" },
    { name: "Horror", emoji: "👻", query: "horror" },
    { name: "Romance", emoji: "💕", query: "romance" },
    { name: "Sci-Fi", emoji: "🚀", query: "sci-fi" },
    { name: "Drama", emoji: "🎭", query: "drama" },
    { name: "Thriller", emoji: "🔪", query: "thriller" },
    { name: "Animation", emoji: "🎨", query: "animated" },
  ];

  // Get recent searches from localStorage
  const getRecentSearches = (): string[] => {
    try {
      const recent = localStorage.getItem("cinerag_recent_searches");
      return recent ? JSON.parse(recent) : [];
    } catch {
      return [];
    }
  };

  const [recentSearches] = useState<string[]>(getRecentSearches());

  // Filter suggestions based on current query
  const filteredSuggestions =
    query.length > 0
      ? popularSuggestions
          .filter((suggestion) =>
            suggestion.toLowerCase().includes(query.toLowerCase())
          )
          .slice(0, 5)
      : [];

  // All suggestions combined
  const allSuggestions = [
    ...filteredSuggestions,
    ...recentSearches.slice(0, 3),
    ...genreSuggestions.map((g) => g.query),
  ];

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isVisible) return;

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setSelectedIndex((prev) =>
            prev < allSuggestions.length - 1 ? prev + 1 : prev
          );
          break;
        case "ArrowUp":
          e.preventDefault();
          setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
          break;
        case "Enter":
          e.preventDefault();
          if (selectedIndex >= 0 && allSuggestions[selectedIndex]) {
            onSuggestionSelect(allSuggestions[selectedIndex]);
          }
          break;
        case "Escape":
          onClose();
          break;
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isVisible, selectedIndex, allSuggestions, onSuggestionSelect, onClose]);

  // Reset selected index when query changes
  useEffect(() => {
    setSelectedIndex(-1);
  }, [query]);

  if (!isVisible) return null;

  return (
    <div className="absolute top-full left-0 right-0 mt-1 bg-black border border-gray-600 rounded-sm shadow-lg max-h-80 overflow-y-auto z-50">
      <div className="p-2">
        {/* Filtered suggestions based on query */}
        {query.length > 0 && filteredSuggestions.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center text-gray-400 text-xs font-medium mb-2 px-2">
              <MagnifyingGlassIcon className="h-3 w-3 mr-1" />
              Search suggestions
            </div>
            {filteredSuggestions.map((suggestion, index) => (
              <button
                key={`filtered-${suggestion}`}
                onClick={() => onSuggestionSelect(suggestion)}
                className={`w-full text-left px-3 py-2 text-sm rounded transition-colors duration-150 flex items-center ${
                  selectedIndex === index
                    ? "bg-gray-800 text-white"
                    : "text-gray-300 hover:bg-gray-800 hover:text-white"
                }`}
              >
                <MagnifyingGlassIcon className="h-4 w-4 mr-3 text-gray-500" />
                <span>{suggestion}</span>
              </button>
            ))}
          </div>
        )}

        {/* Recent searches */}
        {query.length === 0 && recentSearches.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center text-gray-400 text-xs font-medium mb-2 px-2">
              <ClockIcon className="h-3 w-3 mr-1" />
              Recent searches
            </div>
            {recentSearches.slice(0, 3).map((search, index) => (
              <button
                key={`recent-${search}`}
                onClick={() => onSuggestionSelect(search)}
                className={`w-full text-left px-3 py-2 text-sm rounded transition-colors duration-150 flex items-center ${
                  selectedIndex === filteredSuggestions.length + index
                    ? "bg-gray-800 text-white"
                    : "text-gray-300 hover:bg-gray-800 hover:text-white"
                }`}
              >
                <ClockIcon className="h-4 w-4 mr-3 text-gray-500" />
                <span>{search}</span>
              </button>
            ))}
          </div>
        )}

        {/* Popular genres */}
        {query.length === 0 && (
          <div>
            <div className="flex items-center text-gray-400 text-xs font-medium mb-2 px-2">
              <FireIcon className="h-3 w-3 mr-1" />
              Browse by genre
            </div>
            <div className="grid grid-cols-2 gap-1">
              {genreSuggestions.map((genre, index) => (
                <button
                  key={`genre-${genre.query}`}
                  onClick={() => onSuggestionSelect(genre.query)}
                  className={`text-left px-3 py-2 text-sm rounded transition-colors duration-150 flex items-center ${
                    selectedIndex ===
                    filteredSuggestions.length + recentSearches.length + index
                      ? "bg-gray-800 text-white"
                      : "text-gray-300 hover:bg-gray-800 hover:text-white"
                  }`}
                >
                  <span className="mr-2">{genre.emoji}</span>
                  <span>{genre.name}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* No suggestions message */}
        {query.length > 0 && filteredSuggestions.length === 0 && (
          <div className="px-3 py-4 text-center text-gray-400 text-sm">
            <MagnifyingGlassIcon className="h-8 w-8 mx-auto mb-2 text-gray-600" />
            <p>No suggestions found</p>
            <p className="text-xs mt-1">Try a different search term</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchSuggestions;
