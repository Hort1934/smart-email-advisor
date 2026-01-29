from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict
import logging
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.models.schemas import (
    EmailAnalysisRequest, 
    EmailAnalysisResponse,
    RecommendationRequest,
    SmartRecommendation
)
from app.services.ai_service import AIService
from app.services.email_service import EmailService
from app.services.email_storage_service import EmailStorageService
from app.services.smart_assistant_service import SmartEmailAssistant
from app.services.database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

async def get_ai_service():
    """Dependency to get AI service"""
    return AIService()

async def get_email_service():
    """Dependency to get Email service"""
    return EmailService()

@router.post("/analyze", response_model=EmailAnalysisResponse)
async def analyze_email(
    request: EmailAnalysisRequest,
    ai_service: AIService = Depends(get_ai_service),
    db: AsyncSession = Depends(get_async_session),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Аналіз електронного листа з використанням AI
    
    Повертає:
    - Пріоритет листа
    - Категорію
    - Тональність
    - Ключові пункти
    - Рекомендовані дії
    """
    try:
        # Виконання AI аналізу
        analysis_result = await ai_service.analyze_email(request)
        
        # TODO: Зберегти результат аналізу в базу даних
        # await save_analysis_to_db(analysis_result, db)
        
        return analysis_result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка при аналізі листа: {str(e)}"
        )

@router.post("/summarize")
async def summarize_email(
    request: EmailAnalysisRequest,
    ai_service: AIService = Depends(get_ai_service),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Створення короткого резюме листа
    """
    try:
        summary = await ai_service.generate_summary(request.content)
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка при створенні резюме: {str(e)}"
        )

@router.post("/recommendations", response_model=List[SmartRecommendation])
async def get_smart_recommendations(
    request: RecommendationRequest,
    ai_service: AIService = Depends(get_ai_service),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Отримання розумних рекомендацій щодо листа
    """
    try:
        recommendations = await ai_service.generate_smart_recommendations(
            request.email_content,
            request.user_context
        )
        return recommendations
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка при генерації рекомендацій: {str(e)}"
        )

@router.post("/{email_id}/archive")
async def archive_email(
    email_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Архівування листа
    """
    try:
        # Оновлюємо статус листа в базі даних
        await db.execute(
            text("UPDATE email_analyses SET is_archived = true WHERE id = :email_id"),
            {"email_id": email_id}
        )
        await db.commit()
        
        return {"success": True, "message": "Лист успішно архівовано"}
        
    except Exception as e:
        logger.error(f"Error archiving email: {e}")
        raise HTTPException(status_code=500, detail="Failed to archive email")

@router.post("/batch-analyze")
async def batch_analyze_emails(
    requests: List[EmailAnalysisRequest],
    ai_service: AIService = Depends(get_ai_service),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Пакетний аналіз декількох листів
    """
    if len(requests) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Максимум 50 листів за один запит"
        )
    
    try:
        results = []
        for email_request in requests:
            analysis = await ai_service.analyze_email(email_request)
            results.append({
                "email_subject": email_request.subject,
                "analysis": analysis
            })
        
        return {"batch_results": results}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка при пакетному аналізі: {str(e)}"
        )

@router.get("/spam")
async def get_spam_emails(
    limit: int = 10,
    email_service: EmailService = Depends(get_email_service)
):
    """
    Отримання листів зі спаму
    """
    try:
        emails = await email_service.get_spam_emails(limit)
        
        # Конвертація в словники для JSON відповіді
        email_list = []
        for email_msg in emails:
            email_list.append({
                "uid": email_msg.uid,
                "subject": email_msg.subject,
                "sender": email_msg.sender,
                "recipient": email_msg.recipient,
                "content_preview": email_msg.content[:200] + "..." if len(email_msg.content) > 200 else email_msg.content,
                "received_at": email_msg.received_at.isoformat(),
                "is_read": email_msg.is_read,
                "folder": email_msg.folder,
                "attachments_count": len(email_msg.attachments)
            })
        
        return {
            "emails": email_list,
            "total_count": len(email_list),
            "source_folder": "Спам"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка при отриманні spam листів: {str(e)}"
        )

@router.post("/analyze-from-spam")
async def analyze_spam_emails(
    limit: int = 20,
    email_service: EmailService = Depends(get_email_service),
    ai_service: AIService = Depends(get_ai_service),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Автоматичний аналіз листів зі спам папки з збереженням в БД
    """
    try:
        # Отримання листів зі спаму
        spam_emails = await email_service.get_spam_emails(limit)
        
        results = []
        for email_msg in spam_emails:
            # Створення запиту для аналізу
            analysis_request = EmailAnalysisRequest(
                subject=email_msg.subject,
                content=email_msg.content,
                sender=email_msg.sender,
                recipient=email_msg.recipient,
                received_at=email_msg.received_at
            )
            
            # AI аналіз
            analysis_result = await ai_service.analyze_email(analysis_request)
            
            # Збереження в БД
            try:
                db_record = await EmailStorageService.save_email_analysis(
                    db=db,
                    email_msg=email_msg,
                    analysis_result=analysis_result,
                    user_id=None  # Автоматичний аналіз без прив'язки до користувача
                )
                
                saved_to_db = True
                db_id = db_record.id
                
            except Exception as save_error:
                logger.error(f"Failed to save email analysis to DB: {save_error}")
                saved_to_db = False
                db_id = None
            
            results.append({
                "email": {
                    "uid": email_msg.uid,
                    "subject": email_msg.subject,
                    "sender": email_msg.sender,
                    "received_at": email_msg.received_at.isoformat(),
                    "folder": email_msg.folder
                },
                "analysis": {
                    "priority": analysis_result.priority,
                    "category": analysis_result.category,
                    "summary": {
                        "content": analysis_result.summary.content if analysis_result.summary else "",
                        "key_points": analysis_result.summary.key_points if analysis_result.summary else [],
                        "action_required": analysis_result.summary.action_required if analysis_result.summary else False,
                        "urgency_score": analysis_result.summary.urgency_score if analysis_result.summary else 0.5,
                        "sentiment": analysis_result.summary.sentiment if analysis_result.summary else "neutral"
                    },
                    "recommendations": [
                        {
                            "action_type": rec.action_type,
                            "description": rec.description,
                            "confidence": rec.confidence,
                            "reasoning": getattr(rec, 'reasoning', '')
                        } for rec in analysis_result.recommendations
                    ] if analysis_result.recommendations else [],
                    "confidence": analysis_result.confidence,
                    "processing_time": analysis_result.processing_time,
                    "model_version": analysis_result.model_version
                },
                "database": {
                    "saved": saved_to_db,
                    "record_id": db_id
                }
            })
        
        successful_saves = sum(1 for r in results if r["database"]["saved"])
        
        return {
            "analyzed_emails": results,
            "total_analyzed": len(results),
            "source_folder": "Спам",
            "saved_to_database": successful_saves
        }
        
    except Exception as e:
        logger.error(f"Error analyzing spam emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка при аналізі spam листів: {str(e)}"
        )

@router.get("/")
async def get_all_emails(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Отримання всіх збережених листів з бази даних
    """
    try:
        query = text("""
            SELECT 
                e.id,
                e.sender,
                e.recipient,
                e.subject,
                e.content as body,
                e.priority,
                false as is_spam,
                e.received_at as created_at,
                e.urgency_score,
                e.communication_tone,
                e.emotions,
                e.practical_value,
                e.email_uid
            FROM email_analyses e 
            ORDER BY e.received_at DESC 
            LIMIT :limit OFFSET :offset
        """)
        
        result = await db.execute(query, {"limit": limit, "offset": offset})
        emails = result.fetchall()
        
        email_list = []
        for email in emails:
            # Parse emotions if it's a JSON string
            emotions = email.emotions
            if isinstance(emotions, str):
                try:
                    emotions = json.loads(emotions)
                except:
                    emotions = []
            elif emotions is None:
                emotions = []
            
            email_list.append({
                "id": email.id,
                "sender": email.sender,
                "recipient": email.recipient,
                "subject": email.subject,
                "body": email.body,
                "priority": email.priority,
                "is_spam": email.is_spam,
                "created_at": email.created_at.isoformat() if email.created_at else None,
                "urgency_score": email.urgency_score,
                "communication_tone": email.communication_tone,
                "emotions": emotions,
                "practical_value": email.practical_value,
                "email_uid": email.email_uid
            })
        
        # Get total count
        count_query = text("SELECT COUNT(*) FROM email_analyses")
        count_result = await db.execute(count_query)
        total_count = count_result.scalar()
        
        return {
            "emails": email_list,
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error getting emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка при отриманні листів: {str(e)}"
        )

@router.get("/{email_id}")
async def get_email_by_id(
    email_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Отримання конкретного листа за ID
    """
    try:
        query = text("""
            SELECT 
                e.id,
                e.sender,
                e.recipient,
                e.subject,
                e.content as body,
                e.priority,
                false as is_spam,
                e.received_at as created_at,
                e.urgency_score,
                e.communication_tone,
                e.emotions,
                e.practical_value,
                e.email_uid
            FROM email_analyses e 
            WHERE e.id = :email_id
        """)
        
        result = await db.execute(query, {"email_id": email_id})
        email = result.fetchone()
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Лист не знайдено"
            )
        
        # Parse emotions if it's a JSON string
        emotions = email.emotions
        if isinstance(emotions, str):
            try:
                emotions = json.loads(emotions)
            except:
                emotions = []
        elif emotions is None:
            emotions = []
        
        return {
            "id": email.id,
            "sender": email.sender,
            "recipient": email.recipient,
            "subject": email.subject,
            "body": email.body,
            "priority": email.priority,
            "is_spam": email.is_spam,
            "created_at": email.created_at.isoformat() if email.created_at else None,
            "urgency_score": email.urgency_score,
            "communication_tone": email.communication_tone,
            "emotions": emotions,
            "practical_value": email.practical_value,
            "email_uid": email.email_uid
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email {email_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка при отриманні листа: {str(e)}"
        )

@router.get("/folders")
async def list_email_folders(
    email_service: EmailService = Depends(get_email_service)
):
    """
    Отримання списку доступних email папок
    """
    try:
        folders = await email_service.list_folders()
        return {
            "folders": folders,
            "total_count": len(folders),
            "message": "Список доступних папок"
        }
        
    except Exception as e:
        logger.error(f"Error getting email folders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка при отриманні списку папок: {str(e)}"
        )