"""
AdAngle - AI Ad Generator Using Proven Marketing Psychology
FastAPI application entry point.

Generate Facebook/Instagram ads using framework-driven marketing psychology:
- Problem-Agitate-Solution (PAS)
- Social Proof
- Transformation
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from api.routes import assets, generate

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Runs on startup and shutdown.
    """
    # Startup
    print("Starting AdAngle API...")
    print(f"Debug mode: {settings.debug}")
    yield
    # Shutdown
    print("Shutting down AdAngle API...")


# Create FastAPI application
app = FastAPI(
    title="AdAngle API",
    description="""
## AI-Powered Ad Generator Using Marketing Psychology

Generate 3 psychologically different ad concepts in seconds using proven conversion frameworks.

### How It Works

1. **Upload Assets** - Upload your product image (logo optional)
2. **Describe Your Product** - Tell us what you sell, who buys it, and the main benefit
3. **Get 3 Angles** - Receive 3 ads using different psychological frameworks

### Marketing Frameworks

- **Problem-Agitate-Solution (PAS)** - Call out pain, agitate it, offer solution
- **Social Proof** - Lead with impressive numbers/results, invite to join
- **Transformation** - Show current frustration vs aspirational future

### Key Features

- **Framework-Driven** - Not templates, real marketing psychology
- **Copy-First** - Strong copy, not just pretty visuals
- **90-Second Generation** - Fast results, no setup required
- **True Variety** - 3 psychologically DIFFERENT approaches, not layout variations

### API Notes

- Session-based tracking (no authentication required for MVP)
- Signed URLs expire after 1 hour by default
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
app.include_router(generate.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "AdAngle API",
        "version": "1.0.0",
        "tagline": "3 marketing angles in 90 seconds",
        "description": "AI-powered ad generator using proven marketing psychology frameworks",
        "docs": "/docs",
        "endpoints": {
            "upload_assets": "POST /api/assets/upload",
            "generate_ads": "POST /api/generate",
            "get_generated_ads": "GET /api/generate/{session_id}",
        },
        "frameworks": [
            "Problem-Agitate-Solution (PAS)",
            "Social Proof",
            "Transformation",
        ],
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "adangle"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
