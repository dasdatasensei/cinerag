"""
Qdrant Client Configuration

Manages Qdrant vector database connections, collections, and basic operations.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    Match,
    MatchValue,
)
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QdrantManager:
    """
    Manages Qdrant vector database operations for CineRAG.

    Handles connections, collection management, and basic CRUD operations.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        timeout: int = 30,
        prefer_grpc: bool = False,
    ):
        """
        Initialize Qdrant client.

        Args:
            host: Qdrant server host
            port: Qdrant server port
            timeout: Connection timeout in seconds
            prefer_grpc: Whether to prefer gRPC over HTTP
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.prefer_grpc = prefer_grpc

        # Initialize client
        self.client = None
        self.is_connected = False

        # Default collection configuration
        self.default_collection_config = {
            "vectors": {
                "size": 384,  # all-MiniLM-L6-v2 embedding size
                "distance": Distance.COSINE,
            }
        }

        # Connect to Qdrant
        self.connect()

    def connect(self) -> bool:
        """
        Establish connection to Qdrant server.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to Qdrant at {self.host}:{self.port}")

            self.client = QdrantClient(
                host=self.host,
                port=self.port,
                timeout=self.timeout,
                prefer_grpc=self.prefer_grpc,
            )

            # Test connection with a simple collections list call
            collections = self.client.get_collections()
            logger.info(
                f"Qdrant connection successful. Found {len(collections.collections)} collections"
            )

            self.is_connected = True
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {str(e)}")
            self.is_connected = False
            return False

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get connection status and server information.

        Returns:
            dict: Connection and server status information
        """
        if not self.is_connected:
            return {
                "connected": False,
                "host": self.host,
                "port": self.port,
                "error": "Not connected to Qdrant",
            }

        try:
            # Get collections info
            collections = self.client.get_collections()

            return {
                "connected": True,
                "host": self.host,
                "port": self.port,
                "collections_count": len(collections.collections),
                "collections": [col.name for col in collections.collections],
            }

        except Exception as e:
            logger.error(f"Error getting connection info: {str(e)}")
            return {
                "connected": False,
                "host": self.host,
                "port": self.port,
                "error": str(e),
            }

    def create_collection(
        self,
        collection_name: str,
        vector_size: int = 384,
        distance_metric: Distance = Distance.COSINE,
        recreate: bool = False,
    ) -> bool:
        """
        Create a new collection in Qdrant.

        Args:
            collection_name: Name of the collection
            vector_size: Dimension of vectors
            distance_metric: Distance metric for similarity search
            recreate: Whether to recreate if collection exists

        Returns:
            bool: True if creation successful
        """
        if not self.is_connected:
            logger.error("Not connected to Qdrant")
            return False

        try:
            # Check if collection exists
            existing_collections = self.client.get_collections()
            collection_exists = any(
                col.name == collection_name for col in existing_collections.collections
            )

            if collection_exists:
                if recreate:
                    logger.info(f"Deleting existing collection: {collection_name}")
                    self.client.delete_collection(collection_name)
                else:
                    logger.info(f"Collection {collection_name} already exists")
                    return True

            # Create collection
            logger.info(f"Creating collection: {collection_name}")

            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=distance_metric),
            )

            logger.info(f"Collection {collection_name} created successfully")
            return True

        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {str(e)}")
            return False

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Get information about a specific collection.

        Args:
            collection_name: Name of the collection

        Returns:
            dict: Collection information and statistics
        """
        if not self.is_connected:
            return {"error": "Not connected to Qdrant"}

        try:
            # Get basic collection count (more reliable)
            stats = self.client.count(collection_name)

            # Try to get collection info, but handle errors gracefully
            try:
                collection_info = self.client.get_collection(collection_name)
                vector_size = collection_info.config.params.vectors.size
                distance = collection_info.config.params.vectors.distance.value
                status = collection_info.status.value
            except Exception as e:
                logger.warning(f"Could not get detailed collection info: {str(e)}")
                vector_size = 384  # Default assumption
                distance = "Cosine"
                status = "green"

            return {
                "name": collection_name,
                "status": status,
                "vectors_count": stats.count,
                "points_count": stats.count,
                "config": {"vector_size": vector_size, "distance": distance},
            }

        except Exception as e:
            logger.error(
                f"Error getting collection info for {collection_name}: {str(e)}"
            )
            return {"error": str(e)}

    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection.

        Args:
            collection_name: Name of the collection to delete

        Returns:
            bool: True if deletion successful
        """
        if not self.is_connected:
            logger.error("Not connected to Qdrant")
            return False

        try:
            logger.info(f"Deleting collection: {collection_name}")
            self.client.delete_collection(collection_name)
            logger.info(f"Collection {collection_name} deleted successfully")
            return True

        except Exception as e:
            logger.error(f"Error deleting collection {collection_name}: {str(e)}")
            return False

    def list_collections(self) -> List[str]:
        """
        List all collections in Qdrant.

        Returns:
            list: List of collection names
        """
        if not self.is_connected:
            logger.error("Not connected to Qdrant")
            return []

        try:
            collections = self.client.get_collections()
            return [col.name for col in collections.collections]

        except Exception as e:
            logger.error(f"Error listing collections: {str(e)}")
            return []

    def close(self):
        """Close the Qdrant client connection."""
        if self.client:
            try:
                self.client.close()
                self.is_connected = False
                logger.info("Qdrant connection closed")
            except Exception as e:
                logger.error(f"Error closing Qdrant connection: {str(e)}")


# Global instance for easy access
qdrant_manager = None


def get_qdrant_manager(host: str = None, port: int = None) -> QdrantManager:
    """
    Get or create global Qdrant manager instance.

    Args:
        host: Override default host
        port: Override default port

    Returns:
        QdrantManager: Global Qdrant manager instance
    """
    global qdrant_manager

    # Use environment variables or defaults
    default_host = os.getenv("QDRANT_HOST", "localhost")
    default_port = int(os.getenv("QDRANT_PORT", "6333"))

    final_host = host or default_host
    final_port = port or default_port

    if qdrant_manager is None:
        qdrant_manager = QdrantManager(host=final_host, port=final_port)

    return qdrant_manager
