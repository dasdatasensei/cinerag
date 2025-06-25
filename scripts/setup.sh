#!/bin/bash

echo "🚀 CineRAG - Docker Setup with RAG"
echo "RAG-Powered Movie Recommendations"
echo "============================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env_example.txt .env
    echo "✅ .env file created. Please edit it with your API keys:"
    echo "   - TMDB_API_KEY (required for movie posters)"
    echo "   - OPENAI_API_KEY (optional, for AI chat features)"
    echo ""
fi

echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo "🔍 Checking service health..."
docker-compose ps

echo ""
echo "✅ CineRAG with RAG is starting up!"
echo ""
echo "📡 API available at: http://localhost:8000"
echo "📚 API docs: http://localhost:8000/docs"
echo "🔍 Qdrant UI: http://localhost:6334"
echo ""

# Ask about populating vector database
echo "🤖 RAG Vector Database Setup"
echo "============================"
echo "To enable semantic search, you need to populate the vector database."
echo "This will:"
echo "   - Load 1000 movies from MovieLens"
echo "   - Enrich with TMDB metadata"
echo "   - Generate embeddings using sentence-transformers"
echo "   - Store in Qdrant vector database"
echo ""
read -p "Do you want to populate the vector database now? (y/N): " populate_db

if [[ $populate_db =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔄 Populating vector database..."
    echo "   This may take 5-10 minutes depending on your system..."

    # Run the population script inside the container
    docker-compose exec netflix-api python populate_vectors.py

    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 Vector database populated successfully!"
        echo ""
        echo "🧪 Test RAG features:"
        echo "   curl \"http://localhost:8000/api/movies/search?q=space%20adventure&semantic=true\""
        echo "   curl \"http://localhost:8000/api/vector/search?query=romantic%20comedy\""
    else
        echo ""
        echo "⚠️  Vector database population failed."
        echo "   You can try again later with: docker-compose exec netflix-api python populate_vectors.py"
    fi
else
    echo ""
    echo "⏭️  Skipping vector database population."
    echo "   You can populate it later with:"
    echo "   docker-compose exec netflix-api python populate_vectors.py"
fi

echo ""
echo "🔍 Service Status:"
echo "   docker-compose ps"
echo ""
echo "📋 View logs:"
echo "   docker-compose logs -f netflix-api"
echo "   docker-compose logs -f qdrant"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""
echo "⚙️  Edit .env file and restart to add API keys for full functionality"
echo ""
echo "🎬 Ready to build your Netflix frontend!"