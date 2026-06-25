from fastapi import FastAPI
from app.database import engine, Base
from app.api.routes import router as assets_router
from app.api.analyze import router as analyze_router

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Buguard Asset Management API",
    description="DarkAtlas Attack Surface Monitoring - Asset Management Module",
    version="1.0.0"
)

# Register routers
app.include_router(assets_router, tags=["Assets"])
app.include_router(analyze_router, tags=["Analysis"])

@app.get("/")
def root():
    return {
        "message": "Buguard Asset Management API",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}