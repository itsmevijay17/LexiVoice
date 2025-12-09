"""
FastAPI application entry point for LexiVoice (MVP - No Auth).
Includes RAG chat, feedback, and analytics endpoints.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Core configuration
from backend.core.config import settings
from backend.core.database import Database, get_database
from backend.core.crud import QueryLogCRUD, FeedbackCRUD
from backend.core.retriever import preload_retrievers

# Routers
from backend.routers import chat, feedback

# ====================== Logging Configuration ======================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ====================== Application Lifespan ======================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown management."""
    try:
        # Startup
        logger.info(f"🚀 Starting {settings.PROJECT_NAME}...")
        Database.connect_db()
        logger.info("✅ Database connected successfully")
        # Preload FAISS retrievers (loads indexes in background)
        try:
            preload_retrievers()
            logger.info("✅ FAISS retrievers scheduled for background loading")
        except Exception as e:
            logger.warning(f"Could not preload FAISS retrievers: {e}")
        logger.info("✅ Application started successfully")
        yield
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
        raise
    finally:
        # Shutdown
        logger.info("🔄 Shutting down application...")
        Database.close_db()
        logger.info("👋 Application stopped")


# ====================== FastAPI App Setup ======================

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Multilingual Legal Assistant with RAG (MVP)",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ====================== Root & Health Endpoints ======================

@app.get("/health")
def health_check():
    """Health check endpoint with database status."""
    db_healthy = Database.health_check()
    return {
        "status": "healthy" if db_healthy else "degraded",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",
        "database": "connected" if db_healthy else "disconnected"
    }


@app.get("/")
def root():
    """Root endpoint for basic info and API navigation."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "chat": f"{settings.API_V1_PREFIX}/chat",
            "feedback": f"{settings.API_V1_PREFIX}/feedback",
            "stats": f"{settings.API_V1_PREFIX}/stats"
        }
    }


# ====================== Statistics Endpoint ======================

@app.get(f"{settings.API_V1_PREFIX}/stats")
def get_stats(db=Depends(get_database)):
    """Fetch overall system statistics and analytics."""
    try:
        # Total queries
        total_queries = db.query_logs.count_documents({})

        # Country-wise breakdown
        country_pipeline = [
            {"$group": {"_id": "$country", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        country_stats = list(db.query_logs.aggregate(country_pipeline))

        # Feedback statistics
        feedback_stats = FeedbackCRUD.get_feedback_stats(db)

        return {
            "total_queries": total_queries,
            "queries_by_country": [
                {"country": item["_id"], "count": item["count"]}
                for item in country_stats
            ],
            "feedback": feedback_stats
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return {"error": "Failed to fetch statistics"}


# ====================== Include Routers ======================

# Main RAG chat endpoint
app.include_router(
    chat.router,
    prefix=f"{settings.API_V1_PREFIX}/chat",
    tags=["Chat"]
)

# Feedback endpoint
app.include_router(
    feedback.router,
    prefix=f"{settings.API_V1_PREFIX}/feedback",
    tags=["Feedback"]
)


# ====================== Local Development Entry ======================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=(settings.ENVIRONMENT == "development")
    )
