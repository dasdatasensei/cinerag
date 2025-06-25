# 🚀 CineRAG Deployment Guide

## 🎯 Quick Start (5 minutes)

### **Prerequisites**

- Docker and Docker Compose installed
- 4GB+ RAM available
- Internet connection for downloading models

### **1. Clone & Setup**

```bash
git clone <your-repository>
cd CineRAG
```

### **2. Environment Configuration**

```bash
# Copy environment template
cp config/env_example config/.env

# Edit configuration (optional)
nano config/.env
```

### **3. Start Services**

```bash
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Check status
docker-compose -f docker/docker-compose.yml ps
```

### **4. Access Application**

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs
- **Qdrant UI**: http://localhost:6334/dashboard

## ⚙️ Environment Configuration

### **Required Variables**

```bash
# config/.env
TMDB_API_KEY=your_tmdb_api_key_here
```

### **Optional Variables**

```bash
# OpenAI integration (for chat features)
OPENAI_API_KEY=your_openai_api_key_here

# Vector database (auto-configured in Docker)
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# API configuration
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

## 🔧 Service Architecture

### **Docker Services**

- **cinerag-api**: FastAPI backend (port 8000)
- **qdrant**: Vector database (ports 6333, 6334)
- **frontend**: React development server (port 3000)

### **Service Dependencies**

```
Frontend → API → Qdrant
                ↓
            TMDB API
                ↓
            OpenAI (optional)
```

## 🏃‍♂️ Development Setup

### **Local Development**

```bash
# Backend only (with external Qdrant)
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend only
cd frontend
npm install
npm start
```

### **Hybrid Setup**

```bash
# Start vector database only
docker-compose -f docker/docker-compose.yml up qdrant -d

# Run API locally
uvicorn app.main:app --reload

# Run frontend locally
cd frontend && npm start
```

## 📊 Health Checks

### **System Status**

```bash
# API health
curl http://localhost:8000/health

# Vector database
curl http://localhost:6333/health

# Test search
curl "http://localhost:8000/api/movies/popular?limit=5"
```

### **Expected Responses**

```json
// API Health
{
  "status": "healthy",
  "service": "CineRAG API",
  "rag_enabled": true,
  "vector_count": 9742
}

// Qdrant Health
{
  "status": "ok"
}
```

## 🔍 Troubleshooting

### **Common Issues**

#### **API Container Failing**

```bash
# Check logs
docker-compose -f docker/docker-compose.yml logs cinerag-api

# Common fixes
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.yml build --no-cache
docker-compose -f docker/docker-compose.yml up -d
```

#### **Vector Database Issues**

```bash
# Reset Qdrant data
docker-compose -f docker/docker-compose.yml down -v
docker-compose -f docker/docker-compose.yml up -d
```

#### **Frontend Not Loading**

```bash
# Check if API is running
curl http://localhost:8000/health

# Restart frontend
docker-compose -f docker/docker-compose.yml restart frontend
```

### **Port Conflicts**

If ports 3000, 6333, 6334, or 8000 are in use:

```yaml
# Edit docker/docker-compose.yml
services:
  cinerag-api:
    ports:
      - "8001:8000" # Change host port
  qdrant:
    ports:
      - "6335:6333" # Change host port
      - "6336:6334"
```

## 🚀 Production Deployment

### **Environment Setup**

```bash
# Production environment
DEBUG=False
FRONTEND_URL=https://your-domain.com

# Security
ALLOWED_HOSTS=your-domain.com
CORS_ORIGINS=https://your-domain.com

# Performance
WORKERS=4
MAX_CONNECTIONS=1000
```

### **Reverse Proxy (Nginx)**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### **SSL/HTTPS**

```bash
# Let's Encrypt setup
sudo certbot --nginx -d your-domain.com
```

## 📈 Scaling

### **Horizontal Scaling**

```yaml
# docker-compose.prod.yml
services:
  cinerag-api:
    scale: 3
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
```

### **Resource Allocation**

```yaml
services:
  cinerag-api:
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 2G
        reservations:
          cpus: "0.5"
          memory: 1G
```

## 🔒 Security

### **Production Checklist**

- [ ] Set `DEBUG=False`
- [ ] Configure CORS origins
- [ ] Add rate limiting
- [ ] Implement API authentication
- [ ] Enable HTTPS
- [ ] Regular security updates

### **API Key Management**

```bash
# Use environment variables
export TMDB_API_KEY=your_key
export OPENAI_API_KEY=your_key

# Or secure key management service
```

## 📊 Monitoring

### **Basic Monitoring**

```bash
# Container health
docker-compose -f docker/docker-compose.yml ps

# Resource usage
docker stats

# Logs
docker-compose -f docker/docker-compose.yml logs -f
```

### **Advanced Monitoring**

```yaml
# Add to docker-compose.yml
prometheus:
  image: prom/prometheus
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana
  ports:
    - "3001:3000"
```

## 🔄 Updates & Maintenance

### **Updating the Application**

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker/docker-compose.yml down
docker-compose -f docker/docker-compose.yml build --no-cache
docker-compose -f docker/docker-compose.yml up -d
```

### **Database Backup**

```bash
# Backup Qdrant data
docker cp docker-qdrant-1:/qdrant/storage ./qdrant-backup-$(date +%Y%m%d)

# Backup environment
cp config/.env config/.env.backup
```

## 📞 Support

### **Getting Help**

- **Logs**: Check Docker logs for error details
- **Health Checks**: Use `/health` endpoints
- **Documentation**: API docs at `/api/docs`
- **Issues**: Create GitHub issue with logs

### **Performance Tuning**

- Monitor response times via `/health`
- Check cache hit rates in logs
- Scale containers based on load
- Optimize vector database settings

---

**🎯 This deployment guide gets CineRAG running in production with industry-standard practices for monitoring, security, and scalability.**
