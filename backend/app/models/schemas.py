from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class EmailPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class EmailCategory(str, Enum):
    WORK = "work"
    PERSONAL = "personal"
    MARKETING = "marketing"
    NOTIFICATION = "notification"
    SPAM = "spam"

class EmailAnalysisRequest(BaseModel):
    subject: str = Field(..., description="Тема листа")
    content: str = Field(..., description="Зміст листа")
    sender: EmailStr = Field(..., description="Відправник")
    recipient: EmailStr = Field(..., description="Отримувач")
    received_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

class EmailSummary(BaseModel):
    content: str = Field(..., description="Короткий резюме листа")
    key_points: List[str] = Field(default_factory=list, description="Ключові пункти")
    action_required: bool = Field(default=False, description="Потрібні дії")
    urgency_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Оцінка терміновості (0-1)")
    sentiment: str = Field(default="neutral", description="Тональність")

class SmartRecommendation(BaseModel):
    action_type: str = Field(..., description="Тип дії (reply, forward, archive, etc.)")
    priority: str = Field(..., description="Пріоритет дії (high, medium, low)")
    title: str = Field(..., description="Назва рекомендації")
    description: str = Field(..., description="Опис рекомендації")
    suggested_response: Optional[str] = Field(None, description="Запропонований текст відповіді")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Впевненість")
    reasoning: str = Field(default="", description="Обґрунтування рекомендації")
    category: str = Field(default="general", description="Категорія рекомендації")
    
class CommunicationAnalysis(BaseModel):
    tone: str = Field(..., description="Тон комунікації")
    sentiment: str = Field(..., description="Емоційне забарвлення")
    emotions: List[str] = Field(default_factory=list, description="Виявлені емоції")
    formality_level: str = Field(..., description="Рівень формальності")
    urgency_indicators: List[str] = Field(default_factory=list, description="Індикатори терміновості")
    relationship_context: str = Field(..., description="Контекст стосунків")
    communication_style: str = Field(..., description="Стиль комунікації")
    
class PersonalizedAnalysis(BaseModel):
    practical_value: float = Field(..., ge=0.0, le=1.0, description="Практична цінність")
    urgency_score: float = Field(..., ge=0.0, le=1.0, description="Оцінка терміновості")
    life_impact: float = Field(..., ge=0.0, le=1.0, description="Вплив на життя/роботу")
    relevance: float = Field(..., ge=0.0, le=1.0, description="Релевантність")
    is_noise: bool = Field(..., description="Чи є інформаційним шумом")
    needs_attention: bool = Field(..., description="Потребує персональної уваги")
    importance_category: str = Field(..., description="Категорія важливості")
    recommended_action: str = Field(..., description="Рекомендована дія")
    reasoning: str = Field(..., description="Обґрунтування аналізу")
    
class UserFeedback(BaseModel):
    email_id: str = Field(..., description="ID листа")
    action_taken: str = Field(..., description="Дія користувача")
    satisfaction: int = Field(..., ge=1, le=5, description="Оцінка задоволеності (1-5)")
    feedback_text: Optional[str] = Field(None, description="Текстовий коментар")
    recommendation_helpful: bool = Field(..., description="Чи були корисні рекомендації")

class EmailAnalysisResponse(BaseModel):
    priority: EmailPriority
    category: EmailCategory
    summary: EmailSummary
    recommendations: List[SmartRecommendation] = Field(default_factory=list)
    communication_analysis: Optional[CommunicationAnalysis] = Field(None, description="Аналіз комунікації")
    personalized_analysis: Optional[PersonalizedAnalysis] = Field(None, description="Персоналізований аналіз")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Впевненість аналізу")
    processing_time: float = Field(default=0.0, description="Час обробки в секундах")
    model_version: str = Field(default="1.0.0", description="Версія моделі")

class RecommendationRequest(BaseModel):
    email_content: str
    user_context: Dict[str, Any] = Field(default_factory=dict)
    previous_emails: List[str] = Field(default_factory=list)