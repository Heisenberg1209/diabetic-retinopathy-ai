from fastapi import FastAPI

from .database import engine, Base
from . import models
from .routes import router


# Create database tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Diabetic Retinopathy Screening API",
    description="Backend API for AI-assisted diabetic retinopathy screening",
    version="1.0.0"
)


# Register API routes
app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "Diabetic Retinopathy Screening API is running",
        "status": "success"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }