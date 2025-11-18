from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.core.database import init_db, close_db
from app.utils.logger import setup_logging
from app.api import auth_routes, trading_routes, ai_routes
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    setup_logging()
    await init_db()
    print(f"🚀 {settings.APP_NAME} started successfully!")
    print(f"📊 Environment: {settings.ENVIRONMENT}")
    print(f"🔧 Testnet Mode: {settings.BINANCE_TESTNET}")
    yield
    # Shutdown
    await close_db()
    print("👋 Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Cryptocurrency Trading Agent for Binance Exchange",
    version=settings.API_VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router)
app.include_router(trading_routes.router)
app.include_router(ai_routes.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Cryptocurrency Trading Bot API",
        "version": settings.API_VERSION,
        "status": "operational",
        "environment": settings.ENVIRONMENT,
        "testnet": settings.BINANCE_TESTNET
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2025-01-01T00:00:00Z"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
