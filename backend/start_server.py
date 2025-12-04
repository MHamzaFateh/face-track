"""
Start the Face Recognition API server
"""
import uvicorn
from config import settings

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Face Recognition System")
    print("=" * 60)
    print(f"Host: {settings.API_HOST}")
    print(f"Port: {settings.API_PORT}")
    print(f"Model: {settings.FACE_MODEL}")
    print(f"Distance Metric: {settings.DISTANCE_METRIC}")
    print(f"Recognition Threshold: {settings.RECOGNITION_THRESHOLD}")
    print("=" * 60)
    print("\nAPI Documentation available at:")
    print(f"  - Swagger UI: http://localhost:{settings.API_PORT}/docs")
    print(f"  - ReDoc: http://localhost:{settings.API_PORT}/redoc")
    print("\nPress CTRL+C to stop the server")
    print("=" * 60)
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )

