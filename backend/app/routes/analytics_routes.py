from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.database import get_async_session
from app.routes.auth_routes import get_current_user

router = APIRouter()
security = HTTPBearer()

class EmailMetrics(BaseModel):
    total_emails: int
    emails_by_priority: Dict[str, int]
    emails_by_category: Dict[str, int]
    average_response_time: float
    productivity_score: float

class UserActivityStats(BaseModel):
    emails_processed_today: int
    emails_processed_this_week: int
    emails_processed_this_month: int
    most_active_hours: List[int]
    preferred_categories: List[str]

class TrendData(BaseModel):
    date: str
    email_count: int
    priority_distribution: Dict[str, int]

@router.get("/dashboard", response_model=EmailMetrics)
async def get_dashboard_metrics(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    days: int = Query(30, description="Кількість днів для аналізу")
):
    """
    Отримання метрик для дашборду користувача
    """
    try:
        # TODO: Реальні запити до бази даних
        # Поки що повертаємо моковані дані
        
        mock_metrics = EmailMetrics(
            total_emails=247,
            emails_by_priority={
                "low": 89,
                "medium": 125,
                "high": 28,
                "urgent": 5
            },
            emails_by_category={
                "work": 180,
                "personal": 45,
                "marketing": 15,
                "notification": 7
            },
            average_response_time=2.4,  # години
            productivity_score=85.5  # процент
        )
        
        return mock_metrics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка отримання метрик: {str(e)}"
        )

@router.get("/activity", response_model=UserActivityStats)
async def get_user_activity_stats(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Отримання статистики активності користувача
    """
    try:
        # TODO: Реальні запити до бази даних
        
        mock_activity = UserActivityStats(
            emails_processed_today=15,
            emails_processed_this_week=89,
            emails_processed_this_month=347,
            most_active_hours=[9, 10, 14, 15, 16],  # години дня
            preferred_categories=["work", "personal", "notification"]
        )
        
        return mock_activity
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка отримання статистики: {str(e)}"
        )

@router.get("/trends", response_model=List[TrendData])
async def get_email_trends(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    days: int = Query(30, description="Кількість днів для аналізу тренду")
):
    """
    Отримання трендів по електронній пошті
    """
    try:
        # TODO: Реальні запити до бази даних для трендів
        
        # Генеруємо моковані дані для тренду
        trends = []
        base_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            current_date = base_date + timedelta(days=i)
            trend_data = TrendData(
                date=current_date.strftime("%Y-%m-%d"),
                email_count=15 + (i % 10),  # Симуляція змінної кількості листів
                priority_distribution={
                    "low": 5 + (i % 3),
                    "medium": 8 + (i % 4),
                    "high": 2 + (i % 2),
                    "urgent": 0 if i % 5 == 0 else 1
                }
            )
            trends.append(trend_data)
        
        return trends
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка отримання трендів: {str(e)}"
        )

@router.get("/performance")
async def get_performance_insights(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Отримання аналізу ефективності роботи з поштою
    """
    try:
        # TODO: Реальний аналіз ефективності на основі даних
        
        insights = {
            "response_time_improvement": "12% швидше ніж минулого тижня",
            "priority_accuracy": "89% правильно визначених пріоритетів",
            "productivity_tips": [
                "Рекомендуємо обробляти листи batch-ами о 9:00, 13:00 та 17:00",
                "Ваш пік продуктивності між 14:00-16:00",
                "Розгляньте можливість створення шаблонів для частих відповідей"
            ],
            "email_load_analysis": {
                "peak_days": ["вівторок", "середа", "четвер"],
                "average_daily_emails": 23,
                "busiest_hour": "10:00-11:00"
            },
            "category_insights": {
                "most_time_consuming": "work emails",
                "quick_to_process": "notifications",
                "needs_attention": "marketing emails (often ignored)"
            }
        }
        
        return insights
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка аналізу ефективності: {str(e)}"
        )

@router.get("/export")
async def export_analytics_data(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    format: str = Query("json", description="Формат експорту: json, csv"),
    start_date: Optional[str] = Query(None, description="Початкова дата (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Кінцева дата (YYYY-MM-DD)")
):
    """
    Експорт аналітичних даних користувача
    """
    try:
        if format not in ["json", "csv"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Підтримувані формати: json, csv"
            )
        
        # TODO: Реальний експорт даних з бази
        
        export_data = {
            "user_id": current_user["user_id"],
            "export_date": datetime.now().isoformat(),
            "period": {
                "start": start_date or "2024-01-01",
                "end": end_date or datetime.now().strftime("%Y-%m-%d")
            },
            "analytics": {
                "total_emails_analyzed": 347,
                "categories_breakdown": {
                    "work": 180,
                    "personal": 45,
                    "marketing": 122
                },
                "ai_accuracy_metrics": {
                    "priority_accuracy": 89.5,
                    "category_accuracy": 92.1,
                    "sentiment_accuracy": 86.3
                }
            }
        }
        
        return export_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка експорту: {str(e)}"
        )