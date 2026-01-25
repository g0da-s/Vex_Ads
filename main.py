"""
AdMimic - AI Ad Generator
FastAPI application entry point.

Generate Facebook ads inspired by competitor patterns using Google Gemini AI.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from api.routes import assets, competitors, generate

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Runs on startup and shutdown.
    """
    # Startup
    print("Starting AdMimic API...")
    print(f"Debug mode: {settings.debug}")
    yield
    # Shutdown
    print("Shutting down AdMimic API...")


# Create FastAPI application
app = FastAPI(
    title="AdMimic API",
    description="""
## AI-Powered Ad Generator

Generate professional Facebook ads inspired by competitor patterns using Google Gemini AI.

### How It Works

1. **Upload Assets** - Upload your product image and brand logo
2. **Analyze Competitors** - Paste a Facebook Ad Library URL to fetch competitor ads
3. **Generate Ads** - Select a competitor ad as style reference and generate new ads

### Key Features

- **No Scraping Required** - Uses Meta Ad Library API for direct image access
- **Supabase Storage** - All images stored securely with signed URLs
- **Gemini AI** - State-of-the-art multimodal generation

### API Notes

- Session-based tracking (no authentication required for MVP)
- Signed URLs expire after 1 hour by default
- Meta API works best for EU ads or political/social issue ads
""",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(assets.router, prefix="/api")
app.include_router(competitors.router, prefix="/api")
app.include_router(generate.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "AdMimic API",
        "version": "1.0.0",
        "description": "AI-powered ad generator using competitor analysis",
        "docs": "/docs",
        "endpoints": {
            "upload_assets": "POST /api/assets/upload",
            "analyze_competitor": "POST /api/competitors/analyze",
            "generate_ads": "POST /api/generate",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
