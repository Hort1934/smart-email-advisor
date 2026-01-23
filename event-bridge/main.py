import asyncio
import os
import logging
import json
from typing import Dict, List, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import redis.asyncio as redis
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Smart Email Advisor - Event Bridge",
    description="Event Bridge для обробки подій та координації між сервісами",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event models
class EmailEvent(BaseModel):
    event_type: str  # new_email, analysis_complete, user_action
    email_id: str
    data: Dict[str, Any]
    timestamp: datetime = datetime.utcnow()
    source_service: str

class EventBridge:
    def __init__(self):
        self.redis_client = None
        self.subscriptions = {}
        
    async def initialize(self):
        """Initialize Redis connection"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
            self.redis_client = redis.from_url(redis_url)
            await self.redis_client.ping()
            logger.info("Event Bridge Redis connection established")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            raise
            
    async def publish_event(self, event: EmailEvent):
        """Publish event to Redis channels"""
        try:
            event_data = event.dict()
            
            # Publish to general event channel
            await self.redis_client.publish("email_events", json.dumps(event_data))
            
            # Publish to specific event type channel
            await self.redis_client.publish(
                f"email_events:{event.event_type}",
                json.dumps(event_data)
            )
            
            # Store event in queue for processing
            await self.redis_client.lpush("event_queue", json.dumps(event_data))
            
            logger.info(f"Event published: {event.event_type} for email {event.email_id}")
            
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            raise
            
    async def subscribe_to_events(self, event_types: List[str], callback):
        """Subscribe to specific event types"""
        try:
            pubsub = self.redis_client.pubsub()
            
            for event_type in event_types:
                await pubsub.subscribe(f"email_events:{event_type}")
                
            logger.info(f"Subscribed to events: {event_types}")
            return pubsub
            
        except Exception as e:
            logger.error(f"Failed to subscribe to events: {e}")
            raise
            
    async def process_email_queue(self):
        """Process emails from queue"""
        while True:
            try:
                # Get email from queue (blocking)
                result = await self.redis_client.brpop("new_emails", timeout=10)
                
                if result:
                    queue_name, email_data = result
                    email_data = json.loads(email_data)
                    
                    # Create new email event
                    event = EmailEvent(
                        event_type="new_email",
                        email_id=email_data.get("id"),
                        data=email_data,
                        source_service="email_bridge"
                    )
                    
                    await self.publish_event(event)
                    
                    # Send to AI agent for analysis
                    await self.send_to_ai_agent(email_data)
                    
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
                await asyncio.sleep(5)
                
    async def send_to_ai_agent(self, email_data: Dict[str, Any]):
        """Send email to AI agent for analysis"""
        try:
            import aiohttp
            
            ai_agent_url = os.getenv("AI_AGENT_URL", "http://ai-agent:8001")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{ai_agent_url}/analyze",
                    json=email_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        analysis_result = await response.json()
                        
                        # Publish analysis complete event
                        event = EmailEvent(
                            event_type="analysis_complete",
                            email_id=email_data.get("id"),
                            data=analysis_result,
                            source_service="event_bridge"
                        )
                        
                        await self.publish_event(event)
                        
                        # Send results to backend
                        await self.send_to_backend(analysis_result)
                        
                    else:
                        logger.error(f"AI Agent returned status {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send to AI agent: {e}")
            
    async def send_to_backend(self, analysis_result: Dict[str, Any]):
        """Send analysis results to backend"""
        try:
            import aiohttp
            
            backend_url = os.getenv("BACKEND_URL", "http://backend:8000")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{backend_url}/internal/analysis-complete",
                    json=analysis_result,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Analysis sent to backend for email {analysis_result.get('email_id')}")
                    else:
                        logger.error(f"Backend returned status {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send to backend: {e}")
            
    async def start_background_tasks(self):
        """Start background processing tasks"""
        asyncio.create_task(self.process_email_queue())
        logger.info("Background tasks started")

# Initialize Event Bridge
event_bridge = EventBridge()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        await event_bridge.initialize()
        await event_bridge.start_background_tasks()
        logger.info("Event Bridge initialized successfully")
    except Exception as e:
        logger.error(f"Event Bridge initialization failed: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Event Bridge is running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/events/publish")
async def publish_event(event_data: Dict[str, Any]):
    """Manually publish an event"""
    try:
        event = EmailEvent(**event_data)
        await event_bridge.publish_event(event)
        return {"status": "success", "message": "Event published"}
    except Exception as e:
        logger.error(f"Failed to publish event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/events/stats")
async def get_event_stats():
    """Get event processing statistics"""
    try:
        stats = {
            "queue_size": await event_bridge.redis_client.llen("event_queue"),
            "new_emails_queue": await event_bridge.redis_client.llen("new_emails"),
            "timestamp": datetime.utcnow().isoformat()
        }
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=os.getenv("DEBUG", "False").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )