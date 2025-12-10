"""
FastAPI Main Application
Smart Travel Recommendation API
"""
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import logging

from configs.settings import settings
from api.routes import itinerary, recommendation

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## 🌏 Smart Travel Recommendation API

AI-powered travel itinerary generation using advanced machine learning algorithms.

### Features
- 🤖 **Hybrid Recommendations**: BERT embeddings + SVD collaborative filtering
- 🗺️ **Optimized Routing**: Dijkstra shortest path + Greedy block scheduling
- ⚡ **Fast Response**: < 10s for 3-day itineraries (with caching)
- 🌍 **Multi-city Support**: Works with any city in database
- 🎯 **Personalization**: Dynamic alpha calculation based on user engagement

### Tech Stack
- **ML Models**: BERT (paraphrase-multilingual-mpnet-base-v2), SVD
- **Algorithms**: Dijkstra, Greedy Constraint Satisfaction
- **Database**: MongoDB
- **Caching**: BERT embedding cache (~700x speedup)

### Performance
- **Cold run**: ~40-50s (first time)
- **Warm run**: ~5-10s (cached embeddings)
- **Accuracy**: POD ~32%, Precision ~24%, F1 ~0.27 (Top-20)

---
**Documentation**: [API Docs](/docs) | [Integration Guide](/docs/integration)
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
    return response

# Include routers
app.include_router(itinerary.router, prefix="/api/v1", tags=["Itinerary"])
app.include_router(recommendation.router, prefix="/api/v1", tags=["Recommendations"])

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    API Root - Welcome message
    """
    return {
        "message": "Smart Travel Recommendation API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "generate_itinerary": "/api/v1/generate-itinerary",
            "get_recommendations": "/api/v1/recommendations"
        }
    }

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring
    """
    try:
        # Test MongoDB connection
        from src.database import MongoDBHandler
        db = MongoDBHandler()
        db.client.server_info()  # Will raise exception if can't connect
        
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "database": "connected",
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "details": str(exc) if settings.DEBUG else None
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
