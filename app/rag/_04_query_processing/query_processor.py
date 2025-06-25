"""
Integrated Query Processor

Main interface that combines query preprocessing and enhancement
to provide a complete query processing pipeline for the RAG system.
"""

import logging
from typing import Dict, List, Optional
from .query_preprocessor import get_query_preprocessor
from .query_enhancer import get_query_enhancer

# Configure logging
logger = logging.getLogger(__name__)


class QueryProcessor:
    """
    Main query processor that orchestrates preprocessing and enhancement.

    Provides a unified interface for all query processing operations
    including cleaning, enhancement, and contextual improvements.
    """

    def __init__(self):
        """Initialize the query processor."""
        self.preprocessor = get_query_preprocessor()
        self.enhancer = get_query_enhancer()

        # Query processing configuration
        self.config = {
            "enable_preprocessing": True,
            "enable_enhancement": True,
            "enable_spell_correction": True,
            "enable_intent_detection": True,
            "enable_query_expansion": True,
            "min_query_length": 1,
            "max_query_length": 500,
            "default_processing_mode": "full",  # 'full', 'light', 'minimal'
        }

        # Processing mode configurations
        self.processing_modes = {
            "minimal": {
                "preprocessing": True,
                "enhancement": False,
                "spell_correction": False,
                "intent_detection": False,
                "query_expansion": False,
            },
            "light": {
                "preprocessing": True,
                "enhancement": True,
                "spell_correction": True,
                "intent_detection": False,
                "query_expansion": False,
            },
            "full": {
                "preprocessing": True,
                "enhancement": True,
                "spell_correction": True,
                "intent_detection": True,
                "query_expansion": True,
            },
        }

    def validate_query(self, query: str) -> Dict[str, any]:
        """
        Validate query input before processing.

        Args:
            query: Input query string

        Returns:
            dict: Validation results
        """
        if not query:
            return {
                "valid": False,
                "error": "Query is empty",
                "suggestions": [
                    'Try searching for movie genres like "action", "comedy", or "drama"'
                ],
            }

        if not isinstance(query, str):
            return {
                "valid": False,
                "error": "Query must be a string",
                "suggestions": ["Please provide a text query"],
            }

        query_length = len(query.strip())

        if query_length < self.config["min_query_length"]:
            return {
                "valid": False,
                "error": f'Query too short (minimum {self.config["min_query_length"]} characters)',
                "suggestions": [
                    'Try adding more descriptive words like "funny movie" or "sci-fi film"'
                ],
            }

        if query_length > self.config["max_query_length"]:
            return {
                "valid": False,
                "error": f'Query too long (maximum {self.config["max_query_length"]} characters)',
                "suggestions": [
                    "Try shortening your query to focus on the main keywords"
                ],
            }

        # Check for potentially problematic content
        if query.strip().isdigit():
            return {
                "valid": True,
                "warning": "Numeric-only query detected",
                "suggestions": [
                    'If searching by year, try "movies from 1995" or "1990s films"'
                ],
            }

        return {"valid": True}

    def process_query(
        self, query: str, mode: str = None, custom_config: Dict = None
    ) -> Dict[str, any]:
        """
        Complete query processing pipeline.

        Args:
            query: Raw user query
            mode: Processing mode ('minimal', 'light', 'full')
            custom_config: Custom processing configuration

        Returns:
            dict: Complete processing results
        """
        # Validate input
        validation = self.validate_query(query)
        if not validation["valid"]:
            return {
                "success": False,
                "error": validation["error"],
                "suggestions": validation.get("suggestions", []),
                "original_query": query,
            }

        # Determine processing configuration
        processing_mode = mode or self.config["default_processing_mode"]
        if processing_mode not in self.processing_modes:
            processing_mode = "full"

        mode_config = self.processing_modes[processing_mode].copy()
        if custom_config:
            mode_config.update(custom_config)

        # Initialize results
        results = {
            "success": True,
            "original_query": query,
            "processed_query": query,
            "final_query": query,
            "processing_mode": processing_mode,
            "validation": validation,
            "preprocessing_results": None,
            "enhancement_results": None,
            "processing_steps": [],
            "recommendations": {
                "use_processed_query": True,
                "alternative_queries": [],
                "search_suggestions": [],
            },
        }

        try:
            current_query = query.strip()

            # Step 1: Preprocessing
            if mode_config.get("preprocessing", True):
                logger.info(f"Starting preprocessing for query: '{current_query}'")

                preprocessing_results = self.preprocessor.preprocess_query(
                    current_query,
                    expand_synonyms=True,
                    remove_stop_words=True,
                    normalize_terms=True,
                )

                results["preprocessing_results"] = preprocessing_results
                current_query = preprocessing_results["processed_query"]
                results["processing_steps"].append("preprocessing")

                logger.info(f"Preprocessing completed: '{current_query}'")

            # Step 2: Enhancement
            if mode_config.get("enhancement", True):
                logger.info(f"Starting enhancement for query: '{current_query}'")

                enhanced_query = self.enhancer.enhance_query(current_query)

                # Create enhancement results structure
                enhancement_results = {
                    "original_query": current_query,
                    "enhanced_query": enhanced_query,
                    "enhancement_applied": enhanced_query != current_query,
                    "enhancement_methods": [
                        "spelling_correction",
                        "synonym_expansion",
                        "quality_expansion",
                        "mood_expansion",
                        "time_context",
                    ],
                    "expanded_queries": [],  # Initialize as empty list for now
                }

                results["enhancement_results"] = enhancement_results

                # Update current query based on enhancement
                if enhancement_results["enhancement_applied"]:
                    current_query = enhancement_results["enhanced_query"]

                results["processing_steps"].append("enhancement")

                # Add alternative queries from expansion (if any)
                if enhancement_results.get("expanded_queries"):
                    results["recommendations"]["alternative_queries"].extend(
                        enhancement_results["expanded_queries"]
                    )

                logger.info(f"Enhancement completed: '{current_query}'")

            # Step 3: Generate search suggestions (simplified)
            if mode_config.get("query_expansion", True) and len(current_query) >= 2:
                # Generate simple suggestions based on current query
                suggestions = self._generate_simple_suggestions(current_query)
                results["recommendations"]["search_suggestions"] = suggestions
                results["processing_steps"].append("suggestion_generation")

            # Finalize results
            results["processed_query"] = current_query
            results["final_query"] = current_query

            # Remove duplicates from alternative queries
            alt_queries = results["recommendations"]["alternative_queries"]
            unique_alt_queries = []
            seen = set()
            for aq in alt_queries:
                if aq not in seen and aq != current_query:
                    seen.add(aq)
                    unique_alt_queries.append(aq)
            results["recommendations"]["alternative_queries"] = unique_alt_queries[:5]

            # Processing summary
            results["summary"] = {
                "query_changed": current_query != query,
                "steps_applied": len(results["processing_steps"]),
                "alternatives_generated": len(
                    results["recommendations"]["alternative_queries"]
                ),
                "suggestions_generated": len(
                    results["recommendations"]["search_suggestions"]
                ),
                "processing_time_info": f"Mode: {processing_mode}",
            }

            logger.info(
                f"Query processing completed successfully: '{query}' -> '{current_query}'"
            )

        except Exception as e:
            logger.error(f"Error processing query '{query}': {str(e)}")
            results.update(
                {
                    "success": False,
                    "error": f"Processing failed: {str(e)}",
                    "final_query": query,  # Fallback to original
                    "recommendations": {
                        "use_processed_query": False,
                        "alternative_queries": [query],
                        "search_suggestions": [],
                    },
                }
            )

        return results

    def quick_process(self, query: str) -> str:
        """
        Quick query processing that returns just the processed query string.

        Args:
            query: Raw user query

        Returns:
            str: Processed query string
        """
        try:
            results = self.process_query(query, mode="light")
            return results.get("final_query", query)
        except Exception as e:
            logger.error(f"Quick processing failed for '{query}': {str(e)}")
            return query

    def get_processing_info(self) -> Dict[str, any]:
        """
        Get information about the query processor configuration and capabilities.

        Returns:
            dict: Processor information
        """
        return {
            "version": "1.0.0",
            "capabilities": {
                "preprocessing": True,
                "enhancement": True,
                "spell_correction": True,
                "intent_detection": True,
                "query_expansion": True,
                "search_suggestions": True,
            },
            "processing_modes": list(self.processing_modes.keys()),
            "config": self.config.copy(),
            "supported_languages": ["en"],  # Currently English only
            "max_query_length": self.config["max_query_length"],
        }

    def update_config(self, new_config: Dict) -> bool:
        """
        Update processor configuration.

        Args:
            new_config: New configuration dictionary

        Returns:
            bool: True if update successful
        """
        try:
            valid_keys = set(self.config.keys())
            for key, value in new_config.items():
                if key in valid_keys:
                    self.config[key] = value
                    logger.info(f"Updated config: {key} = {value}")
                else:
                    logger.warning(f"Invalid config key ignored: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to update config: {str(e)}")
            return False

    def _generate_simple_suggestions(self, query: str) -> List[str]:
        """
        Generate simple search suggestions based on the current query.

        Args:
            query: Current processed query

        Returns:
            List of suggestion strings
        """
        suggestions = []
        query_lower = query.lower()

        # Genre-based suggestions
        genre_suggestions = {
            "action": ["action thriller", "action adventure", "action comedy"],
            "comedy": ["romantic comedy", "action comedy", "dark comedy"],
            "drama": ["family drama", "crime drama", "romantic drama"],
            "horror": ["psychological horror", "horror thriller", "classic horror"],
            "sci-fi": ["sci-fi action", "sci-fi thriller", "space adventure"],
            "romance": ["romantic comedy", "romantic drama", "period romance"],
            "thriller": ["psychological thriller", "action thriller", "crime thriller"],
            "fantasy": ["fantasy adventure", "dark fantasy", "fantasy comedy"],
            "animation": ["animated family", "animated comedy", "animated adventure"],
        }

        # Add genre-specific suggestions
        for genre, genre_subs in genre_suggestions.items():
            if genre in query_lower:
                for sub in genre_subs:
                    if sub not in query_lower:
                        suggestions.append(sub)

        # Time period suggestions
        if any(term in query_lower for term in ["recent", "new", "latest"]):
            suggestions.extend(["movies from 2020", "recent releases", "latest films"])
        elif any(term in query_lower for term in ["classic", "old", "vintage"]):
            suggestions.extend(["classic movies", "old films", "vintage cinema"])

        # Quality suggestions
        if any(term in query_lower for term in ["good", "best", "great"]):
            suggestions.extend(
                ["highly rated", "award winning", "critically acclaimed"]
            )

        # Mood suggestions
        if "funny" in query_lower:
            suggestions.extend(["hilarious", "comedy", "humorous"])
        elif "scary" in query_lower:
            suggestions.extend(["horror", "thriller", "suspense"])
        elif "sad" in query_lower:
            suggestions.extend(["drama", "emotional", "tearjerker"])

        # Remove duplicates and limit results
        unique_suggestions = []
        seen = set()
        for suggestion in suggestions:
            if suggestion not in seen and suggestion != query_lower:
                seen.add(suggestion)
                unique_suggestions.append(suggestion)

        return unique_suggestions[:5]  # Return top 5 suggestions


# Global instance for easy access
query_processor = None


def get_query_processor() -> QueryProcessor:
    """
    Get or create global query processor instance.

    Returns:
        QueryProcessor: Global processor instance
    """
    global query_processor

    if query_processor is None:
        query_processor = QueryProcessor()

    return query_processor


# Convenience functions for direct use
def process_query(query: str, mode: str = "full") -> Dict[str, any]:
    """
    Process a query with the global processor instance.

    Args:
        query: Query to process
        mode: Processing mode

    Returns:
        dict: Processing results
    """
    processor = get_query_processor()
    return processor.process_query(query, mode=mode)


def quick_process_query(query: str) -> str:
    """
    Quick process a query and return the processed string.

    Args:
        query: Query to process

    Returns:
        str: Processed query
    """
    processor = get_query_processor()
    return processor.quick_process(query)
