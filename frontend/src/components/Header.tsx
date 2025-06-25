import React, { useState, useRef, useEffect } from "react";
import {
  MagnifyingGlassIcon,
  XMarkIcon,
  BellIcon,
  UserCircleIcon,
  Bars3Icon,
  HomeIcon,
  FilmIcon,
  TvIcon,
  BookmarkIcon,
} from "@heroicons/react/24/outline";

interface HeaderProps {
  onSearch: (query: string) => void;
  searchQuery: string;
  onClearSearch: () => void;
}

const Header: React.FC<HeaderProps> = ({
  onSearch,
  searchQuery,
  onClearSearch,
}) => {
  const [isSearchFocused, setIsSearchFocused] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const [searchValue, setSearchValue] = useState(searchQuery);

  useEffect(() => {
    setSearchValue(searchQuery);
  }, [searchQuery]);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchValue.trim()) {
      onSearch(searchValue.trim());
    }
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchValue(value);

    // Real-time search for better UX
    if (value.trim()) {
      const debounceTimer = setTimeout(() => {
        onSearch(value.trim());
      }, 300);
      return () => clearTimeout(debounceTimer);
    }
  };

  const handleClearSearch = () => {
    setSearchValue("");
    onClearSearch();
    searchInputRef.current?.focus();
  };

  const navigationItems = [
    { name: "Home", icon: HomeIcon, active: true },
    { name: "Movies", icon: FilmIcon, active: false },
    { name: "TV Shows", icon: TvIcon, active: false },
    { name: "My List", icon: BookmarkIcon, active: false },
  ];

  return (
    <>
      <header
        className={`
        fixed top-0 left-0 right-0 z-50 transition-all duration-300
        ${
          isScrolled
            ? "bg-black/90 backdrop-blur-md border-b border-gray-800/50"
            : "bg-transparent"
        }
      `}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 lg:h-20">
            {/* Logo */}
            <div className="flex items-center space-x-8">
              <div className="flex-shrink-0">
                <h1 className="text-2xl lg:text-3xl font-display font-bold">
                  <span className="text-gradient">Cine</span>
                  <span className="text-white">RAG</span>
                </h1>
              </div>

              {/* Desktop Navigation */}
              <nav className="hidden lg:flex space-x-8">
                {navigationItems.map((item) => (
                  <button
                    key={item.name}
                    className={`
                      flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200
                      ${
                        item.active
                          ? "text-white bg-white/10"
                          : "text-gray-300 hover:text-white hover:bg-white/5"
                      }
                    `}
                  >
                    <item.icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </button>
                ))}
              </nav>
            </div>

            {/* Search Bar */}
            <div className="flex-1 max-w-xl mx-4 lg:mx-8">
              <form onSubmit={handleSearchSubmit} className="relative group">
                <div
                  className={`
                  relative overflow-hidden rounded-xl transition-all duration-300
                  ${
                    isSearchFocused
                      ? "bg-gray-900/90 border-2 border-red-500/50 shadow-lg shadow-red-500/10"
                      : "bg-gray-900/60 border-2 border-gray-700/50 hover:border-gray-600/50"
                  }
                `}
                >
                  <div className="flex items-center">
                    <div className="pl-4">
                      <MagnifyingGlassIcon
                        className={`
                        w-5 h-5 transition-colors duration-200
                        ${isSearchFocused ? "text-red-400" : "text-gray-400"}
                      `}
                      />
                    </div>

                    <input
                      ref={searchInputRef}
                      type="text"
                      value={searchValue}
                      onChange={handleSearchChange}
                      onFocus={() => setIsSearchFocused(true)}
                      onBlur={() => setIsSearchFocused(false)}
                      placeholder="Search movies, genres, actors..."
                      className="
                        w-full px-4 py-3 bg-transparent text-white placeholder-gray-400
                        focus:outline-none text-sm lg:text-base
                      "
                    />

                    {searchValue && (
                      <button
                        type="button"
                        onClick={handleClearSearch}
                        className="
                          pr-4 text-gray-400 hover:text-white transition-colors duration-200
                          hover:scale-110 transform
                        "
                      >
                        <XMarkIcon className="w-5 h-5" />
                      </button>
                    )}
                  </div>

                  {/* Animated search glow effect */}
                  <div
                    className={`
                    absolute inset-0 opacity-0 transition-opacity duration-300 pointer-events-none
                    ${isSearchFocused ? "opacity-100" : ""}
                  `}
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-red-500/20 via-pink-500/20 to-red-500/20 blur-sm"></div>
                  </div>
                </div>
              </form>
            </div>

            {/* Right Side Actions */}
            <div className="flex items-center space-x-4">
              {/* Desktop Actions */}
              <div className="hidden lg:flex items-center space-x-4">
                <button
                  className="
                  p-2 text-gray-400 hover:text-white transition-colors duration-200
                  hover:bg-white/10 rounded-lg
                "
                >
                  <BellIcon className="w-5 h-5" />
                </button>

                <div className="w-px h-6 bg-gray-700"></div>

                <button
                  className="
                  flex items-center space-x-2 p-2 text-gray-400 hover:text-white
                  transition-colors duration-200 hover:bg-white/10 rounded-lg
                "
                >
                  <UserCircleIcon className="w-6 h-6" />
                  <span className="text-sm font-medium">Profile</span>
                </button>
              </div>

              {/* Mobile Menu Button */}
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="
                  lg:hidden p-2 text-gray-400 hover:text-white
                  transition-colors duration-200 hover:bg-white/10 rounded-lg
                "
              >
                <Bars3Icon className="w-6 h-6" />
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Search Results / Current Search Display */}
        {searchQuery && (
          <div className="lg:hidden bg-gray-900/95 backdrop-blur-sm border-t border-gray-800/50">
            <div className="max-w-7xl mx-auto px-4 py-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-300">
                  Searching:{" "}
                  <span className="text-white font-medium">
                    "{searchQuery}"
                  </span>
                </span>
                <button
                  onClick={onClearSearch}
                  className="text-red-400 hover:text-red-300 text-sm font-medium"
                >
                  Clear
                </button>
              </div>
            </div>
          </div>
        )}
      </header>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 z-40">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setIsMobileMenuOpen(false)}
          ></div>

          <div className="absolute top-16 left-0 right-0 bg-gray-900/95 backdrop-blur-md border-b border-gray-800/50">
            <div className="max-w-7xl mx-auto px-4 py-6">
              {/* Mobile Navigation */}
              <nav className="space-y-2 mb-6">
                {navigationItems.map((item) => (
                  <button
                    key={item.name}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={`
                      w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-left transition-all duration-200
                      ${
                        item.active
                          ? "text-white bg-white/10 border border-white/20"
                          : "text-gray-300 hover:text-white hover:bg-white/5"
                      }
                    `}
                  >
                    <item.icon className="w-5 h-5" />
                    <span className="font-medium">{item.name}</span>
                  </button>
                ))}
              </nav>

              {/* Mobile Actions */}
              <div className="border-t border-gray-800/50 pt-6 space-y-2">
                <button
                  className="
                  w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-left
                  text-gray-300 hover:text-white hover:bg-white/5 transition-all duration-200
                "
                >
                  <BellIcon className="w-5 h-5" />
                  <span className="font-medium">Notifications</span>
                </button>

                <button
                  className="
                  w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-left
                  text-gray-300 hover:text-white hover:bg-white/5 transition-all duration-200
                "
                >
                  <UserCircleIcon className="w-5 h-5" />
                  <span className="font-medium">Profile Settings</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default Header;
