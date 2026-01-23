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
    action_type: str = Field(..., description="Тип рекомендації")
    description: str = Field(..., description="Опис рекомендації")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Впевненість")
    reasoning: str = Field(default="", description="Обґрунтування")

class EmailAnalysisResponse(BaseModel):
    priority: EmailPriority
    category: EmailCategory
    summary: EmailSummary
    recommendations: List[SmartRecommendation] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0, description="Впевненість аналізу")
    processing_time: float = Field(default=0.0, description="Час обробки в секундах")
    model_version: str = Field(default="1.0.0", description="Версія моделі")

class RecommendationRequest(BaseModel):
    email_content: str
    user_context: Dict[str, Any] = Field(default_factory=dict)
    previous_emails: List[str] = Field(default_factory=list)
    reasoning: str = Field(default="", description="Обґрунтування")
    type: str = Field(..., description="Тип рекомендації (reply, action, schedule)")
    content: str = Field(..., description="Зміст рекомендації")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., description="Пояснення рекомендації")