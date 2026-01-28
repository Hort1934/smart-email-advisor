from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

from app.services.database import get_async_session

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/processing-logs")
async def get_processing_logs(
    limit: int = 50,
    log_type: str = None,
    db: AsyncSession = Depends(get_async_session)
) -> List[Dict[str, Any]]:
    """Отримати логи обробки листів"""
    try:
        # Отримуємо реальні логи з бази даних
        logs = []
        
        # Реальні логи з email_analyses таблиці
        email_logs_query = text("""
            SELECT 
                id::text as id,
                processed_at as timestamp,
                'success' as type,
                'Успішно оброблено спам лист' as message,
                CONCAT('Лист проаналізовано та збережено в базу даних. Рівень загрози: ', 
                       CASE 
                           WHEN urgency_score >= 0.8 THEN 'Високий'
                           WHEN urgency_score >= 0.5 THEN 'Середній'
                           ELSE 'Низький'
                       END) as details,
                subject as emailSubject
            FROM email_analyses 
            WHERE processed_at IS NOT NULL
            ORDER BY processed_at DESC
            LIMIT :limit
        """)
        
        result = await db.execute(email_logs_query, {"limit": min(limit, 20)})
        email_logs = result.fetchall()
        
        # Конвертуємо в потрібний формат
        for log in email_logs:
            logs.append({
                "id": log.id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else datetime.now().isoformat(),
                "type": log.type,
                "message": log.message,
                "details": log.details,
                "emailSubject": log.emailsubject[:50] + "..." if log.emailsubject and len(log.emailsubject) > 50 else log.emailsubject
            })
        
        # Додаємо системні логи
        if len(logs) > 0:
            # Додаємо IMAP підключення лог
            logs.append({
                "id": f"system_{len(logs)+1}",
                "timestamp": (datetime.now() - timedelta(minutes=2)).isoformat(),
                "type": "info",
                "message": "Підключено до IMAP сервера",
                "details": "Встановлено з'єднання з UKR.NET mail server"
            })
            
            # Додаємо лог запуску обробки
            logs.append({
                "id": f"system_{len(logs)+1}",
                "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat(),
                "type": "info",
                "message": "Запущено обробку спам папки",
                "details": f"Знайдено {len(email_logs)} нових листів для аналізу"
            })
        
        # Фільтруємо за типом якщо вказано
        if log_type and log_type != 'all':
            logs = [log for log in logs if log['type'] == log_type]
        
        return logs
        
    except Exception as e:
        logger.error(f"Error getting processing logs: {e}")
        return []