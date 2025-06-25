#!/usr/bin/env python3
"""
Quick start script for the CineRAG API.

This script provides a convenient way to start the CineRAG API server
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the parent directory to the path so we can import from app
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# Load environment variables from config directory
from dotenv import load_dotenv

config_dir = project_root / "config"
env_file = config_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    print(f"Warning: {env_file} not found. Using environment variables only.")


def start_server():
    """Start the CineRAG API server."""
    print("🚀 Starting CineRAG API...")
    print("🎬 RAG-Powered Movie Recommendations")
    print("📊 Features: Semantic Search, AI Chat, Collaborative Filtering")
    print("-" * 50)

    # Check if we're in the right directory
    if not Path("app/main.py").exists():
        print("❌ Error: Please run this script from the mvp/ directory")
        sys.exit(1)

    # Check if .env file exists
    if not Path(".env").exists():
        print("⚠️  Warning: .env file not found")
        print("   Copy env_example.txt to .env and add your API keys")
        print("   The API will work without keys but with limited features")

    # Start the server
    try:
        print("📡 Starting server at http://localhost:8000")
        print("📚 API docs available at http://localhost:8000/docs")
        print("🔄 Press Ctrl+C to stop the server")
        print()

        subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--reload",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
            ]
        )

    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    start_server()
