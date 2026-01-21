from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List

from app.models.schemas import (
    EmailAnalysisRequest, 
    EmailAnalysisResponse,
    RecommendationRequest,
    SmartRecommendation
)
from app.services.ai_service import AIService
from app.services.database import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
security = HTTPBearer()

async def get_ai_service():
    """Dependency to get AI service"""
    return AIService()

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