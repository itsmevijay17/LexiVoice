# Feedback route handler
"""
Feedback router - Collect user feedback on responses.

Allows users to rate responses (1-5 stars) and provide comments.
This data is valuable for:
- Evaluating system performance
- Identifying problem areas
- Training/fine-tuning models later
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.database import Database
import logging

from backend.core.schemas import FeedbackCreate, FeedbackResponse
from backend.core.database import get_database
from backend.core.crud import FeedbackCRUD, QueryLogCRUD

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback: FeedbackCreate,
    db: Database = Depends(get_database)
) -> FeedbackResponse:
    """
    Submit feedback for a query response.
    
    Args:
        feedback: FeedbackCreate with query_id, rating, comment
        db: Database instance
        
    Returns:
        FeedbackResponse with confirmation
        
    Raises:
        HTTPException: If query_id doesn't exist or feedback already submitted
    """
    logger.info(f"📝 Feedback submission for query: {feedback.query_id}")
    logger.info(f"   Rating: {feedback.rating}/5")
    
    try:
        # Step 1: Verify query exists
        query_log = QueryLogCRUD.get_query_log_by_id(db, feedback.query_id)
        
        if not query_log:
            logger.warning(f"⚠️ Query not found: {feedback.query_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query with ID {feedback.query_id} not found"
            )
        
        # Step 2: Check if feedback already exists
        existing_feedback = FeedbackCRUD.get_feedback_by_query_id(db, feedback.query_id)
        
        if existing_feedback:
            logger.warning(f"⚠️ Feedback already exists for query: {feedback.query_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Feedback already submitted for this query"
            )
        
        # Step 3: Save feedback
        feedback_id = FeedbackCRUD.create_feedback(
            db=db,
            query_id=feedback.query_id,
            rating=feedback.rating,
            comment=feedback.comment,
            session_id=query_log.get('session_id')
        )
        
        logger.info(f"✅ Feedback saved with ID: {feedback_id}")
        
        # Step 4: Return response
        from datetime import datetime
        return FeedbackResponse(
            id=feedback_id,
            query_id=feedback.query_id,
            rating=feedback.rating,
            comment=feedback.comment,
            created_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error saving feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save feedback: {str(e)}"
        )


@router.get("/stats")
async def get_feedback_stats(db: Database = Depends(get_database)):
    """
    Get feedback statistics.
    
    Returns:
        Overall feedback stats (avg rating, distribution, etc.)
    """
    try:
        stats = FeedbackCRUD.get_feedback_stats(db)
        
        logger.info(f"📊 Feedback stats requested")
        logger.info(f"   Total feedback: {stats.get('total_feedback', 0)}")
        logger.info(f"   Average rating: {stats.get('average_rating', 0)}/5")
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error fetching feedback stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch statistics: {str(e)}"
        )