from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, text
from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging

from app.services.database import get_async_session
from app.models.database import EmailAnalysis

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stats")
async def get_email_stats(db: AsyncSession = Depends(get_async_session)) -> Dict[str, Any]:
    """Отримати статистику по email аналізу"""
    try:
        # Загальна кількість листів
        total_result = await db.execute(
            text("SELECT COUNT(*) as count FROM email_analyses")
        )
        total_emails = total_result.scalar() or 0
        
        # Листи за сьогодні
        today = datetime.now().date()
        today_result = await db.execute(
            text("SELECT COUNT(*) as count FROM email_analyses WHERE DATE(processed_at) = :today"),
            {"today": today}
        )
        analyzed_today = today_result.scalar() or 0
        
        # Рівні загроз (використовуємо urgency_score)
        threat_result = await db.execute(
            text("""
                SELECT 
                    CASE
                        WHEN urgency_score >= 0.8 THEN 'high'
                        WHEN urgency_score >= 0.5 THEN 'medium'
                        ELSE 'low'
                    END as level,
                    COUNT(*) as count 
                FROM email_analyses 
                WHERE urgency_score IS NOT NULL 
                GROUP BY 
                    CASE
                        WHEN urgency_score >= 0.8 THEN 'high'
                        WHEN urgency_score >= 0.5 THEN 'medium'
                        ELSE 'low'
                    END
            """)
        )
        threat_data = threat_result.fetchall()
        threat_levels = {"high": 0, "medium": 0, "low": 0}
        for row in threat_data:
            if row.level in threat_levels:
                threat_levels[row.level] = row.count
        
        # Категорії email (конвертуємо в spam категорії для UI)
        category_result = await db.execute(
            text("""
                SELECT 
                    CASE 
                        WHEN category = 'marketing' THEN 'Реклама'
                        WHEN category = 'spam' THEN 'Фішинг'
                        WHEN category = 'notification' THEN 'Шахрайство'
                        WHEN category = 'work' THEN 'Малвар'
                        ELSE 'Інше'
                    END as category,
                    COUNT(*) as count 
                FROM email_analyses 
                WHERE category IS NOT NULL 
                GROUP BY category 
                ORDER BY count DESC 
                LIMIT 10
            """)
        )
        category_data = category_result.fetchall()
        categories = [{"name": row.category, "count": row.count} for row in category_data]
        
        if not categories:
            categories = [
                {"name": "Фішинг", "count": 0},
                {"name": "Реклама", "count": 0},
                {"name": "Шахрайство", "count": 0},
                {"name": "Малвар", "count": 0},
                {"name": "Інше", "count": 0}
            ]
        
        return {
            "totalEmails": total_emails,
            "analyzedToday": analyzed_today,
            "threatLevels": threat_levels,
            "categories": categories
        }
        
    except Exception as e:
        logger.error(f"Error getting email stats: {e}")
        # Повернути дефолтні дані при помилці
        return {
            "totalEmails": 0,
            "analyzedToday": 0,
            "threatLevels": {"high": 0, "medium": 0, "low": 0},
            "categories": [
                {"name": "Фішинг", "count": 0},
                {"name": "Реклама", "count": 0},
                {"name": "Шахрайство", "count": 0},
                {"name": "Малвар", "count": 0},
                {"name": "Інше", "count": 0}
            ]
        }

@router.get("/recent-emails")
async def get_recent_emails(
    limit: int = 10, 
    db: AsyncSession = Depends(get_async_session)
) -> List[Dict[str, Any]]:
    """Отримати останні оброблені листи"""
    try:
        result = await db.execute(
            text("""
                SELECT 
                    id, subject, sender, received_at, 
                    priority, urgency_score, ai_summary,
                    processed_at
                FROM email_analyses 
                ORDER BY processed_at DESC 
                LIMIT :limit
            """),
            {"limit": limit}
        )
        
        emails = []
        for row in result.fetchall():
            emails.append({
                "id": str(row.id),
                "subject": row.subject or "Без теми",
                "sender": row.sender or "Невідомий відправник", 
                "received_date": row.received_at.isoformat() if row.received_at else datetime.now().isoformat(),
                "priority": row.priority,
                "threat_level": "medium" if row.urgency_score > 0.5 else "low",  # Використовуємо urgency_score
                "analysis_summary": row.ai_summary
            })
        
        return emails
        
    except Exception as e:
        logger.error(f"Error getting recent emails: {e}")
        return []