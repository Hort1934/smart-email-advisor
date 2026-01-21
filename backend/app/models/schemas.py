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

class EmailAnalysisResponse(BaseModel):
    priority: EmailPriority
    category: EmailCategory
    sentiment: str = Field(..., description="Тональність листа (positive, negative, neutral)")
    key_points: List[str] = Field(..., description="Ключові пункти з листа")
    suggested_actions: List[str] = Field(..., description="Рекомендовані дії")
    urgency_score: float = Field(..., ge=0.0, le=1.0, description="Оцінка терміновості (0-1)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Впевненість аналізу")

class EmailSummary(BaseModel):
    summary: str = Field(..., description="Короткий резюме листа")
    main_topic: str = Field(..., description="Основна тема")
    actionable_items: List[str] = Field(default_factory=list)
    deadline_mentioned: Optional[datetime] = None

class UserProfile(BaseModel):
    user_id: str
    email: EmailStr
    preferences: Dict[str, Any] = Field(default_factory=dict)
    email_patterns: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RecommendationRequest(BaseModel):
    email_content: str
    user_context: Dict[str, Any] = Field(default_factory=dict)
    previous_emails: List[str] = Field(default_factory=list)

class SmartRecommendation(BaseModel):
    type: str = Field(..., description="Тип рекомендації (reply, action, schedule)")
    content: str = Field(..., description="Зміст рекомендації")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(..., description="Пояснення рекомендації")