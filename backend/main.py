"""
Face Recognition System - FastAPI Application
Main API server with REST endpoints and WebSocket support
"""
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import shutil
from pathlib import Path

from config import settings
from services.face_recognition_service import FaceRecognitionService
from services.live_tracking_service import LiveTrackingService
from models.user import UserRegistration, UserRecognitionResponse, UserInfo

# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="AI-powered Face Recognition System with DeepFace"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
face_service = FaceRecognitionService(
    model_name=settings.FACE_MODEL,
    distance_metric=settings.DISTANCE_METRIC,
    threshold=settings.RECOGNITION_THRESHOLD
)

live_tracking_service = LiveTrackingService(face_service)

# Create temp directory if it doesn't exist
os.makedirs(settings.TEMP_DIR, exist_ok=True)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Face Recognition System API",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Face Recognition System",
        "model": settings.FACE_MODEL,
        "threshold": settings.RECOGNITION_THRESHOLD
    }


@app.post("/api/register", response_model=dict)
async def register_user(
    user_id: str = Form(...),
    name: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Register a new user with their face image
    
    Parameters:
    - user_id: Unique identifier for the user
    - name: Full name of the user
    - file: Face image file (jpg, jpeg, png, bmp)
    
    Returns:
    - Success message with user details
    """
    try:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Save uploaded file temporarily
        temp_path = os.path.join(settings.TEMP_DIR, file.filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        try:
            # Register user
            result = face_service.register_user(
                user_id=user_id,
                name=name,
                image_path=temp_path
            )
            
            return {
                "success": True,
                "message": "User registered successfully",
                "user": result
            }
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/recognize", response_model=UserRecognitionResponse)
async def recognize_user(file: UploadFile = File(...)):
    """
    Recognize a user from their face image
    
    Parameters:
    - file: Face image file (jpg, jpeg, png, bmp)
    
    Returns:
    - Recognition result with user details and confidence
    """
    try:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Save uploaded file temporarily
        temp_path = os.path.join(settings.TEMP_DIR, file.filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        try:
            # Recognize user
            result = face_service.recognize_user(temp_path)
            
            if result:
                return UserRecognitionResponse(
                    recognized=True,
                    user_id=result["user_id"],
                    name=result["name"],
                    confidence=result.get("confidence"),
                    distance=result.get("distance")
                )
            else:
                return UserRecognitionResponse(recognized=False)
                
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/users", response_model=List[UserInfo])
async def get_all_users():
    """Get all registered users"""
    try:
        users = face_service.get_all_users()
        return [UserInfo(**user) for user in users]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users/{user_id}", response_model=UserInfo)
async def get_user(user_id: str):
    """Get a specific user by ID"""
    try:
        user = face_service.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserInfo(**user)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/users/{user_id}")
async def delete_user(user_id: str):
    """Delete a user by ID"""
    try:
        success = face_service.delete_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "success": True,
            "message": f"User {user_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/live-tracking")
async def websocket_live_tracking(websocket: WebSocket):
    """
    WebSocket endpoint for real-time face tracking
    
    Receives video frames and returns face detection/recognition results
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive frame data from client
            data = await websocket.receive()
            
            if "bytes" in data:
                # Process frame and get tracking results
                frame_bytes = data["bytes"]
                results = await live_tracking_service.process_frame(frame_bytes)
                
                # Send results back to client
                await websocket.send_json(results)
            elif "text" in data:
                # Handle text commands (e.g., "start", "stop")
                command = data["text"]
                if command == "stop":
                    break
                    
    except WebSocketDisconnect:
        print("Client disconnected from live tracking")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        await websocket.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )

