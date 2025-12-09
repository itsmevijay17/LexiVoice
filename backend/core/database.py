# MongoDB connection
"""
MongoDB database connection using pymongo (synchronous).
"""
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database as PyMongoDatabase
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database manager using pymongo."""
    
    client: MongoClient = None
    db: PyMongoDatabase = None
    
    @classmethod
    def connect_db(cls):
        """Connect to MongoDB."""
        try:
            cls.client = MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            
            # Test connection
            cls.client.admin.command('ping')
            cls.db = cls.client[settings.MONGODB_DB_NAME]
            
            logger.info(f"✅ Connected to MongoDB: {settings.MONGODB_DB_NAME}")
            
            # Create indexes
            cls._create_indexes()
            
        except ConnectionFailure as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            raise
    
    @classmethod
    def close_db(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            logger.info("🔌 MongoDB connection closed")
    
    @classmethod
    def _create_indexes(cls):
        """Create database indexes for performance."""
        try:
            # QueryLog collection indexes
            cls.db.query_logs.create_index([("session_id", ASCENDING)])
            cls.db.query_logs.create_index([("country", ASCENDING)])
            cls.db.query_logs.create_index([("timestamp", DESCENDING)])
            
            # Feedback collection indexes
            cls.db.feedback.create_index([("query_id", ASCENDING)])
            cls.db.feedback.create_index([("session_id", ASCENDING)])
            cls.db.feedback.create_index([("created_at", DESCENDING)])
            
            logger.info("✅ Database indexes created")
        except Exception as e:
            logger.warning(f"⚠️ Index creation warning: {e}")
    
    @classmethod
    def get_db(cls) -> PyMongoDatabase:
        """Get database instance."""
        if cls.db is None:
            raise Exception("Database not connected. Call connect_db() first.")
        return cls.db
    
    @classmethod
    def health_check(cls) -> bool:
        """Check if database connection is healthy."""
        try:
            cls.client.admin.command('ping')
            return True
        except Exception:
            return False


# Dependency for FastAPI routes
def get_database() -> PyMongoDatabase:
    """FastAPI dependency to get database instance."""
    return Database.get_db()