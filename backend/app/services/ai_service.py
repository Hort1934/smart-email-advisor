import openai
import os
import json
import asyncio
import aiohttp
from typing import List, Dict, Any
from datetime import datetime, timedelta
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import logging

from app.models.schemas import (
    EmailAnalysisRequest, 
    EmailAnalysisResponse, 
    EmailPriority, 
    EmailCategory,
    EmailSummary,
    SmartRecommendation
)
from app.services.ai_service_helpers import _convert_ai_result_to_response, _fallback_analysis

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.ai_agent_url = os.getenv("AI_AGENT_URL", "http://ai-agent:8001")
    
    async def analyze_email(self, request: EmailAnalysisRequest) -> EmailAnalysisResponse:
        """Аналіз електронного листа з використанням AI Agent або OpenAI"""
        
        try:
            # Спробувати використати AI Agent сервіс
            email_data = {
                "id": str(request.id) if hasattr(request, 'id') else None,
                "subject": request.subject,
                "content": request.content,
                "sender": request.sender,
                "recipient": request.recipient,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if self.ai_agent_url:
                result = await self._analyze_with_ai_agent(email_data)
                if result:
                    return _convert_ai_result_to_response(result, request)
            
            # Fallback до прямого виклику OpenAI
            return await self._analyze_with_openai_direct(request)
            
        except Exception as e:
            logger.error(f"Email analysis failed: {e}")
            return _fallback_analysis(request)
    
    async def _analyze_with_ai_agent(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Аналіз через AI Agent сервіс"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ai_agent_url}/analyze",
                    json=email_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"AI Agent analysis completed for email {email_data.get('id')}")
                        return result
                    else:
                        logger.error(f"AI Agent returned status {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"AI Agent analysis failed: {e}")
            return None
    
    async def _analyze_with_openai_direct(self, request: EmailAnalysisRequest) -> EmailAnalysisResponse:
        
        # Підготовка промпту для аналізу
        analysis_prompt = f"""
        Проаналізуй наступний електронний лист та надай детальну оцінку:

        Тема: {request.subject}
        Відправник: {request.sender}
        Отримувач: {request.recipient}
        Зміст:
        {request.content}

        Виконай наступний аналіз:
        1. Визначи пріоритет (low, medium, high, urgent)
        2. Категорізуй лист (work, personal, marketing, notification, spam)
        3. Оціни тональність (positive, negative, neutral)
        4. Виділи ключові пункти (до 5 найважливіших)
        5. Запропонуй дії (до 3 конкретних рекомендацій)
        6. Оціни терміновість (0.0-1.0)
        7. Оціни впевненість аналізу (0.0-1.0)

        Надай відповідь у форматі JSON:
        {{
            "priority": "medium",
            "category": "work",
            "sentiment": "neutral",
            "key_points": ["пункт1", "пункт2"],
            "suggested_actions": ["дія1", "дія2"],
            "urgency_score": 0.5,
            "confidence_score": 0.8
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Ти - експерт з аналізу електронних листів. Відповідай лише у форматі JSON."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Парсинг JSON відповіді
            analysis_result = json.loads(response.choices[0].message.content)
            
            return EmailAnalysisResponse(
                priority=EmailPriority(analysis_result["priority"]),
                category=EmailCategory(analysis_result["category"]),
                sentiment=analysis_result["sentiment"],
                key_points=analysis_result["key_points"],
                suggested_actions=analysis_result["suggested_actions"],
                urgency_score=analysis_result["urgency_score"],
                confidence_score=analysis_result["confidence_score"]
            )
            
        except Exception as e:
            # Fallback аналіз у випадку помилки
            return await self._fallback_analysis(request)
    
    async def generate_summary(self, email_content: str) -> EmailSummary:
        """Генерація короткого резюме листа"""
        
        summary_prompt = f"""
        Створи короткий резюме наступного листа:

        {email_content}

        Надай:
        1. Коротке резюме (1-2 речення)
        2. Основну тему
        3. Дії, які потрібно виконати (якщо є)
        4. Згадані дедлайни (якщо є)

        Формат JSON:
        {{
            "summary": "Короткий опис...",
            "main_topic": "Основна тема",
            "actionable_items": ["дія1", "дія2"],
            "deadline_mentioned": "2024-01-25T10:00:00" або null
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Ти створюєш короткі та точні резюме листів. Відповідай у форматі JSON."},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )
            
            summary_result = json.loads(response.choices[0].message.content)
            
            return EmailSummary(
                summary=summary_result["summary"],
                main_topic=summary_result["main_topic"],
                actionable_items=summary_result.get("actionable_items", []),
                deadline_mentioned=datetime.fromisoformat(summary_result["deadline_mentioned"]) 
                    if summary_result.get("deadline_mentioned") else None
            )
            
        except Exception as e:
            # Fallback резюме
            return EmailSummary(
                summary="Не вдалося створити автоматичне резюме",
                main_topic="Невизначено",
                actionable_items=[],
                deadline_mentioned=None
            )
    
    async def generate_smart_recommendations(self, email_content: str, user_context: Dict[str, Any] = None) -> List[SmartRecommendation]:
        """Генерація розумних рекомендацій на основі контексту"""
        
        context_info = ""
        if user_context:
            context_info = f"Контекст користувача: {json.dumps(user_context, indent=2)}"
        
        recommendations_prompt = f"""
        Надай розумні рекомендації для наступного листа:

        {email_content}

        {context_info}

        Створи до 3 різних типів рекомендацій:
        1. reply - рекомендація щодо відповіді
        2. action - рекомендована дія
        3. schedule - рекомендація щодо планування

        Формат JSON:
        [
            {{
                "type": "reply",
                "content": "Рекомендований текст відповіді або підхід",
                "confidence": 0.8,
                "reasoning": "Пояснення чому ця рекомендація"
            }}
        ]
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Ти - помічник з ефективної роботи з поштою. Створюй корисні та практичні рекомендації."},
                    {"role": "user", "content": recommendations_prompt}
                ],
                temperature=0.4,
                max_tokens=1000
            )
            
            recommendations_result = json.loads(response.choices[0].message.content)
            
            return [
                SmartRecommendation(
                    type=rec["type"],
                    content=rec["content"],
                    confidence=rec["confidence"],
                    reasoning=rec["reasoning"]
                )
                for rec in recommendations_result
            ]
            
        except Exception as e:
            # Fallback рекомендації
            return [
                SmartRecommendation(
                    type="action",
                    content="Прочитайте лист уважно та визначте необхідні дії",
                    confidence=0.5,
                    reasoning="Автоматичний аналіз недоступний"
                )
            ]
    
    async def _fallback_analysis(self, request: EmailAnalysisRequest) -> EmailAnalysisResponse:
        """Запасний аналіз без AI"""
        
        # Простий алгоритм для визначення пріоритету
        urgency_keywords = ["urgent", "asap", "immediately", "терміново", "негайно"]
        high_keywords = ["important", "critical", "deadline", "важливо", "критично"]
        
        content_lower = request.content.lower()
        subject_lower = request.subject.lower()
        
        urgency_score = 0.3  # базовий рівень
        
        if any(keyword in content_lower or keyword in subject_lower for keyword in urgency_keywords):
            priority = EmailPriority.URGENT
            urgency_score = 0.9
        elif any(keyword in content_lower or keyword in subject_lower for keyword in high_keywords):
            priority = EmailPriority.HIGH
            urgency_score = 0.7
        else:
            priority = EmailPriority.MEDIUM
            urgency_score = 0.4
        
        # Проста категоризація
        if "noreply" in request.sender or "notification" in request.sender:
            category = EmailCategory.NOTIFICATION
        elif any(word in content_lower for word in ["meeting", "project", "work", "office"]):
            category = EmailCategory.WORK
        else:
            category = EmailCategory.PERSONAL
        
        return EmailAnalysisResponse(
            priority=priority,
            category=category,
            sentiment="neutral",
            key_points=["Автоматичний аналіз недоступний"],
            suggested_actions=["Прочитайте лист та визначте необхідні дії"],
            urgency_score=urgency_score,
            confidence_score=0.6
        )