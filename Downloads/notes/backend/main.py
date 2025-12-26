# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Firebase Admin (if available)
try:
    from firebase_admin import initialize_firebase_admin, get_firestore_client
    print("Attempting to initialize Firebase Admin...")
    firestore_client = initialize_firebase_admin()
    if firestore_client:
        print("✓ Firebase Admin initialized successfully")
    else:
        print("⚠ Firebase Admin not available (Firestore disabled)")
except Exception as e:
    print(f"⚠ Could not initialize Firebase Admin: {e}")
    print("  Firestore features will be disabled")

# Verify environment variables
try:
    from firebase_config import verify_env_variables
    verify_env_variables()
except ImportError:
    print("⚠ firebase_config not available, skipping environment variable verification")

# Import routes
from routes import router
from collaboration_routes import router as collaboration_router
from project_files_routes import router as project_files_router
from chat_routes import router as chat_router
from ai_routes import router as ai_router
from analytics_routes import router as analytics_router
from websocket_routes import router as websocket_router
from database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)
print("✓ Database tables created/verified")

app = FastAPI(
    title="EduNex API",
    description="Collaborative Learning Platform API",
    version="1.0.0"
)

# CORS middleware configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",  # Vite default port
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api prefix
app.include_router(router, prefix="/api", tags=["api"])
app.include_router(collaboration_router, prefix="/api", tags=["Collaboration"])
app.include_router(project_files_router, prefix="/api", tags=["Project Files"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])
app.include_router(ai_router, prefix="/api", tags=["AI"])
app.include_router(analytics_router, prefix="/api", tags=["Analytics"])
app.include_router(websocket_router, tags=["WebSocket"])

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Serve static files from uploads directory
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "EduNex API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)