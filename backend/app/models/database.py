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
    
    # Relationships
    email_analyses = relationship("EmailAnalysis", back_populates="user")
    user_preferences = relationship("UserPreference", back_populates="user")
    context = relationship("UserContext", back_populates="user", uselist=False)
    contact_analyses = relationship("ContactAnalysis", back_populates="user")

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
    
    # Smart assistant features  
    communication_tone = Column(String, nullable=True)
    emotions = Column(JSON, nullable=True)
    relationship_context = Column(String, nullable=True)
    practical_value = Column(Float, default=0.5)
    life_impact = Column(Float, default=0.5)
    is_noise = Column(Boolean, default=False)
    needs_attention = Column(Boolean, default=True)
    is_archived = Column(Boolean, default=False)
    
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
    
    # Relationships
    user = relationship("User", back_populates="email_analyses")
    email_recommendations = relationship("EmailRecommendation", back_populates="email_analysis")
    feedback_entries = relationship("UserFeedback", back_populates="email_analysis")

class EmailRecommendation(Base):
    __tablename__ = "email_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    email_analysis_id = Column(Integer, ForeignKey("email_analyses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Recommendation details
    action_type = Column(String, nullable=False)  # reply, forward, archive, etc.
    priority = Column(String, nullable=False)     # high, medium, low
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    suggested_response = Column(Text, nullable=True)
    confidence = Column(Float, default=0.5)
    reasoning = Column(Text, nullable=True)
    category = Column(String, default="general")
    
    # Tracking
    is_executed = Column(Boolean, default=False)
    executed_at = Column(DateTime, nullable=True)
    user_rating = Column(Integer, nullable=True)  # 1-5 rating
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    email_analysis = relationship("EmailAnalysis", back_populates="email_recommendations")
    user = relationship("User")

class UserFeedback(Base):
    __tablename__ = "user_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    email_analysis_id = Column(Integer, ForeignKey("email_analyses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Feedback details
    action_taken = Column(String, nullable=False)
    satisfaction = Column(Integer, nullable=False)  # 1-5 scale
    feedback_text = Column(Text, nullable=True)
    recommendation_helpful = Column(Boolean, nullable=False)
    improvement_suggestions = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    email_analysis = relationship("EmailAnalysis", back_populates="feedback_entries")
    user = relationship("User")

class UserContext(Base):
    __tablename__ = "user_contexts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Personal preferences
    communication_style = Column(String, default="professional")  # diplomatic, direct, friendly
    language_preference = Column(String, default="ukrainian")
    response_style = Column(String, default="balanced")  # formal, casual, balanced
    
    # Work patterns
    work_hours_start = Column(String, default="09:00")
    work_hours_end = Column(String, default="18:00")
    timezone = Column(String, default="Europe/Kiev")
    peak_productivity_hours = Column(JSON)  # [9, 10, 14, 15]
    
    # Email patterns learned from behavior
    average_response_time = Column(Float, default=2.5)  # hours
    priority_keywords = Column(JSON)  # ["термін", "важливо", "терміново"]
    frequent_contacts = Column(JSON)  # Contact analysis data
    email_categories_preference = Column(JSON)  # Preferred handling for categories
    
    # AI learning data
    ai_accuracy_feedback = Column(JSON)  # Historical accuracy data
    preferred_recommendation_types = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="context")

class ContactAnalysis(Base):
    __tablename__ = "contact_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Contact details
    email_address = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True)
    
    # Relationship analysis
    relationship_type = Column(String, nullable=True)  # colleague, client, friend, etc.
    interaction_frequency = Column(Integer, default=0)
    last_interaction = Column(DateTime, nullable=True)
    
    # Communication patterns
    typical_response_time = Column(Float, nullable=True)  # hours
    communication_style = Column(String, nullable=True)
    typical_topics = Column(JSON)  # Analyzed topics
    importance_score = Column(Float, default=0.5)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="contact_analyses")

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