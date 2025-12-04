from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserRegistration(BaseModel):
    """Model for user registration"""
    user_id: str
    name: str
    registered_at: Optional[str] = None


class UserRecognitionResponse(BaseModel):
    """Model for recognition response"""
    recognized: bool
    user_id: Optional[str] = None
    name: Optional[str] = None
    confidence: Optional[float] = None
    distance: Optional[float] = None


class UserInfo(BaseModel):
    """Model for user information"""
    user_id: str
    name: str
    registered_at: str
    face_embedding_size: Optional[int] = None

