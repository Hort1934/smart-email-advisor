import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from app.models.database import EmailAnalysis
from app.models.schemas import EmailAnalysisRequest, EmailAnalysisResponse
from app.services.email_service import EmailMessage

logger = logging.getLogger(__name__)

class EmailStorageService:
    """Сервіс для роботи з email'ами в базі даних"""
    
    @staticmethod
    async def save_email_analysis(
        db: AsyncSession,
        email_msg: EmailMessage,
        analysis_result: EmailAnalysisResponse,
        user_id: Optional[int] = None
    ) -> EmailAnalysis:
        """Збереження результатів аналізу email'а в БД"""
        try:
            # Перевірка чи email вже існує
            existing = await EmailStorageService.get_email_by_uid(db, email_msg.uid)
            if existing:
                logger.info(f"Email with UID {email_msg.uid} already exists, updating analysis")
                return await EmailStorageService.update_email_analysis(
                    db, existing, analysis_result
                )
            
            # Підготовка рекомендацій для JSON
            recommendations_json = []
            if analysis_result.recommendations:
                for rec in analysis_result.recommendations:
                    recommendations_json.append({
                        "action_type": rec.action_type,
                        "description": rec.description,
                        "confidence": rec.confidence,
                        "reasoning": getattr(rec, 'reasoning', '')
                    })
            
            # Підготовка ключових пунктів
            key_points_json = []
            if analysis_result.summary and analysis_result.summary.key_points:
                key_points_json = analysis_result.summary.key_points
            
            # Підготовка інформації про вкладення
            attachments_json = []
            if email_msg.attachments:
                attachments_json = email_msg.attachments
            
            # Створення запису в БД
            db_email = EmailAnalysis(
                user_id=user_id,
                email_uid=email_msg.uid,
                message_id=email_msg.message_id,
                subject=email_msg.subject[:500] if email_msg.subject else "",  # Обмеження довжини
                content=email_msg.content[:5000] if email_msg.content else "",  # Обмеження до 5000 символів
                html_content=email_msg.html_content[:10000] if email_msg.html_content else "",  # Обмеження до 10000 символів
                sender=email_msg.sender[:255] if email_msg.sender else "",  # Обмеження довжини
                recipient=email_msg.recipient[:255] if email_msg.recipient else "",  # Обмеження довжини
                folder=email_msg.folder,
                received_at=email_msg.received_at.replace(tzinfo=None) if email_msg.received_at.tzinfo else email_msg.received_at,
                is_read=email_msg.is_read,
                
                # AI Analysis results
                priority=analysis_result.priority.value if hasattr(analysis_result.priority, 'value') else str(analysis_result.priority),
                category=analysis_result.category.value if hasattr(analysis_result.category, 'value') else str(analysis_result.category),
                sentiment=analysis_result.summary.sentiment if analysis_result.summary else "neutral",
                urgency_score=analysis_result.summary.urgency_score if analysis_result.summary else 0.5,
                confidence_score=analysis_result.confidence,
                
                # Analysis metadata
                processing_time=analysis_result.processing_time,
                model_version=analysis_result.model_version,
                analyzed_at=datetime.utcnow(),
                
                # JSON fields
                key_points=key_points_json,
                recommendations=recommendations_json,
                attachments_info=attachments_json,
                
                # Legacy fields
                ai_summary=analysis_result.summary.content if analysis_result.summary else "",
                suggested_actions=[]  # Можна заповнити пізніше якщо потрібно
            )
            
            db.add(db_email)
            await db.commit()
            await db.refresh(db_email)
            
            logger.info(f"Email analysis saved for UID: {email_msg.uid}")
            return db_email
            
        except IntegrityError as e:
            await db.rollback()
            logger.warning(f"Email with UID {email_msg.uid} might already exist: {e}")
            # Спробуємо отримати існуючий запис
            existing = await EmailStorageService.get_email_by_uid(db, email_msg.uid)
            if existing:
                return existing
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error saving email analysis: {e}")
            raise
    
    @staticmethod
    async def get_email_by_uid(db: AsyncSession, uid: str) -> Optional[EmailAnalysis]:
        """Отримання email'а за UID"""
        try:
            result = await db.execute(
                select(EmailAnalysis).where(EmailAnalysis.email_uid == uid)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting email by UID {uid}: {e}")
            return None
    
    @staticmethod
    async def update_email_analysis(
        db: AsyncSession,
        db_email: EmailAnalysis,
        analysis_result: EmailAnalysisResponse
    ) -> EmailAnalysis:
        """Оновлення аналізу існуючого email'а"""
        try:
            # Оновлення полів аналізу
            db_email.priority = analysis_result.priority.value if hasattr(analysis_result.priority, 'value') else str(analysis_result.priority)
            db_email.category = analysis_result.category.value if hasattr(analysis_result.category, 'value') else str(analysis_result.category)
            db_email.sentiment = analysis_result.summary.sentiment if analysis_result.summary else "neutral"
            db_email.urgency_score = analysis_result.summary.urgency_score if analysis_result.summary else 0.5
            db_email.confidence_score = analysis_result.confidence
            db_email.processing_time = analysis_result.processing_time
            db_email.model_version = analysis_result.model_version
            db_email.analyzed_at = datetime.utcnow()
            
            # Оновлення JSON полів
            if analysis_result.summary and analysis_result.summary.key_points:
                db_email.key_points = analysis_result.summary.key_points
            
            if analysis_result.recommendations:
                recommendations_json = []
                for rec in analysis_result.recommendations:
                    recommendations_json.append({
                        "action_type": rec.action_type,
                        "description": rec.description,
                        "confidence": rec.confidence,
                        "reasoning": getattr(rec, 'reasoning', '')
                    })
                db_email.recommendations = recommendations_json
            
            await db.commit()
            await db.refresh(db_email)
            
            logger.info(f"Email analysis updated for UID: {db_email.email_uid}")
            return db_email
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating email analysis: {e}")
            raise
    
    @staticmethod
    async def get_user_emails(
        db: AsyncSession,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[EmailAnalysis]:
        """Отримання email'ів користувача з пагінацією"""
        try:
            result = await db.execute(
                select(EmailAnalysis)
                .where(EmailAnalysis.user_id == user_id)
                .order_by(EmailAnalysis.received_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting user emails: {e}")
            return []
    
    @staticmethod
    async def get_spam_emails_count(db: AsyncSession) -> int:
        """Отримання кількості spam email'ів"""
        try:
            result = await db.execute(
                select(EmailAnalysis).where(
                    (EmailAnalysis.folder == 'Spam') | 
                    (EmailAnalysis.category == 'spam')
                )
            )
            emails = result.scalars().all()
            return len(emails)
        except Exception as e:
            logger.error(f"Error counting spam emails: {e}")
            return 0
    
    @staticmethod
    async def get_email_stats(db: AsyncSession) -> Dict[str, Any]:
        """Отримання статистики email'ів"""
        try:
            # Загальна кількість
            result = await db.execute(select(EmailAnalysis))
            all_emails = result.scalars().all()
            total_count = len(all_emails)
            
            # Статистика по категоріях
            categories = {}
            priorities = {}
            folders = {}
            
            for email in all_emails:
                # Категорії
                cat = email.category or 'unknown'
                categories[cat] = categories.get(cat, 0) + 1
                
                # Пріоритети
                prior = email.priority or 'unknown'
                priorities[prior] = priorities.get(prior, 0) + 1
                
                # Папки
                folder = email.folder or 'unknown'
                folders[folder] = folders.get(folder, 0) + 1
            
            return {
                "total_emails": total_count,
                "categories": categories,
                "priorities": priorities,
                "folders": folders,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting email stats: {e}")
            return {
                "total_emails": 0,
                "categories": {},
                "priorities": {},
                "folders": {},
                "error": str(e)
            }
    
    @staticmethod
    async def search_emails(
        db: AsyncSession,
        user_id: Optional[int] = None,
        query: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 50
    ) -> List[EmailAnalysis]:
        """Пошук email'ів за критеріями"""
        try:
            sql_query = select(EmailAnalysis)
            
            # Фільтри
            if user_id:
                sql_query = sql_query.where(EmailAnalysis.user_id == user_id)
            
            if query:
                sql_query = sql_query.where(
                    (EmailAnalysis.subject.ilike(f'%{query}%')) |
                    (EmailAnalysis.content.ilike(f'%{query}%')) |
                    (EmailAnalysis.sender.ilike(f'%{query}%'))
                )
            
            if category:
                sql_query = sql_query.where(EmailAnalysis.category == category)
            
            if priority:
                sql_query = sql_query.where(EmailAnalysis.priority == priority)
            
            sql_query = sql_query.order_by(EmailAnalysis.received_at.desc()).limit(limit)
            
            result = await db.execute(sql_query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error searching emails: {e}")
            return []