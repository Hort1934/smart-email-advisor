"""
Smart Email Assistant - Інтелектуальний персональний помічник для роботи з email
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import logging
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.models.schemas import EmailAnalysisRequest, EmailAnalysisResponse
from app.services.email_service import EmailMessage

logger = logging.getLogger(__name__)

@dataclass
class SmartRecommendation:
    action_type: str  # reply, forward, archive, delete, schedule, create_task, etc.
    priority: str     # high, medium, low
    title: str        # Короткий опис дії
    description: str  # Детальний опис
    suggested_response: Optional[str] = None  # Запропонований текст відповіді
    confidence: float = 0.0
    reasoning: str = ""
    category: str = "general"  # Категорія рекомендації
    
@dataclass
class CommunicationAnalysis:
    tone: str          # professional, friendly, aggressive, neutral, urgent
    sentiment: str     # positive, negative, neutral
    emotions: List[str] # anger, frustration, enthusiasm, concern, etc.
    formality_level: str # very_formal, formal, semi_formal, informal, casual
    urgency_indicators: List[str]
    relationship_context: str # colleague, client, partner, vendor, personal
    communication_style: str # direct, diplomatic, assertive, passive

@dataclass
class PersonalContext:
    user_preferences: Dict[str, Any]
    email_patterns: Dict[str, Any]
    frequent_contacts: List[Dict[str, Any]]
    work_schedule: Dict[str, Any]
    communication_style: str
    priority_keywords: List[str]
    
class SmartEmailAssistant:
    """
    Інтелектуальний персональний помічник для email
    Аналізує листи в контексті користувача та надає контекстні рекомендації
    """
    
    def __init__(self):
        self.client = AsyncOpenAI()
        
    async def analyze_email_comprehensively(
        self, 
        email: EmailMessage, 
        user_context: PersonalContext,
        db: AsyncSession
    ) -> Tuple[EmailAnalysisResponse, List[SmartRecommendation], CommunicationAnalysis]:
        """
        Повний аналіз листа з контекстом користувача
        """
        try:
            # 1. Аналіз комунікаційного контексту
            comm_analysis = await self._analyze_communication_context(email)
            
            # 2. Персоналізований аналіз важливості
            importance_analysis = await self._analyze_personal_importance(email, user_context)
            
            # 3. Генерація розумних рекомендацій
            smart_recommendations = await self._generate_smart_recommendations(
                email, comm_analysis, user_context, importance_analysis
            )
            
            # 4. Створення базового аналізу
            basic_analysis = await self._create_basic_analysis(
                email, comm_analysis, importance_analysis
            )
            
            return basic_analysis, smart_recommendations, comm_analysis
            
        except Exception as e:
            logger.error(f"Error in comprehensive email analysis: {e}")
            raise
    
    async def _analyze_communication_context(self, email: EmailMessage) -> CommunicationAnalysis:
        """Аналіз тону, емоцій та стилю комунікації"""
        
        prompt = f"""
        Проаналізуй наступний email для визначення комунікаційного контексту:
        
        Відправник: {email.sender}
        Тема: {email.subject}
        Текст: {email.content}
        
        Визнач:
        1. Тон спілкування (professional, friendly, aggressive, neutral, urgent)
        2. Емоційний настрій (positive, negative, neutral) 
        3. Конкретні емоції (anger, frustration, enthusiasm, concern, etc.)
        4. Рівень формальності (very_formal, formal, semi_formal, informal, casual)
        5. Індикатори терміновості
        6. Контекст стосунків (colleague, client, partner, vendor, personal)
        7. Стиль комунікації (direct, diplomatic, assertive, passive)
        
        Відповідай у JSON форматі:
        {{
            "tone": "",
            "sentiment": "", 
            "emotions": [],
            "formality_level": "",
            "urgency_indicators": [],
            "relationship_context": "",
            "communication_style": ""
        }}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return CommunicationAnalysis(
                tone=result.get("tone", "neutral"),
                sentiment=result.get("sentiment", "neutral"),
                emotions=result.get("emotions", []),
                formality_level=result.get("formality_level", "formal"),
                urgency_indicators=result.get("urgency_indicators", []),
                relationship_context=result.get("relationship_context", "unknown"),
                communication_style=result.get("communication_style", "neutral")
            )
            
        except Exception as e:
            logger.error(f"Error analyzing communication context: {e}")
            return CommunicationAnalysis(
                tone="neutral", sentiment="neutral", emotions=[], 
                formality_level="formal", urgency_indicators=[],
                relationship_context="unknown", communication_style="neutral"
            )
    
    async def _analyze_personal_importance(
        self, 
        email: EmailMessage, 
        user_context: PersonalContext
    ) -> Dict[str, Any]:
        """Персоналізований аналіз важливості листа для конкретного користувача"""
        
        prompt = f"""
        Як персональний AI помічник, проаналізуй важливість цього email для користувача:
        
        EMAIL:
        Відправник: {email.sender}
        Тема: {email.subject}  
        Текст: {email.content}
        
        КОНТЕКСТ КОРИСТУВАЧА:
        Стиль комунікації: {user_context.communication_style}
        Пріоритетні ключові слова: {user_context.priority_keywords}
        Робочий графік: {user_context.work_schedule}
        
        Оціни:
        1. Практичну цінність для користувача (0-1)
        2. Необхідність негайної дії (0-1) 
        3. Потенційний вплив на роботу/життя (0-1)
        4. Релевантність інтересам користувача (0-1)
        5. Є це інформаційним шумом? (true/false)
        6. Потребує персональної уваги? (true/false)
        7. Категорія важливості: critical, high, medium, low, noise
        8. Рекомендовані дії: action_required, monitor, archive, delete
        
        Відповідай у JSON:
        {{
            "practical_value": 0.0,
            "urgency_score": 0.0, 
            "life_impact": 0.0,
            "relevance": 0.0,
            "is_noise": false,
            "needs_attention": true,
            "importance_category": "",
            "recommended_action": "",
            "reasoning": ""
        }}
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error in importance analysis: {e}")
            return {
                "practical_value": 0.5,
                "urgency_score": 0.3,
                "life_impact": 0.3, 
                "relevance": 0.5,
                "is_noise": False,
                "needs_attention": True,
                "importance_category": "medium",
                "recommended_action": "monitor",
                "reasoning": "Помилка аналізу, потребує ручної перевірки"
            }
    
    async def _generate_smart_recommendations(
        self,
        email: EmailMessage,
        comm_analysis: CommunicationAnalysis, 
        user_context: PersonalContext,
        importance_analysis: Dict[str, Any]
    ) -> List[SmartRecommendation]:
        """Генерація розумних рекомендацій на основі повного контексту"""
        
        # Спеціальна логіка для агресивного тону в діловій комунікації
        recommendations = []
        
        if (comm_analysis.tone == "aggressive" and 
            comm_analysis.relationship_context in ["colleague", "client", "partner"]):
            
            # Генеруємо дипломатичну відповідь
            diplomatic_response = await self._generate_diplomatic_response(
                email, comm_analysis, user_context
            )
            
            recommendations.append(SmartRecommendation(
                action_type="reply_diplomatic",
                priority="high", 
                title="Дипломатична відповідь на агресивний тон",
                description="Рекомендується відповісти в дипломатичному тоні для збереження ділових стосунків",
                suggested_response=diplomatic_response,
                confidence=0.9,
                reasoning="Виявлено агресивний тон у діловому листі",
                category="communication"
            ))
        
        # Загальні рекомендації на основі аналізу
        general_recs = await self._generate_general_recommendations(
            email, comm_analysis, user_context, importance_analysis
        )
        
        recommendations.extend(general_recs)
        
        return recommendations
    
    async def _generate_diplomatic_response(
        self, 
        email: EmailMessage,
        comm_analysis: CommunicationAnalysis,
        user_context: PersonalContext
    ) -> str:
        """Генерація дипломатичної відповіді на агресивний тон"""
        
        prompt = f"""
        Як експерт ділової комунікації, створи дипломатичну відповідь на агресивний email:
        
        ОТРИМАНИЙ EMAIL:
        Відправник: {email.sender}
        Тема: {email.subject}
        Текст: {email.content}
        
        АНАЛІЗ ТОНУ:
        Тон: {comm_analysis.tone}
        Емоції: {comm_analysis.emotions}
        Стиль: {comm_analysis.communication_style}
        
        СТИЛЬ КОРИСТУВАЧА: {user_context.communication_style}
        
        Створи професійну відповідь яка:
        1. Визнає проблему без конфронтації
        2. Пропонує конструктивне рішення
        3. Зберігає професійний тон
        4. Демонструє готовність до співпраці
        5. Відповідає стилю користувача
        
        Відповідай тільки текстом листа без додаткових коментарів.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating diplomatic response: {e}")
            return "Дякую за Ваш лист. Розумію Вашу позицію і готовий/а обговорити це питання. Пропоную зустрітися для вирішення ситуації."
    
    async def _generate_general_recommendations(
        self,
        email: EmailMessage, 
        comm_analysis: CommunicationAnalysis,
        user_context: PersonalContext,
        importance_analysis: Dict[str, Any]
    ) -> List[SmartRecommendation]:
        """Генерація загальних розумних рекомендацій"""
        
        prompt = f"""
        Як персональний AI помічник, створи список конкретних дій для цього email:
        
        EMAIL: {email.subject} від {email.sender}
        
        АНАЛІЗ:
        - Важливість: {importance_analysis.get('importance_category')}
        - Потребує уваги: {importance_analysis.get('needs_attention')} 
        - Тон: {comm_analysis.tone}
        - Контекст: {comm_analysis.relationship_context}
        
        Запропонуй 3-5 конкретних дій у JSON форматі:
        [
            {{
                "action_type": "reply|forward|archive|schedule|create_task|call|meeting",
                "priority": "high|medium|low", 
                "title": "Короткий опис дії",
                "description": "Детальний опис чому ця дія потрібна",
                "suggested_response": "текст відповіді якщо потрібно", 
                "confidence": 0.0-1.0,
                "reasoning": "обґрунтування рекомендації"
            }}
        ]
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            recommendations_data = json.loads(response.choices[0].message.content)
            
            return [
                SmartRecommendation(
                    action_type=rec.get("action_type", "monitor"),
                    priority=rec.get("priority", "medium"),
                    title=rec.get("title", "Перегляньте лист"),
                    description=rec.get("description", ""),
                    suggested_response=rec.get("suggested_response"),
                    confidence=rec.get("confidence", 0.5),
                    reasoning=rec.get("reasoning", ""),
                    category=rec.get("category", "general")
                ) for rec in recommendations_data
            ]
            
        except Exception as e:
            logger.error(f"Error generating general recommendations: {e}")
            return [
                SmartRecommendation(
                    action_type="monitor",
                    priority="medium", 
                    title="Перегляньте лист",
                    description="Потребує вашої уваги",
                    confidence=0.3,
                    reasoning="Помилка в аналізі рекомендацій",
                    category="general"
                )
            ]
    
    async def _create_basic_analysis(
        self,
        email: EmailMessage,
        comm_analysis: CommunicationAnalysis, 
        importance_analysis: Dict[str, Any]
    ) -> EmailAnalysisResponse:
        """Створення базового аналізу для зворотної сумісності"""
        
        from app.models.schemas import EmailPriority, EmailCategory, EmailSummary
        
        # Мапінг важливості на пріоритет
        priority_map = {
            "critical": EmailPriority.URGENT,
            "high": EmailPriority.HIGH, 
            "medium": EmailPriority.MEDIUM,
            "low": EmailPriority.LOW,
            "noise": EmailPriority.LOW
        }
        
        priority = priority_map.get(
            importance_analysis.get("importance_category", "medium"), 
            EmailPriority.MEDIUM
        )
        
        # Визначення категорії
        category = EmailCategory.WORK
        if comm_analysis.relationship_context == "personal":
            category = EmailCategory.PERSONAL
        elif "marketing" in email.subject.lower():
            category = EmailCategory.MARKETING
            
        # Створення резюме
        summary = EmailSummary(
            content=f"Лист від {email.sender} з тоном: {comm_analysis.tone}",
            key_points=[
                f"Тон комунікації: {comm_analysis.tone}",
                f"Рівень важливості: {importance_analysis.get('importance_category')}",
                f"Контекст стосунків: {comm_analysis.relationship_context}"
            ],
            action_required=importance_analysis.get("needs_attention", False),
            urgency_score=importance_analysis.get("urgency_score", 0.5),
            sentiment=comm_analysis.sentiment
        )
        
        return EmailAnalysisResponse(
            priority=priority,
            category=category,
            summary=summary,
            recommendations=[],  # Будуть заповнені окремо
            confidence=0.8,
            processing_time=1.0,
            model_version="smart-assistant-1.0"
        )

    async def learn_from_user_feedback(
        self, 
        email_id: str, 
        user_action: str, 
        feedback: Dict[str, Any],
        db: AsyncSession
    ):
        """Навчання на основі дій користувача"""
        
        # Зберігаємо зворотний зв'язок для покращення майбутніх рекомендацій
        await db.execute(
            text("""
                INSERT INTO user_feedback (email_id, action_taken, feedback_data, created_at)
                VALUES (:email_id, :action, :feedback, :created_at)
            """),
            {
                "email_id": email_id,
                "action": user_action, 
                "feedback": json.dumps(feedback),
                "created_at": datetime.utcnow()
            }
        )
        await db.commit()
        
        logger.info(f"Learning from user feedback for email {email_id}")

    async def get_user_context(self, user_id: int, db: AsyncSession) -> PersonalContext:
        """Отримання персонального контексту користувача"""
        
        # В реальному застосунку тут буде складна логіка отримання контексту
        # Поки що повертаємо базовий контекст
        return PersonalContext(
            user_preferences={
                "language": "ukrainian",
                "response_style": "professional", 
                "notification_frequency": "immediate"
            },
            email_patterns={
                "peak_hours": [9, 10, 11, 14, 15, 16],
                "avg_response_time": 2.5,
                "frequent_keywords": ["проект", "зустріч", "термін"]
            },
            frequent_contacts=[],
            work_schedule={
                "start_time": "09:00",
                "end_time": "18:00", 
                "time_zone": "Europe/Kiev"
            },
            communication_style="diplomatic",
            priority_keywords=["термін", "важливо", "терміново", "проект"]
        )