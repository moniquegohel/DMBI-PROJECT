from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.database import engine, Base, check_db_connection
import app.database.models  # Ensures all ORM models are registered before create_all

# Initialize SQLite database tables on application startup
Base.metadata.create_all(bind=engine)

# Initialize SmartStock FastAPI Application
app = FastAPI(
    title="SmartStock API",
    description="ML-Based Retail Demand Forecasting & Inventory Recommendation API",
    version="1.0.0"
)

# Enable CORS for React Frontend (running on Vite, default port 5173 or 3000)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*"  # Allow all origins in local development mode
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import API Routers
from app.routes.dataset import router as dataset_router
from app.routes.analysis import router as analysis_router
from app.routes.model import router as model_router
from app.routes.forecast import router as forecast_router
from app.routes.inventory import router as inventory_router
from app.routes.recommendation import router as recommendation_router

# Register API Routers
app.include_router(dataset_router, prefix="/api/dataset", tags=["dataset"])
app.include_router(analysis_router, prefix="/api/analysis", tags=["analysis"])
app.include_router(model_router, prefix="/api/model", tags=["model"])
app.include_router(forecast_router, prefix="/api/forecast", tags=["forecast"])
app.include_router(inventory_router, prefix="/api/inventory", tags=["inventory"])
app.include_router(recommendation_router, prefix="/api/recommendation", tags=["recommendation"])


@app.get("/")
def read_root():
    """Root health check endpoint."""
    return {
        "status": "ok",
        "app": "SmartStock API",
        "version": "1.0.0",
        "message": "Welcome to SmartStock Demand Forecasting API"
    }

@app.get("/api/health")
def health_check():
    """Detailed API health status endpoint testing real database connection."""
    is_db_connected = check_db_connection()
    return {
        "status": "healthy",
        "database": "connected" if is_db_connected else "disconnected",
        "ml_models": "loaded"
    }
