"""
CRUD operations for MongoDB collections (MVP - No Auth).
"""
from pymongo.database import Database
from datetime import datetime
from typing import Optional, List, Dict, Any
from bson import ObjectId


class QueryLogCRUD:
    """CRUD operations for QueryLog collection."""
    
    @staticmethod
    def create_query_log(
        db: Database,
        session_id: Optional[str],
        country: str,
        user_language: str,
        query: str,
        response: Dict[str, Any],
        processing_time_ms: Optional[float] = None
    ) -> str:
        """Create a new query log."""
        log_doc = {
            "session_id": session_id,
            "country": country,
            "user_language": user_language,
            "query": query,
            "response": response,
            "timestamp": datetime.utcnow(),
            "processing_time_ms": processing_time_ms
        }
        
        result = db.query_logs.insert_one(log_doc)
        return str(result.inserted_id)
    
    @staticmethod
    def get_query_log_by_id(db: Database, query_id: str) -> Optional[Dict]:
        """Get query log by ID."""
        try:
            log = db.query_logs.find_one({"_id": ObjectId(query_id)})
            if log:
                log["id"] = str(log["_id"])
                del log["_id"]
            return log
        except Exception as e:
            return None
    
    @staticmethod
    def get_session_query_logs(
        db: Database,
        session_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """Get recent query logs for a session."""
        cursor = db.query_logs.find(
            {"session_id": session_id}
        ).sort("timestamp", -1).limit(limit)
        
        logs = []
        for log in cursor:
            log["id"] = str(log["_id"])
            del log["_id"]
            logs.append(log)
        
        return logs
    
    @staticmethod
    def get_country_stats(db: Database, country: str) -> Dict[str, Any]:
        """Get statistics for a specific country."""
        total_queries = db.query_logs.count_documents({"country": country})
        
        # Average processing time
        pipeline = [
            {"$match": {"country": country, "processing_time_ms": {"$exists": True}}},
            {"$group": {"_id": None, "avg_time": {"$avg": "$processing_time_ms"}}}
        ]
        
        avg_result = list(db.query_logs.aggregate(pipeline))
        avg_time = avg_result[0]["avg_time"] if avg_result else 0
        
        return {
            "country": country,
            "total_queries": total_queries,
            "avg_processing_time_ms": round(avg_time, 2)
        }


class FeedbackCRUD:
    """CRUD operations for Feedback collection."""
    
    @staticmethod
    def create_feedback(
        db: Database,
        query_id: str,
        rating: int,
        user_language: str = "en",
        comment: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Create feedback for a query."""
        feedback_doc = {
            "query_id": query_id,
            "session_id": session_id,
            "user_language": user_language,
            "rating": rating,
            "comment": comment,
            "created_at": datetime.utcnow()
        }
        
        result = db.feedback.insert_one(feedback_doc)
        return str(result.inserted_id)
    
    @staticmethod
    def get_feedback_by_query_id(db: Database, query_id: str) -> Optional[Dict]:
        """Get feedback for a specific query."""
        feedback = db.feedback.find_one({"query_id": query_id})
        if feedback:
            feedback["id"] = str(feedback["_id"])
            del feedback["_id"]
        return feedback
    
    @staticmethod
    def get_average_rating(db: Database) -> float:
        """Get average rating across all feedback."""
        pipeline = [
            {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}}}
        ]
        
        result = list(db.feedback.aggregate(pipeline))
        return round(result[0]["avg_rating"], 2) if result else 0.0
    
    @staticmethod
    def get_feedback_stats(db: Database) -> Dict[str, Any]:
        """Get overall feedback statistics."""
        total_feedback = db.feedback.count_documents({})
        avg_rating = FeedbackCRUD.get_average_rating(db)
        
        # Rating distribution
        pipeline = [
            {"$group": {"_id": "$rating", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}}
        ]
        
        distribution = list(db.feedback.aggregate(pipeline))
        rating_dist = {item["_id"]: item["count"] for item in distribution}
        
        return {
            "total_feedback": total_feedback,
            "average_rating": avg_rating,
            "rating_distribution": rating_dist
        }