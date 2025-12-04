"""
Live Face Tracking Service
Handles real-time face detection and recognition from video streams
"""
import cv2
import numpy as np
from io import BytesIO
from PIL import Image
import time
from typing import Dict, List, Optional
from .face_recognition_service import FaceRecognitionService


class LiveTrackingService:
    """Service for real-time face tracking and recognition"""
    
    def __init__(self, face_service: FaceRecognitionService):
        """
        Initialize live tracking service
        
        Parameters:
        - face_service: Face recognition service instance
        """
        self.face_service = face_service
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.frame_counter = 0
        self.process_every_n_frames = 2  # Process every 2nd frame for performance
        self.recognition_cache = {}  # Cache recent recognitions
        self.cache_duration = 1.0  # Cache for 1 second
        
    def clear_old_cache(self):
        """Clear cached recognitions older than cache_duration"""
        current_time = time.time()
        keys_to_delete = []
        
        for key, (timestamp, _) in self.recognition_cache.items():
            if current_time - timestamp > self.cache_duration:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self.recognition_cache[key]
    
    def detect_faces(self, img_array: np.ndarray) -> List[tuple]:
        """
        Detect faces in an image using Haar Cascade
        
        Parameters:
        - img_array: Image as numpy array
        
        Returns:
        - List of face bounding boxes (x, y, w, h)
        """
        try:
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            return faces
        except Exception as e:
            print(f"Error detecting faces: {e}")
            return []
    
    def recognize_face(self, face_img: np.ndarray, bbox: tuple) -> Optional[Dict]:
        """
        Recognize a face from image region
        
        Parameters:
        - face_img: Face region as numpy array
        - bbox: Bounding box (x, y, w, h)
        
        Returns:
        - Recognition result or None
        """
        try:
            # Create a simple cache key based on bbox
            cache_key = f"{bbox[0]}_{bbox[1]}_{bbox[2]}_{bbox[3]}"
            current_time = time.time()
            
            # Check cache
            if cache_key in self.recognition_cache:
                timestamp, result = self.recognition_cache[cache_key]
                if current_time - timestamp < self.cache_duration:
                    return result
            
            # Save face temporarily
            temp_path = f"temp/live_face_{int(time.time() * 1000)}.jpg"
            Image.fromarray(face_img).save(temp_path)
            
            # Recognize face
            recognition_result = self.face_service.recognize_user(temp_path)
            
            # Clean up temp file
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            # Cache the result
            if recognition_result.get('recognized'):
                result = {
                    'user_id': recognition_result['user_id'],
                    'name': recognition_result['name'],
                    'confidence': recognition_result['confidence'],
                    'distance': recognition_result['distance']
                }
                self.recognition_cache[cache_key] = (current_time, result)
                return result
            
            return None
            
        except Exception as e:
            print(f"Error recognizing face: {e}")
            return None
    
    def process_frame(self, frame_bytes: bytes) -> Dict:
        """
        Process a single video frame for face detection and recognition
        
        Parameters:
        - frame_bytes: Frame as bytes (JPEG)
        
        Returns:
        - Dictionary with detected faces and recognitions
        """
        try:
            # Increment frame counter
            self.frame_counter += 1
            
            # Clear old cache entries
            if self.frame_counter % 30 == 0:  # Every 30 frames
                self.clear_old_cache()
            
            # Convert bytes to image
            image = Image.open(BytesIO(frame_bytes))
            img_array = np.array(image)
            
            # Detect faces
            faces = self.detect_faces(img_array)
            
            recognitions = []
            
            # Process faces (but not every frame)
            should_process = (self.frame_counter % self.process_every_n_frames) == 0
            
            for idx, (x, y, w, h) in enumerate(faces):
                face_data = {
                    'face_id': f'Face_{idx + 1:02d}',  # Generate face ID (Face_01, Face_02, etc.)
                    'bbox': {
                        'x': int(x),
                        'y': int(y),
                        'width': int(w),
                        'height': int(h)
                    }
                }
                
                # Only run recognition every N frames
                if should_process:
                    # Extract face region (with some padding)
                    padding = 20
                    y1 = max(0, y - padding)
                    y2 = min(img_array.shape[0], y + h + padding)
                    x1 = max(0, x - padding)
                    x2 = min(img_array.shape[1], x + w + padding)
                    
                    face_img = img_array[y1:y2, x1:x2]
                    
                    # Recognize face
                    recognition = self.recognize_face(face_img, (x, y, w, h))
                    
                    if recognition:
                        face_data.update(recognition)
                        face_data['recognized'] = True
                    else:
                        face_data['recognized'] = False
                        face_data['name'] = 'Unknown'
                        face_data['confidence'] = 0.0
                else:
                    # Use cached data or mark as unknown
                    cache_key = f"{x}_{y}_{w}_{h}"
                    if cache_key in self.recognition_cache:
                        _, cached_result = self.recognition_cache[cache_key]
                        face_data.update(cached_result)
                        face_data['recognized'] = True
                    else:
                        face_data['recognized'] = False
                        face_data['name'] = 'Unknown'
                        face_data['confidence'] = 0.0
                
                recognitions.append(face_data)
            
            return {
                'success': True,
                'frame_number': self.frame_counter,
                'faces_detected': len(faces),
                'recognitions': recognitions
            }
            
        except Exception as e:
            print(f"Error processing frame: {e}")
            return {
                'success': False,
                'error': str(e),
                'recognitions': []
            }

