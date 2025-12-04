"""
Advanced Tracking Service with SCRFD + ByteTrack + ArcFace
Complete pipeline for real-time face detection, tracking, and recognition
"""
import cv2
import numpy as np
from io import BytesIO
from PIL import Image
import time
import os
from typing import Dict, List, Tuple
from insightface.app import FaceAnalysis
from .byte_tracker import ByteTracker, TrackedFace
from .face_recognition_service import FaceRecognitionService
from config import settings


class AdvancedTrackingService:
    """
    Advanced face tracking with SCRFD + ByteTrack + ArcFace pipeline
    
    Pipeline:
    1. SCRFD detects all faces → returns bounding boxes
    2. ByteTrack assigns unique IDs → tracks faces across frames
    3. ArcFace extracts identity → 512-dim feature vector
    4. Compare with database → verify identity
    """
    
    def __init__(self, face_service: FaceRecognitionService):
        """
        Initialize advanced tracking service
        
        Parameters:
        - face_service: Face recognition service for database operations
        """
        self.face_service = face_service
        
        # Initialize InsightFace with SCRFD detector and ArcFace recognizer
        print("Initializing SCRFD + ArcFace models...")
        try:
            # Try initializing FaceAnalysis (handles different versions)
            try:
                # Newer version (>0.7) with providers parameter
                self.app = FaceAnalysis(
                    name='buffalo_l',  # SCRFD + ArcFace
                    providers=['CPUExecutionProvider']
                )
            except TypeError:
                # Older version (0.2.1) - name is required, providers not supported
                self.app = FaceAnalysis(name='buffalo_l')
            
            # Prepare the model (ctx_id: -1 for CPU, 0 for GPU)
            self.app.prepare(ctx_id=-1, det_size=(640, 640))
            print("[OK] SCRFD + ArcFace models loaded successfully")
            self.use_insightface = True
        except Exception as e:
            print(f"[INFO] SCRFD not available, using Haar Cascade + Facenet512")
            print(f"       (To enable SCRFD, download InsightFace models)")
            self.use_insightface = False
            # Fallback to Haar Cascade
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
        
        # Initialize ByteTrack tracker
        self.tracker = ByteTracker(
            max_age=30,        # Keep track for 30 frames without detection
            min_hits=3,        # Confirm track after 3 detections
            iou_threshold=0.3  # IoU threshold for matching
        )
        
        # Recognition cache
        self.recognized_tracks = {}  # face_id -> recognition result
        self.frame_counter = 0
        self.process_every_n_frames = 2  # Process recognition every 2nd frame
        
        # Detection validation settings
        self.validate_faces = True  # Enable face validation
        self.validation_cache = {}  # Cache validation results
        
        # Create temp directory if not exists
        os.makedirs("temp", exist_ok=True)
        
    def detect_faces_scrfd(self, img_array: np.ndarray) -> List[Dict]:
        """
        Step 1: Detect faces using SCRFD
        
        Parameters:
        - img_array: Image as numpy array (RGB)
        
        Returns:
        - List of detected faces with bounding boxes and embeddings
        """
        try:
            # Detect faces using InsightFace (SCRFD + ArcFace)
            faces = self.app.get(img_array)
            
            detected_faces = []
            for face in faces:
                # Extract bounding box
                bbox = face.bbox.astype(int)
                x1, y1, x2, y2 = bbox
                w = x2 - x1
                h = y2 - y1
                
                detected_faces.append({
                    'bbox': (x1, y1, w, h),
                    'embedding': face.embedding,  # ArcFace 512-dim vector
                    'confidence': float(face.det_score),  # Detection confidence
                    'landmarks': face.kps  # 5 facial landmarks
                })
            
            return detected_faces
            
        except Exception as e:
            print(f"Error in SCRFD detection: {e}")
            return []
    
    def detect_faces_haar(self, img_array: np.ndarray) -> List[Dict]:
        """
        Fallback: Detect faces using Haar Cascade
        
        Parameters:
        - img_array: Image as numpy array (RGB)
        
        Returns:
        - List of detected faces with bounding boxes
        """
        try:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # More strict parameters to reduce false positives (configurable)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=settings.HAAR_SCALE_FACTOR,   # Higher = stricter (default: 1.15)
                minNeighbors=settings.HAAR_MIN_NEIGHBORS,  # Higher = fewer false positives (default: 8)
                minSize=(settings.HAAR_MIN_SIZE, settings.HAAR_MIN_SIZE),  # Minimum face size (default: 60x60)
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            detected_faces = []
            filtered_count = 0
            
            for (x, y, w, h) in faces:
                # Validate face detection (filter false positives)
                aspect_ratio = w / h if h > 0 else 0
                
                # Face should have aspect ratio between 0.7 and 1.3 (roughly square)
                # This filters out horizontal/vertical false detections
                if not (0.7 <= aspect_ratio <= 1.3):
                    filtered_count += 1
                    continue
                
                # Face should be reasonably sized (not too small or too large)
                face_area = w * h
                image_area = img_array.shape[0] * img_array.shape[1]
                relative_size = face_area / image_area
                
                # Face should occupy between 0.5% and 50% of frame
                if not (0.005 <= relative_size <= 0.5):
                    filtered_count += 1
                    continue
                
                detected_faces.append({
                    'bbox': (x, y, w, h),
                    'embedding': None,  # Will extract later if needed
                    'confidence': 1.0,
                    'landmarks': None
                })
            
            # Log filtering stats (only occasionally to avoid spam)
            if filtered_count > 0 and len(faces) > 0:
                if self.frame_counter % 30 == 0:  # Log every 30 frames
                    print(f"[INFO] Filtered {filtered_count}/{len(faces)} false positive detections")
            
            return detected_faces
            
        except Exception as e:
            print(f"Error in Haar detection: {e}")
            return []
    
    def recognize_track(self, face_id: int, embedding: np.ndarray, img_array: np.ndarray, bbox: Tuple) -> Dict:
        """
        Step 3: Recognize face using ArcFace embedding
        
        Parameters:
        - face_id: Unique track ID
        - embedding: ArcFace 512-dim feature vector
        - img_array: Original image (fallback)
        - bbox: Bounding box (x, y, w, h)
        
        Returns:
        - Recognition result
        """
        try:
            # Check if already recognized
            if face_id in self.recognized_tracks:
                return self.recognized_tracks[face_id]
            
            if embedding is not None:
                # Use embedding directly for comparison
                result = self.face_service.recognize_by_embedding(embedding)
            else:
                # Fallback: Extract face and use existing recognition
                x, y, w, h = bbox
                padding = 20
                y1 = max(0, y - padding)
                y2 = min(img_array.shape[0], y + h + padding)
                x1 = max(0, x - padding)
                x2 = min(img_array.shape[1], x + w + padding)
                
                face_img = img_array[y1:y2, x1:x2]
                
                # Save temporarily
                temp_path = f"temp/track_{face_id}_{int(time.time() * 1000)}.jpg"
                Image.fromarray(face_img).save(temp_path)
                
                result = self.face_service.recognize_user(temp_path)
                
                # Clean up
                import os
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            # Cache result
            if result.get('recognized'):
                recognition_data = {
                    'recognized': True,
                    'user_id': result['user_id'],
                    'name': result['name'],
                    'confidence': result['confidence'],
                    'distance': result['distance']
                }
                self.recognized_tracks[face_id] = recognition_data
                return recognition_data
            
            return {
                'recognized': False,
                'user_id': None,
                'name': 'Unknown',
                'confidence': 0.0
            }
            
        except Exception as e:
            print(f"Error recognizing track {face_id}: {e}")
            return {
                'recognized': False,
                'user_id': None,
                'name': 'Unknown',
                'confidence': 0.0
            }
    
    def process_frame(self, frame_bytes: bytes) -> Dict:
        """
        Complete pipeline: SCRFD → ByteTrack → ArcFace Recognition
        
        Parameters:
        - frame_bytes: Frame as bytes (JPEG)
        
        Returns:
        - Dictionary with tracked faces and recognitions
        """
        try:
            self.frame_counter += 1
            
            # Convert bytes to image
            image = Image.open(BytesIO(frame_bytes))
            img_array = np.array(image)
            
            # Step 1: SCRFD detects all faces
            if self.use_insightface:
                detected_faces = self.detect_faces_scrfd(img_array)
            else:
                detected_faces = self.detect_faces_haar(img_array)
            
            # Extract bounding boxes and embeddings
            bboxes = [face['bbox'] for face in detected_faces]
            embeddings = [face['embedding'] for face in detected_faces]
            
            # Step 2: ByteTrack assigns unique IDs and tracks faces
            tracked_faces = self.tracker.update(bboxes, embeddings)
            
            # Step 3: Recognize faces (only process every N frames)
            should_process = (self.frame_counter % self.process_every_n_frames) == 0
            
            results = []
            for track in tracked_faces:
                face_data = {
                    'face_id': f"Face_{track.face_id:02d}",  # Face_01, Face_02, etc.
                    'bbox': {
                        'x': int(track.bbox[0]),
                        'y': int(track.bbox[1]),
                        'width': int(track.bbox[2]),
                        'height': int(track.bbox[3])
                    },
                    'age': track.age,  # How many frames tracked
                    'hits': track.hits  # Number of detections
                }
                
                # Recognize face if needed
                if should_process or track.face_id not in self.recognized_tracks:
                    recognition = self.recognize_track(
                        track.face_id,
                        track.embedding,
                        img_array,
                        track.bbox
                    )
                    
                    face_data.update(recognition)
                else:
                    # Use cached recognition
                    if track.face_id in self.recognized_tracks:
                        face_data.update(self.recognized_tracks[track.face_id])
                    else:
                        face_data['recognized'] = False
                        face_data['name'] = 'Unknown'
                        face_data['confidence'] = 0.0
                
                results.append(face_data)
            
            return {
                'success': True,
                'frame_number': self.frame_counter,
                'faces_detected': len(detected_faces),
                'faces_tracked': len(tracked_faces),
                'recognitions': results,
                'using_insightface': self.use_insightface
            }
            
        except Exception as e:
            print(f"Error processing frame: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'recognitions': []
            }
    
    def clear_recognition_cache(self):
        """Clear recognition cache"""
        self.recognized_tracks.clear()
    
    def reset_tracker(self):
        """Reset tracker (clear all tracks)"""
        self.tracker.reset()
        self.clear_recognition_cache()
        self.frame_counter = 0

