import React from "react";

const MovieCardSkeleton: React.FC = () => {
  return (
    <div className="group relative rounded-2xl overflow-hidden shadow-xl">
      {/* Main Card Container */}
      <div className="relative card rounded-2xl overflow-hidden animate-loading-pulse">
        {/* Poster Skeleton */}
        <div className="relative aspect-[2/3] bg-gray-800/50 overflow-hidden">
          {/* Shimmer Effect */}
          <div
            className="absolute inset-0 -translate-x-full animate-[shimmer_2s_ease-in-out_infinite]
                         bg-gradient-to-r from-transparent via-white/10 to-transparent"
          ></div>

          {/* Top Badges Skeleton */}
          <div className="absolute top-3 left-0 right-0 flex justify-between items-start px-3">
            <div className="w-8 h-5 bg-gray-700/70 rounded-md"></div>
            <div className="w-12 h-5 bg-gray-700/70 rounded-md"></div>
          </div>
        </div>

        {/* Movie Information Skeleton */}
        <div className="p-4 space-y-3 bg-gradient-to-b from-gray-900/95 to-black/95">
          {/* Title Skeleton */}
          <div className="space-y-2">
            <div className="h-4 bg-gray-700/70 rounded-md w-3/4"></div>
            <div className="h-4 bg-gray-700/70 rounded-md w-1/2"></div>
          </div>

          {/* Metadata Row Skeleton */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1">
              <div className="w-3 h-3 bg-gray-700/70 rounded"></div>
              <div className="w-12 h-3 bg-gray-700/70 rounded"></div>
            </div>
            <div className="w-16 h-5 bg-gray-700/70 rounded-md"></div>
          </div>

          {/* Action Bar Skeleton */}
          <div className="flex items-center justify-between pt-2 border-t border-gray-800/50">
            {/* Rating Stars Skeleton */}
            <div className="flex items-center space-x-1">
              {[...Array(5)].map((_, index) => (
                <div
                  key={index}
                  className="w-3 h-3 bg-gray-700/70 rounded-sm"
                ></div>
              ))}
              <div className="w-8 h-3 bg-gray-700/70 rounded ml-1"></div>
            </div>

            {/* Quick Actions Skeleton */}
            <div className="flex items-center space-x-2">
              <div className="w-6 h-6 bg-gray-700/70 rounded"></div>
              <div className="w-6 h-6 bg-gray-700/70 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MovieCardSkeleton;
