from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to email analyses
    email_analyses = relationship("EmailAnalysis", back_populates="user")
    user_preferences = relationship("UserPreference", back_populates="user")

class EmailAnalysis(Base):
    __tablename__ = "email_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Email identification
    email_uid = Column(String, nullable=False, index=True)
    message_id = Column(String, nullable=True)
    
    # Email content
    subject = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    html_content = Column(Text, nullable=True)
    sender = Column(String, nullable=False)
    recipient = Column(String, nullable=False)
    folder = Column(String, nullable=True)
    received_at = Column(DateTime, nullable=False)
    is_read = Column(Boolean, nullable=True)
    
    # AI Analysis results
    priority = Column(String, nullable=False)  # low, medium, high, urgent
    category = Column(String, nullable=False)  # work, personal, marketing, etc.
    sentiment = Column(String, nullable=False)  # positive, negative, neutral
    urgency_score = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    
    # Analysis metadata
    processing_time = Column(Float, nullable=True)
    model_version = Column(String, nullable=True)
    analyzed_at = Column(DateTime, nullable=True)
    
    # JSON fields for complex data
    key_points = Column(JSON)
    recommendations = Column(JSON)
    attachments_info = Column(JSON)
    
    # Legacy fields
    suggested_actions = Column(JSON)
    ai_summary = Column(Text)
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to user
    user = relationship("User", back_populates="email_analyses")

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    preference_key = Column(String, nullable=False)  # e.g., "priority_weights", "categories"
    preference_value = Column(JSON, nullable=False)  # Store as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to user
    user = relationship("User", back_populates="user_preferences")

class EmailTemplate(Base):
    __tablename__ = "email_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    template_name = Column(String, nullable=False)
    template_subject = Column(String)
    template_content = Column(Text, nullable=False)
    category = Column(String)  # work, personal, etc.
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)