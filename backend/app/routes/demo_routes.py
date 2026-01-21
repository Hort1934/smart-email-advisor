from fastapi import APIRouter, HTTPException, status
from app.models.schemas import EmailAnalysisRequest, EmailAnalysisResponse
from app.services.ai_service import AIService

router = APIRouter()

@router.post("/analyze-demo", response_model=EmailAnalysisResponse)
async def analyze_email_demo(request: EmailAnalysisRequest):
    """
    Демонстраційний аналіз електронного листа без авторизації
    """
    try:
        ai_service = AIService()
        analysis_result = await ai_service.analyze_email(request)
        return analysis_result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка при аналізі листа: {str(e)}"
        )

@router.get("/info")
async def get_api_info():
    """
    Інформація про API
    """
    return {
        "name": "Smart Email Advisor API",
        "version": "1.0.0",
        "description": "AI-орієнтований сервіс для інтелектуального аналізу електронних листів",
        "endpoints": {
            "health": "/health",
            "demo_analysis": "/api/demo/analyze-demo",
            "auth_login": "/api/auth/login",
            "auth_register": "/api/auth/register",
            "email_analysis": "/api/emails/analyze",
            "analytics": "/api/analytics/dashboard"
        },
        "features": [
            "Аналіз пріоритету листів",
            "Категоризація електронної пошти",
            "Визначення тональності",
            "Генерація розумних рекомендацій",
            "Аналітика та звітність"
        ]
    }