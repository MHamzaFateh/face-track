import os
import json
import numpy as np
from datetime import datetime
from typing import Optional, Dict, List
from deepface import DeepFace
import cv2
from pathlib import Path


class FaceRecognitionService:
    """Service for face registration and recognition using DeepFace"""
    
    def __init__(self, 
                 model_name: str = "Facenet512",
                 distance_metric: str = "cosine",
                 threshold: float = 0.4):
        """
        Initialize the face recognition service
        
        Parameters:
        - model_name: Model to use for face recognition (Facenet512, VGG-Face, ArcFace, etc.)
        - distance_metric: Distance metric (cosine, euclidean, euclidean_l2)
        - threshold: Recognition threshold (lower = more strict)
        """
        self.model_name = model_name
        self.distance_metric = distance_metric
        self.threshold = threshold
        self.users_db_path = "data/users/users.json"
        self.faces_dir = "data/faces"
        
        # Create directories if they don't exist
        os.makedirs("data/users", exist_ok=True)
        os.makedirs(self.faces_dir, exist_ok=True)
        
        # Initialize users database
        self._init_database()
    
    def _init_database(self):
        """Initialize the users database"""
        if not os.path.exists(self.users_db_path):
            with open(self.users_db_path, 'w') as f:
                json.dump({}, f)
    
    def _load_database(self) -> Dict:
        """Load the users database"""
        try:
            with open(self.users_db_path, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_database(self, db: Dict):
        """Save the users database"""
        with open(self.users_db_path, 'w') as f:
            json.dump(db, f, indent=2)
    
    def _detect_face(self, image_path: str) -> bool:
        """
        Detect if there's a face in the image
        
        Parameters:
        - image_path: Path to the image
        
        Returns:
        - True if face detected, False otherwise
        """
        try:
            # Use DeepFace to extract faces
            faces = DeepFace.extract_faces(
                img_path=image_path,
                detector_backend='opencv',
                enforce_detection=True
            )
            return len(faces) > 0
        except Exception as e:
            raise Exception(f"No face detected in the image: {str(e)}")
    
    def _get_face_embedding(self, image_path: str, enforce_detection: bool = True) -> np.ndarray:
        """
        Get face embedding from image
        
        Parameters:
        - image_path: Path to the image
        - enforce_detection: Whether to strictly enforce face detection (default True)
        
        Returns:
        - Face embedding as numpy array
        """
        try:
            # Get embedding using DeepFace
            embedding_objs = DeepFace.represent(
                img_path=image_path,
                model_name=self.model_name,
                enforce_detection=enforce_detection,
                detector_backend='opencv'
            )
            
            if embedding_objs and len(embedding_objs) > 0:
                embedding = embedding_objs[0]["embedding"]
                return np.array(embedding)
            else:
                raise Exception("Could not extract face embedding")
                
        except Exception as e:
            raise Exception(f"Error extracting face embedding: {str(e)}")
    
    def _calculate_distance(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate distance between two face embeddings
        
        Parameters:
        - embedding1: First embedding
        - embedding2: Second embedding
        
        Returns:
        - Distance value
        """
        if self.distance_metric == 'cosine':
            # Cosine distance
            return 1 - np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
        elif self.distance_metric == 'euclidean':
            # Euclidean distance
            return np.linalg.norm(embedding1 - embedding2)
        elif self.distance_metric == 'euclidean_l2':
            # Normalized euclidean distance
            return np.linalg.norm(embedding1 - embedding2) / np.linalg.norm(embedding1)
        else:
            return np.linalg.norm(embedding1 - embedding2)
    
    def user_exists(self, user_id: str) -> bool:
        """Check if user exists in database"""
        db = self._load_database()
        return user_id in db
    
    def check_face_exists(self, image_path: str, threshold: float = None, enforce_detection: bool = True) -> Dict:
        """
        Check if a face is already registered in the system
        
        Parameters:
        - image_path: Path to the face image to check
        - threshold: Recognition threshold (uses default if None)
        - enforce_detection: Whether to strictly enforce face detection (default True)
        
        Returns:
        - Dictionary with exists status and matching user info
        """
        try:
            if threshold is None:
                threshold = self.threshold
            
            # Get face embedding for the new image
            query_embedding = self._get_face_embedding(image_path, enforce_detection=enforce_detection)
            
            # Load database
            db = self._load_database()
            
            if not db:
                return {
                    "exists": False,
                    "message": "No users registered in the system"
                }
            
            # Compare with all registered users
            for user_id, user_data in db.items():
                # Load user embedding
                embedding_path = user_data["embedding_path"]
                if not os.path.exists(embedding_path):
                    continue
                
                user_embedding = np.load(embedding_path)
                
                # Calculate distance
                distance = self._calculate_distance(query_embedding, user_embedding)
                
                # If distance is below threshold, face already exists
                if distance <= threshold:
                    return {
                        "exists": True,
                        "matched_user_id": user_data["user_id"],
                        "matched_name": user_data["name"],
                        "distance": float(distance),
                        "confidence": float(1 - distance),
                        "threshold": threshold,
                        "message": f"This face is already registered as '{user_data['name']}' (ID: {user_data['user_id']})"
                    }
            
            return {
                "exists": False,
                "message": "Face is not registered in the system"
            }
            
        except Exception as e:
            raise Exception(f"Error checking if face exists: {str(e)}")
    
    def register_user(self, user_id: str, name: str, image_path: str) -> Dict:
        """
        Register a new user with their face
        
        Parameters:
        - user_id: Unique identifier for the user
        - name: Name of the user
        - image_path: Path to the face image
        
        Returns:
        - Registration result
        """
        try:
            print(f"[FaceService] Starting registration for user_id: {user_id}, name: {name}")
            
            # Check if user ID already exists
            if self.user_exists(user_id):
                error = f"User ID '{user_id}' already exists"
                print(f"[FaceService] Error: {error}")
                raise Exception(error)
            
            print(f"[FaceService] User ID is unique, detecting face in image...")
            # Detect face in image
            self._detect_face(image_path)
            print(f"[FaceService] Face detected successfully")
            
            # Check if this face is already registered
            print(f"[FaceService] Checking for duplicate faces...")
            face_check = self.check_face_exists(image_path)
            if face_check["exists"]:
                error = (
                    f"This face is already registered! "
                    f"Existing user: {face_check['matched_name']} (ID: {face_check['matched_user_id']}). "
                    f"Match confidence: {face_check['confidence']*100:.1f}%"
                )
                print(f"[FaceService] Error: {error}")
                raise Exception(error)
            
            print(f"[FaceService] No duplicate face found, extracting embedding...")
            # Get face embedding
            embedding = self._get_face_embedding(image_path)
            print(f"[FaceService] Embedding extracted, size: {len(embedding)}")
            
            # Save face image
            face_image_path = os.path.join(self.faces_dir, f"{user_id}.jpg")
            import shutil
            shutil.copy(image_path, face_image_path)
            
            # Save embedding
            embedding_path = os.path.join(self.faces_dir, f"{user_id}_embedding.npy")
            np.save(embedding_path, embedding)
            
            # Update database
            db = self._load_database()
            db[user_id] = {
                "user_id": user_id,
                "name": name,
                "registered_at": datetime.now().isoformat(),
                "face_image_path": face_image_path,
                "embedding_path": embedding_path,
                "embedding_size": len(embedding)
            }
            self._save_database(db)
            
            return {
                "user_id": user_id,
                "name": name,
                "registered_at": db[user_id]["registered_at"],
                "embedding_size": len(embedding)
            }
            
        except Exception as e:
            raise Exception(f"Registration failed: {str(e)}")
    
    def recognize_by_embedding(self, query_embedding: np.ndarray) -> Dict:
        """
        Recognize a user from face embedding directly
        
        Parameters:
        - query_embedding: Face embedding vector (512-dim)
        
        Returns:
        - Recognition result
        """
        try:
            # Load database
            db = self._load_database()
            
            if not db:
                return {
                    "recognized": False,
                    "message": "No users registered in the system"
                }
            
            # Compare with all registered users
            best_match = None
            min_distance = float('inf')
            
            for user_id, user_data in db.items():
                # Load user embedding
                embedding_path = user_data["embedding_path"]
                if not os.path.exists(embedding_path):
                    continue
                
                user_embedding = np.load(embedding_path)
                
                # Calculate distance
                distance = self._calculate_distance(query_embedding, user_embedding)
                
                if distance < min_distance:
                    min_distance = distance
                    best_match = user_data
            
            # Check if match is within threshold
            if best_match and min_distance <= self.threshold:
                confidence = 1 - min_distance
                return {
                    "recognized": True,
                    "user_id": best_match["user_id"],
                    "name": best_match["name"],
                    "distance": float(min_distance),
                    "confidence": float(confidence),
                    "threshold": self.threshold
                }
            else:
                return {
                    "recognized": False,
                    "message": "No matching user found",
                    "closest_distance": float(min_distance) if min_distance != float('inf') else None,
                    "threshold": self.threshold
                }
                
        except Exception as e:
            raise Exception(f"Recognition by embedding failed: {str(e)}")
    
    def recognize_user(self, image_path: str, enforce_detection: bool = True) -> Dict:
        """
        Recognize a user from their face image
        
        Parameters:
        - image_path: Path to the face image
        - enforce_detection: Whether to strictly enforce face detection (default True)
        
        Returns:
        - Recognition result
        """
        try:
            # Detect face in image only if enforcement is enabled
            if enforce_detection:
                self._detect_face(image_path)
            
            # Get face embedding with optional enforcement
            query_embedding = self._get_face_embedding(image_path, enforce_detection=enforce_detection)
            
            # Load database
            db = self._load_database()
            
            if not db:
                return {
                    "recognized": False,
                    "message": "No users registered in the system"
                }
            
            # Compare with all registered users
            best_match = None
            min_distance = float('inf')
            
            for user_id, user_data in db.items():
                # Load user embedding
                embedding_path = user_data["embedding_path"]
                if not os.path.exists(embedding_path):
                    continue
                
                user_embedding = np.load(embedding_path)
                
                # Calculate distance
                distance = self._calculate_distance(query_embedding, user_embedding)
                
                if distance < min_distance:
                    min_distance = distance
                    best_match = user_data
            
            # Check if match is within threshold
            if best_match and min_distance <= self.threshold:
                confidence = 1 - min_distance  # Convert distance to confidence
                return {
                    "recognized": True,
                    "user_id": best_match["user_id"],
                    "name": best_match["name"],
                    "distance": float(min_distance),
                    "confidence": float(confidence),
                    "threshold": self.threshold
                }
            else:
                return {
                    "recognized": False,
                    "message": "No matching user found",
                    "closest_distance": float(min_distance) if min_distance != float('inf') else None,
                    "threshold": self.threshold
                }
                
        except Exception as e:
            raise Exception(f"Recognition failed: {str(e)}")
    
    def get_all_users(self) -> List[Dict]:
        """Get list of all registered users"""
        db = self._load_database()
        users = []
        for user_id, user_data in db.items():
            users.append({
                "user_id": user_data["user_id"],
                "name": user_data["name"],
                "registered_at": user_data["registered_at"]
            })
        return users
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get details of a specific user"""
        db = self._load_database()
        if user_id in db:
            user_data = db[user_id]
            return {
                "user_id": user_data["user_id"],
                "name": user_data["name"],
                "registered_at": user_data["registered_at"],
                "embedding_size": user_data.get("embedding_size")
            }
        return None
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a registered user"""
        db = self._load_database()
        if user_id not in db:
            return False
        
        user_data = db[user_id]
        
        # Delete face image
        if os.path.exists(user_data["face_image_path"]):
            os.remove(user_data["face_image_path"])
        
        # Delete embedding
        if os.path.exists(user_data["embedding_path"]):
            os.remove(user_data["embedding_path"])
        
        # Remove from database
        del db[user_id]
        self._save_database(db)
        
        return True

