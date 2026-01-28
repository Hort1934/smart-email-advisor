import asyncio
import os
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Smart Email Advisor - AI Agent",
    description="AI Agent для обробки та аналізу електронних листів",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
redis_client = None
db_engine = None
bedrock_client = None
s3_client = None
llm_rules = {}

class AIAgent:
    def __init__(self):
        self.redis_client = None
        self.db_session = None
        self.bedrock_client = None
        self.s3_client = None
        self.rules = {}
        
    async def initialize(self):
        """Initialize all services"""
        await self.init_redis()
        await self.init_database()
        await self.init_aws_services()
        await self.load_llm_rules()
        
    async def init_redis(self):
        """Initialize Redis connection"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
            self.redis_client = redis.from_url(redis_url)
            await self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise
            
    async def init_database(self):
        """Initialize database connection"""
        try:
            database_url = os.getenv("DATABASE_URL")
            if database_url:
                # Convert postgresql:// to postgresql+asyncpg:// for async operations
                if database_url.startswith("postgresql://"):
                    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
                elif database_url.startswith("postgres://"):
                    database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
                
                self.db_engine = create_async_engine(database_url)
                AsyncSessionLocal = sessionmaker(
                    self.db_engine, class_=AsyncSession, expire_on_commit=False
                )
                logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            # Don't raise - database is optional for AI Agent
            
    async def init_aws_services(self):
        """Initialize AWS services"""
        try:
            aws_region = os.getenv("AWS_REGION", "us-east-1")
            
            # Initialize Bedrock client (no endpoint env needed for boto3)
            # We enable it when a model id is provided.
            if os.getenv("AWS_BEDROCK_MODEL_ID"):
                self.bedrock_client = boto3.client("bedrock-runtime", region_name=aws_region)
                logger.info("AWS Bedrock client initialized")
                
            # Initialize S3 client
            if os.getenv("AWS_S3_BUCKET"):
                self.s3_client = boto3.client(
                    's3',
                    region_name=aws_region
                )
                logger.info("AWS S3 client initialized")
                
        except Exception as e:
            logger.error(f"AWS services initialization failed: {e}")
            
    async def load_llm_rules(self):
        """Load LLM rules from configuration file"""
        try:
            rules_path = os.getenv("LLM_RULES_PATH", "/app/config/llm_rules.json")
            if os.path.exists(rules_path):
                with open(rules_path, 'r', encoding='utf-8') as f:
                    self.rules = json.load(f)
                logger.info(f"LLM rules loaded from {rules_path}")
            else:
                logger.warning(f"LLM rules file not found: {rules_path}")
        except Exception as e:
            logger.error(f"Failed to load LLM rules: {e}")
            
    async def analyze_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main email analysis function"""
        try:
            # If configured, use Bedrock Claude for analysis
            if self.bedrock_client and os.getenv("AWS_BEDROCK_MODEL_ID"):
                bedrock_result = await self._analyze_with_bedrock(email_data)
                if bedrock_result:
                    await self.store_analysis(bedrock_result)
                    return bedrock_result

            # Extract email components
            subject = email_data.get("subject", "")
            content = email_data.get("content", "")
            sender = email_data.get("sender", "")
            
            # Perform analysis
            priority = await self.determine_priority(subject, content, sender)
            category = await self.determine_category(subject, content, sender)
            sentiment = await self.analyze_sentiment(content)
            
            # Get recommendations
            recommendations = await self.generate_recommendations(
                email_data, priority, category, sentiment
            )
            
            # Store analysis results
            analysis_result = {
                "email_id": email_data.get("id"),
                "priority": priority,
                "category": category,
                "sentiment": sentiment,
                "recommendations": recommendations,
                "confidence_score": 0.85,  # Calculate based on rules matching
                "processed_at": datetime.utcnow().isoformat(),
                "agent_version": "1.0.0"
            }
            
            await self.store_analysis(analysis_result)
            return analysis_result
            
        except Exception as e:
            logger.error(f"Email analysis failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def _analyze_with_bedrock(self, email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze email using AWS Bedrock (Claude) and return ai-agent result format."""
        model_id = os.getenv("AWS_BEDROCK_MODEL_ID")
        if not model_id:
            return None

        subject = email_data.get("subject", "")
        content = email_data.get("content", "")
        sender = email_data.get("sender", "")
        recipient = email_data.get("recipient", "")

        prompt = (
            "You are an email triage assistant. Analyze the email and respond with ONLY valid JSON.\n"
            "Return fields:\n"
            "- priority: one of [low, medium, high, urgent]\n"
            "- category: one of [work, personal, marketing, notification, spam]\n"
            "- sentiment: one of [positive, negative, neutral]\n"
            "- recommendations: array of {type, content, confidence, reasoning}\n"
            "- confidence_score: number 0..1\n"
            "Email:\n"
            f"From: {sender}\n"
            f"To: {recipient}\n"
            f"Subject: {subject}\n"
            f"Content:\n{content}\n"
        )

        temperature = float(os.getenv("AI_TEMPERATURE", "0.3"))
        max_tokens = int(os.getenv("AWS_BEDROCK_MAX_TOKENS", "800"))

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}],
                }
            ],
        }

        try:
            resp = self.bedrock_client.invoke_model(
                modelId=model_id,
                body=json.dumps(body).encode("utf-8"),
                accept="application/json",
                contentType="application/json",
            )
            raw = resp["body"].read()
            payload = json.loads(raw)
            # Claude returns content blocks
            text_blocks = payload.get("content", [])
            text = ""
            for block in text_blocks:
                if block.get("type") == "text":
                    text += block.get("text", "")

            # Extract JSON from the response text
            text = text.strip()
            if not text:
                return None
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return None
            parsed = json.loads(text[start : end + 1])

            result = {
                "email_id": email_data.get("id"),
                "priority": parsed.get("priority", "medium"),
                "category": parsed.get("category", "personal"),
                "sentiment": parsed.get("sentiment", "neutral"),
                "recommendations": parsed.get("recommendations", []),
                "confidence_score": float(parsed.get("confidence_score", 0.6)),
                "processed_at": datetime.utcnow().isoformat(),
                "agent_version": f"bedrock:{model_id}",
            }
            return result
        except (BotoCoreError, ClientError, KeyError, ValueError, json.JSONDecodeError) as e:
            logger.error(f"Bedrock analysis failed: {e}")
            return None
            
    async def determine_priority(self, subject: str, content: str, sender: str) -> str:
        """Determine email priority based on rules"""
        text_to_analyze = f"{subject} {content}".lower()
        
        priority_rules = self.rules.get("priority_rules", {})
        scores = {}
        
        for priority, rules in priority_rules.items():
            score = 0.0
            
            # Check keywords
            keywords = rules.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in text_to_analyze:
                    score += 0.3
                    
            # Check sender patterns
            sender_patterns = rules.get("sender_patterns", [])
            for pattern in sender_patterns:
                if pattern.lower() in sender.lower():
                    score += 0.4
                    
            # Check subject patterns
            subject_patterns = rules.get("subject_patterns", [])
            for pattern in subject_patterns:
                if pattern.lower() in subject.lower():
                    score += 0.3
                    
            scores[priority] = min(score, 1.0)
            
        # Return priority with highest score
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return "medium"
        
    async def determine_category(self, subject: str, content: str, sender: str) -> str:
        """Determine email category based on rules"""
        text_to_analyze = f"{subject} {content}".lower()
        
        category_rules = self.rules.get("category_rules", {})
        scores = {}
        
        for category, rules in category_rules.items():
            score = 0.0
            
            # Check keywords
            keywords = rules.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in text_to_analyze:
                    score += 0.2
                    
            # Check sender domains
            sender_domains = rules.get("sender_domains", [])
            for domain in sender_domains:
                if domain.lower() in sender.lower():
                    score += 0.3
                    
            scores[category] = min(score, 1.0)
            
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return "personal"
        
    async def analyze_sentiment(self, content: str) -> str:
        """Analyze email sentiment"""
        content_lower = content.lower()
        sentiment_rules = self.rules.get("sentiment_analysis", {})
        
        positive_keywords = sentiment_rules.get("positive", {}).get("keywords", [])
        negative_keywords = sentiment_rules.get("negative", {}).get("keywords", [])
        
        positive_score = sum(1 for keyword in positive_keywords if keyword in content_lower)
        negative_score = sum(1 for keyword in negative_keywords if keyword in content_lower)
        
        if positive_score > negative_score:
            return "positive"
        elif negative_score > positive_score:
            return "negative"
        else:
            return "neutral"
            
    async def generate_recommendations(self, email_data: Dict, priority: str, category: str, sentiment: str) -> List[Dict]:
        """Generate smart recommendations"""
        recommendations = []
        
        response_rules = self.rules.get("response_recommendations", {})
        
        # Priority-based recommendations
        if priority == "urgent":
            recommendations.append({
                "type": "action",
                "content": "Потребує негайної відповіді протягом години",
                "confidence": 0.9,
                "reasoning": "Високий пріоритет потребує швидкої реакції"
            })
            
        # Category-based recommendations
        if category == "work":
            recommendations.append({
                "type": "schedule",
                "content": "Додати до робочих задач та встановити нагадування",
                "confidence": 0.8,
                "reasoning": "Робочий лист потребує планування"
            })
            
        return recommendations
        
    async def store_analysis(self, analysis_result: Dict[str, Any]):
        """Store analysis results in Redis and optionally database"""
        try:
            # Store in Redis for quick access
            email_id = analysis_result.get("email_id")
            if email_id and self.redis_client:
                await self.redis_client.setex(
                    f"email_analysis:{email_id}",
                    3600,  # 1 hour expiry
                    json.dumps(analysis_result)
                )
                
            # TODO: Store in database for long-term analysis
            
        except Exception as e:
            logger.error(f"Failed to store analysis: {e}")

# Initialize AI Agent
ai_agent = AIAgent()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        await ai_agent.initialize()
        logger.info("AI Agent initialized successfully")
    except Exception as e:
        logger.error(f"AI Agent initialization failed: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "AI Agent is running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/analyze")
async def analyze_email(email_data: Dict[str, Any], background_tasks: BackgroundTasks):
    """Analyze email and return results"""
    try:
        result = await ai_agent.analyze_email(email_data)
        return result
    except Exception as e:
        logger.error(f"Email analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rules")
async def get_llm_rules():
    """Get current LLM rules"""
    return ai_agent.rules

@app.post("/rules/reload")
async def reload_llm_rules():
    """Reload LLM rules from file"""
    try:
        await ai_agent.load_llm_rules()
        return {"status": "success", "message": "LLM rules reloaded"}
    except Exception as e:
        logger.error(f"Failed to reload rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=os.getenv("DEBUG", "False").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )