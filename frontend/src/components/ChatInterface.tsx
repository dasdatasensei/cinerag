import React, { useState, useRef, useEffect } from "react";
import {
  PaperAirplaneIcon,
  XMarkIcon,
  ChatBubbleOvalLeftEllipsisIcon,
  SparklesIcon,
  MicrophoneIcon,
  StopIcon,
} from "@heroicons/react/24/outline";
import { ChatBubbleOvalLeftIcon } from "@heroicons/react/24/solid";
import CineRagApiService, {
  ChatMessage,
  transformApiMovie,
} from "../services/api";
import MovieCard from "./MovieCard";

interface ChatInterfaceProps {
  isOpen: boolean;
  onClose: () => void;
  onMovieClick: (movie: any) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  isOpen,
  onClose,
  onMovieClick,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Hi there! 🎬 I'm your personal movie assistant. Ask me anything about movies - I can recommend films based on your mood, find similar titles, or help you discover your next favorite watch!",
      timestamp: new Date(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [suggestions] = useState([
    "Recommend me a good action movie",
    "What are the best sci-fi films?",
    "I want something funny to watch",
    "Find movies similar to Inception",
    "What's trending this week?",
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      role: "user",
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setIsLoading(true);
    setIsTyping(true);

    try {
      // Prepare conversation history for API
      const conversationHistory = messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      const response = await CineRagApiService.sendChatMessage(
        inputMessage,
        conversationHistory
      );

      // Simulate typing delay for better UX
      setTimeout(() => {
        const assistantMessage: ChatMessage = {
          role: "assistant",
          content: response.response,
          timestamp: new Date(),
          movies: response.movies.map(transformApiMovie),
        };

        setMessages((prev) => [...prev, assistantMessage]);
        setIsTyping(false);
        setIsLoading(false);
      }, 1000);
    } catch (error) {
      console.error("Chat error:", error);
      const errorMessage: ChatMessage = {
        role: "assistant",
        content:
          "I'm sorry, I'm having trouble connecting right now. Please try again later.",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
      setIsTyping(false);
      setIsLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInputMessage(suggestion);
    inputRef.current?.focus();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-end p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Chat Window */}
      <div className="relative w-full max-w-lg h-[600px] lg:h-[700px] glass rounded-2xl overflow-hidden shadow-2xl animate-fade-in-scale">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-white/10 bg-gradient-to-r from-red-600/20 to-purple-600/20">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <div className="w-10 h-10 bg-gradient-to-r from-red-500 to-red-600 rounded-full flex items-center justify-center">
                <SparklesIcon className="w-5 h-5 text-white" />
              </div>
              <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 border-2 border-gray-900 rounded-full"></div>
            </div>
            <div>
              <h3 className="font-semibold text-white">CineRAG Assistant</h3>
              <p className="text-xs text-gray-300">
                AI-powered movie recommendations
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors duration-200"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 h-[400px] lg:h-[500px]">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[80%] ${
                  message.role === "user" ? "order-2" : "order-1"
                }`}
              >
                {/* Message Bubble */}
                <div
                  className={`
                  px-4 py-3 rounded-2xl ${
                    message.role === "user"
                      ? "bg-gradient-to-r from-red-600 to-red-700 text-white ml-auto"
                      : "glass text-white"
                  }
                `}
                >
                  <p className="text-sm leading-relaxed whitespace-pre-wrap">
                    {message.content}
                  </p>
                </div>

                {/* Movies Grid */}
                {message.movies && message.movies.length > 0 && (
                  <div className="mt-3 space-y-3">
                    <div className="text-xs text-gray-400 px-2">
                      Recommended movies:
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      {message.movies.slice(0, 4).map((movie, movieIndex) => (
                        <div key={movieIndex} className="transform scale-90">
                          <MovieCard
                            movie={movie}
                            onMovieClick={() => onMovieClick(movie)}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Timestamp */}
                <div
                  className={`text-xs text-gray-500 mt-1 px-2 ${
                    message.role === "user" ? "text-right" : "text-left"
                  }`}
                >
                  {message.timestamp.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </div>
              </div>

              {/* Avatar */}
              <div
                className={`flex-shrink-0 ${
                  message.role === "user" ? "order-1 ml-3" : "order-2 mr-3"
                }`}
              >
                {message.role === "assistant" ? (
                  <div className="w-8 h-8 bg-gradient-to-r from-red-500 to-red-600 rounded-full flex items-center justify-center">
                    <ChatBubbleOvalLeftIcon className="w-4 h-4 text-white" />
                  </div>
                ) : (
                  <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
                    <span className="text-xs font-medium text-white">You</span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex justify-start">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-r from-red-500 to-red-600 rounded-full flex items-center justify-center">
                  <ChatBubbleOvalLeftIcon className="w-4 h-4 text-white" />
                </div>
                <div className="glass px-4 py-3 rounded-2xl">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce animate-delay-100"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce animate-delay-200"></div>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggestions */}
        {messages.length === 1 && (
          <div className="px-4 py-2 border-t border-white/10">
            <div className="text-xs text-gray-400 mb-2">Try asking:</div>
            <div className="flex flex-wrap gap-2">
              {suggestions.slice(0, 3).map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="text-xs px-3 py-1 glass rounded-full text-gray-300 hover:text-white hover:bg-white/10 transition-colors duration-200"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="p-4 border-t border-white/10 bg-gray-900/50">
          <div className="flex items-end space-x-3">
            <div className="flex-1">
              <div className="relative">
                <input
                  ref={inputRef}
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask about movies, get recommendations..."
                  disabled={isLoading}
                  className="
                    w-full px-4 py-3 pr-12 glass rounded-xl text-white placeholder-gray-400
                    focus:outline-none focus:ring-2 focus:ring-red-500/50 focus:border-transparent
                    disabled:opacity-50 disabled:cursor-not-allowed
                  "
                />
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  {isLoading ? (
                    <div className="loading-spin w-5 h-5 border-2 border-gray-600 border-t-red-500 rounded-full"></div>
                  ) : (
                    <ChatBubbleOvalLeftEllipsisIcon className="w-5 h-5 text-gray-400" />
                  )}
                </div>
              </div>
            </div>

            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading}
              className="
                p-3 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-xl
                hover:from-red-700 hover:to-red-800 focus:outline-none focus:ring-2
                focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-gray-900
                disabled:opacity-50 disabled:cursor-not-allowed
                transform transition-all duration-200 hover:scale-105 active:scale-95
              "
            >
              <PaperAirplaneIcon className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
