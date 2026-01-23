import logging
from typing import Dict, Any
from app.models.schemas import (
    EmailAnalysisRequest, 
    EmailAnalysisResponse, 
    EmailPriority, 
    EmailCategory,
    EmailSummary,
    SmartRecommendation
)

logger = logging.getLogger(__name__)

def _convert_ai_result_to_response(ai_result: Dict[str, Any], request: EmailAnalysisRequest) -> EmailAnalysisResponse:
        """Конвертація результату від AI Agent у EmailAnalysisResponse"""
        try:
            # Отримати значення з AI результату
            priority_map = {
                "urgent": EmailPriority.URGENT,
                "high": EmailPriority.HIGH, 
                "medium": EmailPriority.MEDIUM,
                "low": EmailPriority.LOW
            }
            
            category_map = {
                "work": EmailCategory.WORK,
                "personal": EmailCategory.PERSONAL,
                "spam": EmailCategory.SPAM,
                "newsletter": EmailCategory.NEWSLETTER,
                "promotion": EmailCategory.MARKETING,
                "marketing": EmailCategory.MARKETING,
                "notification": EmailCategory.NOTIFICATIONS
            }
            
            priority = priority_map.get(ai_result.get("priority", "medium"), EmailPriority.MEDIUM)
            category = category_map.get(ai_result.get("category", "personal"), EmailCategory.PERSONAL)
            
            # Створити резюме
            summary = EmailSummary(
                content=ai_result.get("summary", ""),
                key_points=ai_result.get("key_points", []),
                action_required=ai_result.get("action_required", False),
                urgency_score=ai_result.get("confidence_score", 0.5),
                sentiment=ai_result.get("sentiment", "neutral")
            )
            
            # Створити рекомендації
            recommendations = []
            ai_recommendations = ai_result.get("recommendations", [])
            
            for rec in ai_recommendations:
                recommendation = SmartRecommendation(
                    action_type=rec.get("type", "suggestion"),
                    description=rec.get("content", ""),
                    confidence=rec.get("confidence", 0.5),
                    reasoning=rec.get("reasoning", "")
                )
                recommendations.append(recommendation)
            
            return EmailAnalysisResponse(
                priority=priority,
                category=category,
                summary=summary,
                recommendations=recommendations,
                confidence=ai_result.get("confidence_score", 0.5),
                processing_time=1.0,  # Додати реальний час обробки
                model_version=ai_result.get("agent_version", "1.0.0")
            )
            
        except Exception as e:
            logger.error(f"Failed to convert AI result: {e}")
            return _fallback_analysis(request)

def _fallback_analysis(request: EmailAnalysisRequest) -> EmailAnalysisResponse:
        """Базовий аналіз як fallback"""
        summary = EmailSummary(
            content="Автоматичний аналіз недоступний",
            key_points=["Email потребує перегляду"],
            action_required=False,
            urgency_score=0.5,
            sentiment="neutral"
        )
        
        return EmailAnalysisResponse(
            priority=EmailPriority.MEDIUM,
            category=EmailCategory.PERSONAL,
            summary=summary,
            recommendations=[],
            confidence=0.3,
            processing_time=0.1,
            model_version="fallback-1.0"
        )