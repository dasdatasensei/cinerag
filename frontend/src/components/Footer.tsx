import React from "react";

const Footer: React.FC = () => {
  return (
    <footer className="relative z-10 bg-black/50 backdrop-blur-sm border-t border-gray-800/50 mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-20">
        <div className="text-center">
          {/* Author Information */}
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-white mb-2">
              Created by Dr. Jody-Ann S. Jones
            </h3>
            <p className="text-gray-400 text-sm mb-3">
              Founder of{" "}
              <span className="text-red-400 font-medium">The Data Sensei</span>
            </p>
          </div>

          {/* Links */}
          <div className="flex flex-wrap justify-center items-center gap-4 sm:gap-6 mb-6">
            <a
              href="https://www.drjodyannjones.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-300 hover:text-red-400 transition-colors duration-200 text-sm"
            >
              🌐 Portfolio
            </a>
            <a
              href="https://www.thedatasensei.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-300 hover:text-red-400 transition-colors duration-200 text-sm"
            >
              💼 The Data Sensei
            </a>
            <a
              href="https://github.com/dasdatasensei"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-300 hover:text-red-400 transition-colors duration-200 text-sm"
            >
              💻 GitHub
            </a>
            <a
              href="mailto:jody@thedatasensei.com"
              className="text-gray-300 hover:text-red-400 transition-colors duration-200 text-sm"
            >
              📧 Contact
            </a>
          </div>

          {/* Project Info */}
          <div className="text-center text-gray-500 text-xs">
            <p className="mb-1">CineRAG - RAG-Powered Movie Recommendations</p>
            <p>Built with React, FastAPI, and Vector Embeddings</p>
          </div>

          {/* Decorative element */}
          <div className="mt-6 flex justify-center">
            <div className="w-16 h-px bg-gradient-to-r from-transparent via-red-500 to-transparent"></div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
