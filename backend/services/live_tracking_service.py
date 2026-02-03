"""
Live Face Tracking Service - Enhanced Version
Handles real-time face detection and recognition from video streams
with robust tracking and recognition smoothing
"""
import cv2
import numpy as np
from io import BytesIO
from PIL import Image
import time
import os
from typing import Dict, List, Optional, Tuple
from .face_recognition_service import FaceRecognitionService


class FaceTrack:
    """Class to represent a tracked face across multiple frames"""
    
    def __init__(self, track_id: int, bbox: Tuple[int, int, int, int]):
        self.track_id = track_id
        self.bbox = bbox
        self.last_seen = time.time()
        self.first_seen = time.time()
        self.recognition_history = []  # List of recognition results
        self.stable_identity = None  # Smoothed recognition result
        self.frames_since_update = 0
        self.consecutive_recognitions = 0
        
    def update_bbox(self, bbox: Tuple[int, int, int, int]):
        """Update the bounding box and last seen time"""
        self.bbox = bbox
        self.last_seen = time.time()
        self.frames_since_update = 0
        
    def add_recognition(self, recognition: Optional[Dict], history_size: int = 3):
        """Add a recognition result and update stable identity"""
        self.recognition_history.append({
            'timestamp': time.time(),
            'result': recognition
        })
        
        # Keep only recent history (smaller for speed)
        if len(self.recognition_history) > history_size:
            self.recognition_history.pop(0)
        
        # Update stable identity through voting
        self._update_stable_identity()
    
    def _update_stable_identity(self):
        """Determine stable identity from recognition history using voting"""
        if not self.recognition_history:
            self.stable_identity = None
            return
        
        # Count valid recognitions
        valid_recognitions = [
            h['result'] for h in self.recognition_history 
            if h['result'] is not None and h['result'].get('recognized')
        ]
        
        if not valid_recognitions:
            self.stable_identity = None
            self.consecutive_recognitions = 0
            return
        
        # Count votes for each user_id
        votes = {}
        for rec in valid_recognitions:
            user_id = rec.get('user_id')
            if user_id:
                if user_id not in votes:
                    votes[user_id] = {
                        'count': 0,
                        'total_confidence': 0.0,
                        'data': rec
                    }
                votes[user_id]['count'] += 1
                votes[user_id]['total_confidence'] += rec.get('confidence', 0)
        
        # Get winner (most votes)
        if votes:
            winner_id = max(votes.keys(), key=lambda k: votes[k]['count'])
            winner_data = votes[winner_id]
            
            # Fast decision: require just 1 good recognition
            min_votes = 1  # Very lenient for speed
            if winner_data['count'] >= min_votes:
                avg_confidence = winner_data['total_confidence'] / winner_data['count']
                self.stable_identity = {
                    'user_id': winner_id,
                    'name': winner_data['data']['name'],
                    'confidence': avg_confidence,
                    'vote_count': winner_data['count']
                }
                self.consecutive_recognitions += 1
            else:
                self.stable_identity = None
                self.consecutive_recognitions = 0
        else:
            self.stable_identity = None
            self.consecutive_recognitions = 0
    
    def get_age(self) -> float:
        """Get the age of this track in seconds"""
        return time.time() - self.first_seen


class LiveTrackingService:
    """Service for real-time face tracking and recognition with IoU-based tracking"""
    
    def __init__(self, face_service: FaceRecognitionService):
        """
        Initialize live tracking service
        
        Parameters:
        - face_service: Face recognition service instance
        """
        self.face_service = face_service
        
        # Initialize face detector with optimized parameters
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Frame processing settings
        self.frame_counter = 0
        self.process_every_n_frames = 5  # Run recognition every 5 frames for better performance
        
        # Track management
        self.tracks: Dict[int, FaceTrack] = {}
        self.next_track_id = 1
        self.track_timeout = 0.5  # Remove tracks after 0.5 seconds (faster cleanup)
        self.iou_threshold = 0.4  # Higher threshold = more aggressive track updates
        
        # Recognition settings
        self.recognition_history_size = 3  # Smaller history for faster decisions
        self.min_confidence = 0.25  # Minimum confidence to consider valid (more lenient for live tracking)
        
        print("[LiveTracking] Service initialized")
    
    def _calculate_iou(self, bbox1: Tuple, bbox2: Tuple) -> float:
        """
        Calculate Intersection over Union (IoU) between two bounding boxes
        
        Parameters:
        - bbox1, bbox2: Tuples of (x, y, w, h)
        
        Returns:
        - IoU score (0-1)
        """
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2
        
        # Calculate intersection rectangle
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        
        # Calculate union
        bbox1_area = w1 * h1
        bbox2_area = w2 * h2
        union_area = bbox1_area + bbox2_area - intersection_area
        
        return intersection_area / union_area if union_area > 0 else 0.0
    
    def _match_detections_to_tracks(self, detections: List[Tuple]) -> Dict[int, int]:
        """
        Match new detections to existing tracks using IoU
        
        Parameters:
        - detections: List of bounding boxes (x, y, w, h)
        
        Returns:
        - Dictionary mapping detection_idx -> track_id
        """
        current_time = time.time()
        matches = {}
        
        # Remove old tracks (aggressive cleanup for no ghost boxes)
        tracks_to_remove = []
        for track_id, track in self.tracks.items():
            if current_time - track.last_seen > self.track_timeout:
                tracks_to_remove.append(track_id)
        
        for track_id in tracks_to_remove:
            del self.tracks[track_id]
        
        # Match detections to existing tracks
        used_tracks = set()
        
        for det_idx, detection in enumerate(detections):
            best_iou = self.iou_threshold
            best_track_id = None
            
            # Find best matching track
            for track_id, track in self.tracks.items():
                if track_id in used_tracks:
                    continue
                
                iou = self._calculate_iou(detection, track.bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_track_id = track_id
            
            if best_track_id is not None:
                # Match found - update existing track
                matches[det_idx] = best_track_id
                used_tracks.add(best_track_id)
                self.tracks[best_track_id].update_bbox(detection)
            else:
                # No match - create new track
                new_track_id = self.next_track_id
                self.next_track_id += 1
                matches[det_idx] = new_track_id
                self.tracks[new_track_id] = FaceTrack(new_track_id, detection)
                print(f"[LiveTracking] Created new track {new_track_id}")
        
        return matches
    
    def detect_faces(self, img_array: np.ndarray) -> List[Tuple]:
        """
        Detect faces in an image using Haar Cascade with optimized parameters
        
        Parameters:
        - img_array: Image as numpy array
        
        Returns:
        - List of face bounding boxes (x, y, w, h)
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Apply histogram equalization for better detection in varying lighting
            gray = cv2.equalizeHist(gray)
            
            # Detect faces with balanced parameters for speed and accuracy
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.2,  # Higher = faster detection
                minNeighbors=5,  # Balanced for speed
                minSize=(50, 50),  # Slightly smaller for better detection
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            return faces
        except Exception as e:
            print(f"[LiveTracking] Error detecting faces: {e}")
            return []
    
    def recognize_face(self, face_img: np.ndarray, track_id: int) -> Optional[Dict]:
        """
        Recognize a face from image region
        
        Parameters:
        - face_img: Face region as numpy array
        - track_id: Track identifier for this face
        
        Returns:
        - Recognition result or None
        """
        try:
            # Check if face image is valid
            if face_img.size == 0 or face_img.shape[0] < 20 or face_img.shape[1] < 20:
                return None
            
            # Resize image for faster processing (max 200x200)
            pil_img = Image.fromarray(face_img)
            if pil_img.width > 200 or pil_img.height > 200:
                pil_img.thumbnail((200, 200), Image.Resampling.LANCZOS)
            
            # Save face temporarily with lower quality for speed
            temp_path = f"temp/track_{track_id}_{int(time.time() * 1000)}.jpg"
            pil_img.save(temp_path, quality=85, optimize=True)
            
            try:
                # Recognize face (with lenient detection for live tracking)
                recognition_result = self.face_service.recognize_user(
                    temp_path, 
                    enforce_detection=False
                )
                
                # Return result if recognized with sufficient confidence
                if recognition_result.get('recognized'):
                    confidence = recognition_result.get('confidence', 0)
                    if confidence >= self.min_confidence:
                        return {
                            'recognized': True,
                            'user_id': recognition_result['user_id'],
                            'name': recognition_result['name'],
                            'confidence': confidence,
                            'distance': recognition_result.get('distance', 0)
                        }
                
                return None
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
        except Exception as e:
            print(f"[LiveTracking] Error recognizing face for track {track_id}: {e}")
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
            
            # Convert bytes to image
            image = Image.open(BytesIO(frame_bytes))
            img_array = np.array(image)
            
            # Detect faces
            detections = self.detect_faces(img_array)
            
            # Match detections to tracks
            detection_to_track = self._match_detections_to_tracks(detections)
            
            # Determine if we should run recognition this frame
            should_recognize = (self.frame_counter % self.process_every_n_frames) == 0
            
            # Process each detection
            for det_idx, bbox in enumerate(detections):
                track_id = detection_to_track[det_idx]
                track = self.tracks[track_id]
                
                # Run recognition if it's time
                if should_recognize:
                    # Extract face region with moderate padding
                    x, y, w, h = bbox
                    padding = int(max(w, h) * 0.2)  # 20% padding
                    
                    y1 = max(0, y - padding)
                    y2 = min(img_array.shape[0], y + h + padding)
                    x1 = max(0, x - padding)
                    x2 = min(img_array.shape[1], x + w + padding)
                    
                    face_img = img_array[y1:y2, x1:x2]
                    
                    # Recognize face (skip very small faces for speed)
                    if face_img.shape[0] >= 30 and face_img.shape[1] >= 30:
                        recognition = self.recognize_face(face_img, track_id)
                        track.add_recognition(recognition, self.recognition_history_size)
            
            # Build results from tracks
            recognitions = []
            for track_id, track in self.tracks.items():
                x, y, w, h = track.bbox
                
                face_data = {
                    'face_id': f'Track_{track_id:02d}',
                    'bbox': {
                        'x': int(x),
                        'y': int(y),
                        'width': int(w),
                        'height': int(h)
                    },
                    'age': round(track.get_age(), 2),
                    'hits': len(track.recognition_history)
                }
                
                # Use stable identity if available
                if track.stable_identity:
                    face_data['recognized'] = True
                    face_data['user_id'] = track.stable_identity['user_id']
                    face_data['name'] = track.stable_identity['name']
                    face_data['confidence'] = track.stable_identity['confidence']
                else:
                    face_data['recognized'] = False
                    face_data['name'] = 'Unknown'
                    face_data['confidence'] = 0.0
                
                recognitions.append(face_data)
            
            return {
                'success': True,
                'frame_number': self.frame_counter,
                'faces_detected': len(detections),
                'faces_tracked': len(self.tracks),
                'recognitions': recognitions
            }
            
        except Exception as e:
            print(f"[LiveTracking] Error processing frame: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'frame_number': self.frame_counter,
                'faces_detected': 0,
                'faces_tracked': 0,
                'recognitions': []
            }
