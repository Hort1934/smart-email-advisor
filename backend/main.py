from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import os
from dotenv import load_dotenv

from app.routes import email_routes, auth_routes, analytics_routes, demo_routes, stats_routes, logs_routes, smart_assistant_routes
from app.services.database import init_db
from app.services.ai_service import AIService

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Smart Email Advisor",
    description="AI-орієнтований сервіс для інтелектуального аналізу електронних листів",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшені вказати конкретні домени
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and other services"""
    try:
        await init_db()
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
        print("Application will continue without database")
    
    # Initialize AI service
    try:
        ai_service = AIService()
        app.state.ai_service = ai_service
    except Exception as e:
        print(f"Warning: AI service initialization failed: {e}")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Smart Email Advisor API is running"}

# Include routers
app.include_router(demo_routes.router, prefix="/api/demo", tags=["demo"])
app.include_router(auth_routes.router, prefix="/api/auth", tags=["authentication"])
app.include_router(email_routes.router, prefix="/api/emails", tags=["emails"])
app.include_router(analytics_routes.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(stats_routes.router, prefix="/api/stats", tags=["statistics"])
app.include_router(logs_routes.router, prefix="/api/logs", tags=["logs"])
app.include_router(smart_assistant_routes.router, prefix="/api/smart", tags=["smart-assistant"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )