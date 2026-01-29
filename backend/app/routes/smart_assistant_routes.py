"""
Smart Assistant Routes - Персональний AI помічник для email
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, insert, update
import json
import logging

from app.models.schemas import (
    SmartRecommendation, 
    CommunicationAnalysis, 
    PersonalizedAnalysis,
    UserFeedback,
    EmailAnalysisResponse
)
from app.services.smart_assistant_service import SmartEmailAssistant
from app.services.email_service import EmailService, EmailMessage
from app.services.database import get_async_session
from app.models.database import EmailAnalysis, EmailRecommendation, UserFeedback as UserFeedbackDB, UserContext

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

class EmailSmartAnalysisRequest(BaseModel):
    email_uid: str
    analyze_tone: bool = True
    generate_response: bool = False
    user_context_override: Optional[Dict[str, Any]] = None

class SmartAnalysisResponse(BaseModel):
    basic_analysis: EmailAnalysisResponse
    smart_recommendations: List[SmartRecommendation]
    communication_analysis: CommunicationAnalysis
    personalized_insights: PersonalizedAnalysis
    suggested_actions: List[str]
    confidence: float

class PersonalizationSettings(BaseModel):
    communication_style: str = "professional"  # diplomatic, direct, friendly
    response_tone: str = "balanced"  # formal, casual, balanced
    priority_keywords: List[str] = []
    work_hours: Dict[str, str] = {"start": "09:00", "end": "18:00"}
    notification_preferences: Dict[str, Any] = {}

class TrainingDataRequest(BaseModel):
    email_id: str
    user_action: str
    was_recommendation_helpful: bool
    user_satisfaction: int  # 1-5
    improvement_feedback: Optional[str] = None

@router.post("/analyze-smart", response_model=SmartAnalysisResponse)
async def analyze_email_with_smart_assistant(
    request: EmailSmartAnalysisRequest,
    user_id: int = 1,  # TODO: Get from auth
    db: AsyncSession = Depends(get_async_session)
):
    """
    Розумний аналіз листа з персональним контекстом
    """
    try:
        smart_assistant = SmartEmailAssistant()
        
        # Отримуємо лист з бази даних
        email_result = await db.execute(
            select(EmailAnalysis).where(EmailAnalysis.email_uid == request.email_uid)
        )
        email_analysis = email_result.scalar_one_or_none()
        
        if not email_analysis:
            raise HTTPException(status_code=404, detail="Email not found")
        
        # Конвертуємо в EmailMessage для обробки
        email_msg = EmailMessage(
            uid=email_analysis.email_uid,
            subject=email_analysis.subject,
            sender=email_analysis.sender,
            recipient=email_analysis.recipient,
            content=email_analysis.content,
            html_content=email_analysis.html_content or "",
            received_at=email_analysis.received_at,
            message_id=email_analysis.message_id or "",
            folder=email_analysis.folder or "INBOX",
            is_read=email_analysis.is_read or False,
            attachments=[]
        )
        
        # Отримуємо персональний контекст
        user_context = await smart_assistant.get_user_context(user_id, db)
        
        # Застосовуємо override якщо передано
        if request.user_context_override:
            for key, value in request.user_context_override.items():
                if hasattr(user_context, key):
                    setattr(user_context, key, value)
        
        # Проводимо повний аналіз
        basic_analysis, smart_recommendations, comm_analysis = await smart_assistant.analyze_email_comprehensively(
            email_msg, user_context, db
        )
        
        # Створюємо персоналізований аналіз
        personalized_insights = PersonalizedAnalysis(
            practical_value=email_analysis.practical_value or 0.5,
            urgency_score=email_analysis.urgency_score,
            life_impact=email_analysis.life_impact or 0.5,
            relevance=0.7,  # TODO: Calculate based on user patterns
            is_noise=email_analysis.is_noise or False,
            needs_attention=email_analysis.needs_attention or True,
            importance_category=email_analysis.priority,
            recommended_action="review",
            reasoning="Аналіз на основі персональних налаштувань користувача"
        )
        
        # Зберігаємо рекомендації в БД
        await _save_smart_recommendations(db, email_analysis.id, smart_recommendations, user_id)
        
        # Формуємо запропоновані дії
        suggested_actions = [
            rec.action_type for rec in smart_recommendations 
            if rec.confidence > 0.7
        ]
        
        # Конвертуємо dataclass об'єкти в словники для Pydantic
        smart_recs_dict = []
        for rec in smart_recommendations:
            smart_recs_dict.append({
                "action_type": rec.action_type,
                "priority": rec.priority,
                "title": rec.title,
                "description": rec.description,
                "suggested_response": rec.suggested_response,
                "confidence": rec.confidence,
                "reasoning": rec.reasoning,
                "category": rec.category
            })
        
        comm_analysis_dict = {
            "tone": comm_analysis.tone,
            "sentiment": comm_analysis.sentiment,
            "emotions": comm_analysis.emotions,
            "formality_level": comm_analysis.formality_level,
            "urgency_indicators": comm_analysis.urgency_indicators,
            "relationship_context": comm_analysis.relationship_context,
            "communication_style": comm_analysis.communication_style
        }
        
        return SmartAnalysisResponse(
            basic_analysis=basic_analysis,
            smart_recommendations=smart_recs_dict,
            communication_analysis=comm_analysis_dict,
            personalized_insights=personalized_insights,
            suggested_actions=suggested_actions,
            confidence=basic_analysis.confidence
        )
        
    except Exception as e:
        logger.error(f"Error in smart analysis: {e}")
        raise HTTPException(status_code=500, detail="Smart analysis failed")

@router.get("/recommendations/{email_id}")
async def get_smart_recommendations(
    email_id: int,
    db: AsyncSession = Depends(get_async_session)
) -> List[SmartRecommendation]:
    """
    Отримати розумні рекомендації для конкретного листа
    """
    try:
        result = await db.execute(
            select(EmailRecommendation).where(
                EmailRecommendation.email_analysis_id == email_id
            ).order_by(EmailRecommendation.confidence.desc())
        )
        recommendations = result.scalars().all()
        
        return [
            SmartRecommendation(
                action_type=rec.action_type,
                priority=rec.priority,
                title=rec.title,
                description=rec.description,
                suggested_response=rec.suggested_response,
                confidence=rec.confidence,
                reasoning=rec.reasoning,
                category=rec.category
            ) for rec in recommendations
        ]
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recommendations")

@router.post("/generate-response")
async def generate_smart_response(
    email_id: int,
    response_style: str = "diplomatic",
    user_id: int = 1,
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, str]:
    """
    Генерація розумної відповіді на email з урахуванням контексту
    """
    try:
        smart_assistant = SmartEmailAssistant()
        
        # Отримуємо лист
        email_result = await db.execute(
            select(EmailAnalysis).where(EmailAnalysis.id == email_id)
        )
        email_analysis = email_result.scalar_one_or_none()
        
        if not email_analysis:
            raise HTTPException(status_code=404, detail="Email not found")
        
        email_msg = EmailMessage(
            uid=email_analysis.email_uid,
            subject=email_analysis.subject,
            sender=email_analysis.sender,
            content=email_analysis.content,
            received_at=email_analysis.received_at
        )
        
        # Генеруємо відповідь
        if response_style == "diplomatic":
            response = f"Дякую за ваш лист. Ознайомився з інформацією та розгляну всі можливості. Обов'язково повідомлю про результати у найближчий час."
        else:
            response = f"З повагою, \n\nДякую за ваше повідомлення. Я розгляну всі деталі та надам зворотний зв'язок."
        
        return {
            "suggested_response": response,
            "response_style": response_style,
            "detected_tone": "professional",
            "reasoning": f"Відповідь створена в {response_style} стилі"
        }
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate response")

@router.get("/imap-status")
async def check_imap_status():
    """
    Перевірка статусу IMAP підключення
    """
    try:
        from app.services.email_service import EmailService
        email_service = EmailService()
        
        try:
            await email_service.connect()
            await email_service.disconnect()
            return {"status": "connected", "message": "IMAP connection successful"}
        except Exception as e:
            return {"status": "error", "message": f"IMAP connection failed: {str(e)}"}
            
    except Exception as e:
        logger.error(f"Error checking IMAP status: {e}")
        return {"status": "error", "message": "Could not check IMAP status"}

@router.post("/create-task")
async def create_task_from_email(
    task_data: Dict[str, Any],
    user_id: int = 1,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Створення задачі на основі email
    """
    try:
        # Тут можна додати зберігання в базу даних або інтеграцію з task manager
        logger.info(f"Creating task: {task_data}")
        
        return {
            "success": True,
            "message": "Задачу створено",
            "task_id": f"task_{task_data.get('emailId', 0)}_{user_id}"
        }
        
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(status_code=500, detail="Failed to create task")

@router.post("/learn-from-feedback")
async def submit_user_feedback(
    feedback: TrainingDataRequest,
    user_id: int = 1,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Збір зворотного зв'язку для навчання системи
    """
    try:
        smart_assistant = SmartEmailAssistant()
        
        # Зберігаємо фідбек в БД
        feedback_data = {
            "helpful": feedback.was_recommendation_helpful,
            "satisfaction": feedback.user_satisfaction,
            "improvement": feedback.improvement_feedback
        }
        
        await smart_assistant.learn_from_user_feedback(
            feedback.email_id, feedback.user_action, feedback_data, db
        )
        
        return {"message": "Дякуємо за зворотний зв'язок! Система буде вдосконалюватися."}
        
    except Exception as e:
        logger.error(f"Error saving feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to save feedback")

@router.get("/personalization/settings")
async def get_personalization_settings(
    user_id: int = 1,
    db: AsyncSession = Depends(get_async_session)
) -> PersonalizationSettings:
    """
    Отримання персональних налаштувань користувача
    """
    try:
        result = await db.execute(
            select(UserContext).where(UserContext.user_id == user_id)
        )
        context = result.scalar_one_or_none()
        
        if not context:
            # Створюємо базовий контекст
            return PersonalizationSettings()
        
        return PersonalizationSettings(
            communication_style=context.communication_style,
            response_tone=context.response_style,
            priority_keywords=context.priority_keywords or [],
            work_hours={
                "start": context.work_hours_start,
                "end": context.work_hours_end
            },
            notification_preferences=context.ai_accuracy_feedback or {}
        )
        
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get settings")

@router.post("/personalization/settings")
async def update_personalization_settings(
    settings: PersonalizationSettings,
    user_id: int = 1,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Оновлення персональних налаштувань
    """
    try:
        # Перевіряємо чи існує контекст
        result = await db.execute(
            select(UserContext).where(UserContext.user_id == user_id)
        )
        context = result.scalar_one_or_none()
        
        if context:
            # Оновлюємо існуючий
            await db.execute(
                update(UserContext).where(UserContext.user_id == user_id).values(
                    communication_style=settings.communication_style,
                    response_style=settings.response_tone,
                    priority_keywords=settings.priority_keywords,
                    work_hours_start=settings.work_hours.get("start", "09:00"),
                    work_hours_end=settings.work_hours.get("end", "18:00"),
                    updated_at=datetime.utcnow()
                )
            )
        else:
            # Створюємо новий
            await db.execute(
                insert(UserContext).values(
                    user_id=user_id,
                    communication_style=settings.communication_style,
                    response_style=settings.response_tone,
                    priority_keywords=settings.priority_keywords,
                    work_hours_start=settings.work_hours.get("start", "09:00"),
                    work_hours_end=settings.work_hours.get("end", "18:00")
                )
            )
        
        await db.commit()
        
        return {"message": "Налаштування успішно оновлено"}
        
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update settings")

@router.get("/insights/communication-patterns")
async def get_communication_insights(
    user_id: int = 1,
    days: int = 30,
    db: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Аналітика комунікаційних патернів користувача
    """
    try:
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Аналіз тонів комунікації
        tone_result = await db.execute(
            text("""
                SELECT communication_tone, COUNT(*) as count
                FROM email_analyses 
                WHERE user_id = :user_id 
                AND processed_at > :since_date
                AND communication_tone IS NOT NULL
                GROUP BY communication_tone
                ORDER BY count DESC
            """),
            {"user_id": user_id, "since_date": since_date}
        )
        
        tone_distribution = {row[0]: row[1] for row in tone_result.fetchall()}
        
        # Аналіз контекстів стосунків
        context_result = await db.execute(
            text("""
                SELECT relationship_context, COUNT(*) as count,
                       AVG(urgency_score) as avg_urgency
                FROM email_analyses 
                WHERE user_id = :user_id 
                AND processed_at > :since_date
                AND relationship_context IS NOT NULL
                GROUP BY relationship_context
                ORDER BY count DESC
            """),
            {"user_id": user_id, "since_date": since_date}
        )
        
        context_analysis = {
            row[0]: {"count": row[1], "avg_urgency": float(row[2]) if row[2] else 0.0}
            for row in context_result.fetchall()
        }
        
        # Патерни практичної цінності
        value_result = await db.execute(
            text("""
                SELECT 
                    CASE 
                        WHEN practical_value >= 0.8 THEN 'high'
                        WHEN practical_value >= 0.5 THEN 'medium' 
                        ELSE 'low'
                    END as value_category,
                    COUNT(*) as count,
                    AVG(needs_attention::int) as attention_rate
                FROM email_analyses 
                WHERE user_id = :user_id 
                AND processed_at > :since_date
                AND practical_value IS NOT NULL
                GROUP BY value_category
            """),
            {"user_id": user_id, "since_date": since_date}
        )
        
        value_patterns = {
            row[0]: {"count": row[1], "attention_rate": float(row[2]) if row[2] else 0.0}
            for row in value_result.fetchall()
        }
        
        return {
            "period_days": days,
            "tone_distribution": tone_distribution,
            "relationship_contexts": context_analysis,
            "value_patterns": value_patterns,
            "insights": _generate_communication_insights(tone_distribution, context_analysis, value_patterns)
        }
        
    except Exception as e:
        logger.error(f"Error getting insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to get insights")

def _generate_communication_insights(tone_dist: Dict, context_analysis: Dict, value_patterns: Dict) -> List[str]:
    """Генерація інсайтів на основі аналізу"""
    insights = []
    
    if tone_dist:
        dominant_tone = max(tone_dist.items(), key=lambda x: x[1])[0]
        insights.append(f"Найчастіший тон у вашій комунікації: {dominant_tone}")
    
    if "aggressive" in tone_dist and tone_dist["aggressive"] > 0:
        insights.append("Виявлено агресивні тони в комунікації - рекомендуємо дипломатичні відповіді")
    
    if context_analysis:
        high_urgency_contexts = [
            context for context, data in context_analysis.items() 
            if data["avg_urgency"] > 0.7
        ]
        if high_urgency_contexts:
            insights.append(f"Найбільш термінові контексти: {', '.join(high_urgency_contexts)}")
    
    if value_patterns.get("low", {}).get("count", 0) > value_patterns.get("high", {}).get("count", 0):
        insights.append("Багато листів з низькою практичною цінністю - рекомендуємо налаштувати фільтри")
    
    return insights

async def _save_smart_recommendations(
    db: AsyncSession, 
    email_analysis_id: int, 
    recommendations: List[SmartRecommendation], 
    user_id: int
):
    """Збереження розумних рекомендацій в БД"""
    for rec in recommendations:
        await db.execute(
            insert(EmailRecommendation).values(
                email_analysis_id=email_analysis_id,
                user_id=user_id,
                action_type=rec.action_type,
                priority=rec.priority,
                title=rec.title,
                description=rec.description,
                suggested_response=rec.suggested_response,
                confidence=rec.confidence,
                reasoning=rec.reasoning,
                category=rec.category
            )
        )
    await db.commit()