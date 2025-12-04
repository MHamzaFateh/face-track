"""
ByteTrack - Multi-Object Tracking for Faces
Assigns unique IDs to faces and tracks them across frames
"""
import numpy as np
from typing import List, Dict, Tuple
from collections import OrderedDict


class TrackedFace:
    """Represents a tracked face with unique ID"""
    
    def __init__(self, face_id: int, bbox: Tuple[int, int, int, int], embedding: np.ndarray = None):
        self.face_id = face_id
        self.bbox = bbox  # (x, y, w, h)
        self.embedding = embedding
        self.age = 0  # How many frames this face has been tracked
        self.hits = 0  # Number of successful detections
        self.recognized = False
        self.user_id = None
        self.name = "Unknown"
        self.confidence = 0.0
        self.time_since_update = 0
    
    def update(self, bbox: Tuple[int, int, int, int], embedding: np.ndarray = None):
        """Update face position and embedding"""
        self.bbox = bbox
        if embedding is not None:
            self.embedding = embedding
        self.hits += 1
        self.time_since_update = 0
        self.age += 1
    
    def predict(self):
        """Predict next position (simple: keep current position)"""
        self.age += 1
        self.time_since_update += 1
    
    def get_center(self) -> Tuple[float, float]:
        """Get center point of bounding box"""
        x, y, w, h = self.bbox
        return (x + w/2, y + h/2)


class ByteTracker:
    """
    ByteTrack algorithm for multi-face tracking
    Assigns unique IDs to faces and maintains them across frames
    """
    
    def __init__(self, 
                 max_age: int = 30, 
                 min_hits: int = 3,
                 iou_threshold: float = 0.3):
        """
        Initialize ByteTracker
        
        Parameters:
        - max_age: Maximum frames to keep track without detection
        - min_hits: Minimum hits before considering track confirmed
        - iou_threshold: IoU threshold for matching detections
        """
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.tracks: OrderedDict[int, TrackedFace] = OrderedDict()
        self.next_id = 1
        self.frame_count = 0
    
    def compute_iou(self, bbox1: Tuple[int, int, int, int], 
                    bbox2: Tuple[int, int, int, int]) -> float:
        """
        Compute Intersection over Union (IoU) between two bounding boxes
        
        Parameters:
        - bbox1, bbox2: Bounding boxes as (x, y, w, h)
        
        Returns:
        - IoU score (0.0 to 1.0)
        """
        x1, y1, w1, h1 = bbox1
        x2, y2, w2, h2 = bbox2
        
        # Convert to (x1, y1, x2, y2) format
        box1_x2, box1_y2 = x1 + w1, y1 + h1
        box2_x2, box2_y2 = x2 + w2, y2 + h2
        
        # Compute intersection
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(box1_x2, box2_x2)
        y_bottom = min(box1_y2, box2_y2)
        
        if x_right < x_left or y_bottom < y_top:
            return 0.0
        
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        
        # Compute union
        box1_area = w1 * h1
        box2_area = w2 * h2
        union_area = box1_area + box2_area - intersection_area
        
        if union_area == 0:
            return 0.0
        
        return intersection_area / union_area
    
    def match_detections_to_tracks(self, 
                                   detections: List[Tuple[int, int, int, int]]) -> Tuple[List, List, List]:
        """
        Match current detections to existing tracks using IoU
        
        Returns:
        - matched: List of (track_id, detection_idx) pairs
        - unmatched_detections: List of detection indices
        - unmatched_tracks: List of track IDs
        """
        if len(self.tracks) == 0:
            return [], list(range(len(detections))), []
        
        if len(detections) == 0:
            return [], [], list(self.tracks.keys())
        
        # Compute IoU matrix
        iou_matrix = np.zeros((len(self.tracks), len(detections)))
        
        track_ids = list(self.tracks.keys())
        for t_idx, track_id in enumerate(track_ids):
            track = self.tracks[track_id]
            for d_idx, det_bbox in enumerate(detections):
                iou_matrix[t_idx, d_idx] = self.compute_iou(track.bbox, det_bbox)
        
        # Simple greedy matching (can be improved with Hungarian algorithm)
        matched = []
        unmatched_detections = list(range(len(detections)))
        unmatched_tracks = track_ids.copy()
        
        # Match in order of highest IoU
        while True:
            if iou_matrix.size == 0:
                break
            
            # Find highest IoU
            max_iou = iou_matrix.max()
            if max_iou < self.iou_threshold:
                break
            
            max_idx = np.unravel_index(iou_matrix.argmax(), iou_matrix.shape)
            t_idx, d_idx = max_idx
            
            matched.append((track_ids[t_idx], unmatched_detections[d_idx]))
            
            # Remove matched from unmatched lists
            if track_ids[t_idx] in unmatched_tracks:
                unmatched_tracks.remove(track_ids[t_idx])
            
            # Set row and column to -1 so they won't be matched again
            iou_matrix[t_idx, :] = -1
            iou_matrix[:, d_idx] = -1
        
        # Clean up unmatched lists
        unmatched_detections = [d for d in unmatched_detections 
                               if not any(d == m[1] for m in matched)]
        
        return matched, unmatched_detections, unmatched_tracks
    
    def update(self, detections: List[Tuple[int, int, int, int]], 
              embeddings: List[np.ndarray] = None) -> List[TrackedFace]:
        """
        Update tracker with new detections
        
        Parameters:
        - detections: List of bounding boxes [(x, y, w, h), ...]
        - embeddings: Optional list of face embeddings
        
        Returns:
        - List of tracked faces with stable IDs
        """
        self.frame_count += 1
        
        # Match detections to existing tracks
        matched, unmatched_dets, unmatched_tracks = self.match_detections_to_tracks(detections)
        
        # Update matched tracks
        for track_id, det_idx in matched:
            bbox = detections[det_idx]
            embedding = embeddings[det_idx] if embeddings else None
            self.tracks[track_id].update(bbox, embedding)
        
        # Create new tracks for unmatched detections
        for det_idx in unmatched_dets:
            bbox = detections[det_idx]
            embedding = embeddings[det_idx] if embeddings else None
            new_track = TrackedFace(self.next_id, bbox, embedding)
            self.tracks[self.next_id] = new_track
            self.next_id += 1
        
        # Remove old tracks that haven't been updated
        tracks_to_remove = []
        for track_id in unmatched_tracks:
            self.tracks[track_id].predict()
            if self.tracks[track_id].time_since_update > self.max_age:
                tracks_to_remove.append(track_id)
        
        for track_id in tracks_to_remove:
            del self.tracks[track_id]
        
        # Return active tracks (with minimum hits)
        active_tracks = [
            track for track in self.tracks.values()
            if track.hits >= self.min_hits or track.age < self.min_hits
        ]
        
        return active_tracks
    
    def get_track_by_id(self, face_id: int) -> TrackedFace:
        """Get a specific tracked face by ID"""
        return self.tracks.get(face_id)
    
    def reset(self):
        """Reset tracker"""
        self.tracks.clear()
        self.next_id = 1
        self.frame_count = 0

