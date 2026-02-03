"""Configuration settings for the Face Recognition System"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings"""
    
    # API Settings
    API_TITLE: str = "Face Recognition System"
    API_VERSION: str = "1.0.0"
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8003"))
    
    # Face Recognition Settings
    FACE_MODEL: str = os.getenv("FACE_MODEL", "Facenet512")  # Options: VGG-Face, Facenet, Facenet512, OpenFace, DeepFace, DeepID, ArcFace, Dlib, SFace
    DISTANCE_METRIC: str = os.getenv("DISTANCE_METRIC", "cosine")  # Options: cosine, euclidean, euclidean_l2
    RECOGNITION_THRESHOLD: float = float(os.getenv("RECOGNITION_THRESHOLD", "0.5"))  # Lower = more strict, 0.5 = balanced for live tracking
    DUPLICATE_FACE_THRESHOLD: float = float(os.getenv("DUPLICATE_FACE_THRESHOLD", "0.4"))  # Threshold for detecting duplicate registrations
    
    # Face Detection Settings (Haar Cascade)
    HAAR_SCALE_FACTOR: float = float(os.getenv("HAAR_SCALE_FACTOR", "1.15"))  # 1.1-1.3, higher = stricter (reduces false positives)
    HAAR_MIN_NEIGHBORS: int = int(os.getenv("HAAR_MIN_NEIGHBORS", "8"))  # 3-10, higher = stricter (reduces false positives)
    HAAR_MIN_SIZE: int = int(os.getenv("HAAR_MIN_SIZE", "60"))  # Minimum face size in pixels (60-100 recommended)
    
    # Storage Settings
    DATA_DIR: str = os.getenv("DATA_DIR", "data")
    USERS_DIR: str = os.getenv("USERS_DIR", "data/users")
    FACES_DIR: str = os.getenv("FACES_DIR", "data/faces")
    TEMP_DIR: str = os.getenv("TEMP_DIR", "temp")
    
    # File Settings
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))  # 10 MB
    ALLOWED_EXTENSIONS: list = [".jpg", ".jpeg", ".png", ".bmp"]


settings = Settings()

