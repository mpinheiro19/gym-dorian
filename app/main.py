from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.api.routes import auth, users, admin, analytics, workouts, templates, plans

# Import all models to ensure Base.metadata contains all table definitions for Alembic
from app.models import User, UserSettings, UserGoal, Exercise, WorkoutSession, LogExercise, WorkoutTemplate, TemplateExercise, WorkoutPlan, PlanWeek, PlanDay

# Note: We don't call Base.metadata.create_all(bind=engine) here
# because Alembic manages table creation through migrations

app = FastAPI(
    title="Gym Dorian API",
    description="Fitness tracking and analytics API with user authentication",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS middleware
# TODO: Update allowed origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(admin.router, prefix="/api")  # Admin routes (superuser only)
app.include_router(workouts.router, prefix="/api")  # Workout logging
app.include_router(templates.router, prefix="/api")  # Workout templates
app.include_router(analytics.router, prefix="/api")  # Analytics & progress tracking
app.include_router(plans.router, prefix="/api")  # Workout plans

# Root endpoint
@app.get("/")
def read_root():
    """Root endpoint with API information."""
    return {
        "status": "ok",
        "message": "Gym Dorian API is running",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Health check endpoint
@app.get("/ping")
def ping():
    """Health check endpoint to verify API connectivity."""
    return {"status": "ok"}


# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print("🏋️ Gym Dorian API started successfully!")
    print("📚 API Documentation available at: /docs")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print("👋 Gym Dorian API shutting down...")