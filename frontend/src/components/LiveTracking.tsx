import { useEffect, useRef, useState, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Video, VideoOff, Activity, Users, XCircle, CheckCircle } from 'lucide-react';

interface Recognition {
  face_id: string;  // ByteTrack ID (Face_01, Face_02, etc.)
  user_id?: string;
  name: string;
  confidence: number;
  recognized: boolean;
  bbox: { x: number; y: number; width: number; height: number };
  age?: number;  // Frames tracked
  hits?: number;  // Detection count
}

interface FrameResult {
  success: boolean;
  frame_number: number;
  faces_detected: number;
  faces_tracked: number;
  recognitions: Recognition[];
  using_insightface?: boolean;
}

export function LiveTracking() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const sendIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const [isStreaming, setIsStreaming] = useState(false);
  const [recognitions, setRecognitions] = useState<Recognition[]>([]);
  const [error, setError] = useState<string>('');
  const [fps, setFps] = useState(0);
  const [facesDetected, setFacesDetected] = useState(0);
  const [facesTracked, setFacesTracked] = useState(0);
  const [frameNumber, setFrameNumber] = useState(0);
  const [usingInsightFace, setUsingInsightFace] = useState(false);

  const fpsCounterRef = useRef({ frames: 0, lastTime: Date.now() });

  useEffect(() => {
    return () => {
      stopTracking();
    };
  }, []);

  const drawBoundingBoxes = useCallback((recognitions: Recognition[]) => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size to match video
    if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    recognitions.forEach((rec) => {
      const { x, y, width, height } = rec.bbox;
      
      // Choose color based on recognition status
      const color = rec.recognized ? '#00ff00' : '#ff6b6b';
      const bgColor = rec.recognized ? 'rgba(0, 255, 0, 0.2)' : 'rgba(255, 107, 107, 0.2)';

      // Draw background rectangle
      ctx.fillStyle = bgColor;
      ctx.fillRect(x, y, width, height);

      // Draw bounding box
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.strokeRect(x, y, width, height);

      // Draw labels with track ID
      const trackLabel = rec.face_id;
      const identityLabel = rec.recognized 
        ? `${rec.name} (${(rec.confidence * 100).toFixed(1)}%)`
        : 'Unknown';
      
      ctx.font = 'bold 14px Arial';
      const trackWidth = ctx.measureText(trackLabel).width;
      const identityWidth = ctx.measureText(identityLabel).width;
      const maxWidth = Math.max(trackWidth, identityWidth);
      
      // Draw track ID background (top)
      ctx.fillStyle = rec.recognized ? '#0066ff' : '#666666';
      ctx.fillRect(x, y - 55, maxWidth + 10, 25);
      
      // Draw track ID text
      ctx.fillStyle = '#fff';
      ctx.fillText(trackLabel, x + 5, y - 38);
      
      // Draw identity background (below track ID)
      ctx.fillStyle = color;
      ctx.fillRect(x, y - 30, maxWidth + 10, 30);

      // Draw identity text
      ctx.fillStyle = '#000';
      ctx.font = '16px Arial';
      ctx.fillText(identityLabel, x + 5, y - 10);
    });
  }, []);

  const startTracking = async () => {
    try {
      setError('');
      
      // Start camera
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user',
        },
        audio: false,
      });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }

      // Connect WebSocket (dynamic URL for mobile support)
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/track`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsStreaming(true);
        startSendingFrames();
      };

      ws.onmessage = (event) => {
        try {
          const data: FrameResult = JSON.parse(event.data);
          
          if (data.success) {
            setRecognitions(data.recognitions || []);
            setFacesDetected(data.faces_detected || 0);
            setFacesTracked(data.faces_tracked || 0);
            setFrameNumber(data.frame_number || 0);
            setUsingInsightFace(data.using_insightface || false);
            drawBoundingBoxes(data.recognitions || []);
            
            // Update FPS counter
            fpsCounterRef.current.frames++;
            const now = Date.now();
            const elapsed = now - fpsCounterRef.current.lastTime;
            if (elapsed >= 1000) {
              setFps(fpsCounterRef.current.frames);
              fpsCounterRef.current.frames = 0;
              fpsCounterRef.current.lastTime = now;
            }
          }
        } catch (err) {
          console.error('Error parsing message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection error');
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
        setIsStreaming(false);
      };

    } catch (error) {
      setError(
        'Unable to access camera. Please ensure you have granted camera permissions.'
      );
      console.error('Camera access error:', error);
    }
  };

  const startSendingFrames = () => {
    const video = videoRef.current;
    if (!video) return;

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const sendFrame = () => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN || !video) {
        return;
      }

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0);

      canvas.toBlob(
        (blob) => {
          if (blob && wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(blob);
          }
        },
        'image/jpeg',
        0.8
      );
    };

    // Send frames at ~10 FPS
    sendIntervalRef.current = setInterval(sendFrame, 100);
  };

  const stopTracking = () => {
    // Stop sending frames
    if (sendIntervalRef.current) {
      clearInterval(sendIntervalRef.current);
      sendIntervalRef.current = null;
    }

    // Stop camera
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsStreaming(false);
    setRecognitions([]);
    setFps(0);
    setFacesDetected(0);
    setFacesTracked(0);
    setFrameNumber(0);
    setUsingInsightFace(false);
    setError('');
  };

  const recognizedUsers = recognitions.filter((r) => r.recognized);
  const unknownFaces = recognitions.filter((r) => !r.recognized);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-6 w-6" />
          Live Face Tracking
        </CardTitle>
        <CardDescription>
          Real-time face detection and recognition from your camera
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <XCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Video Display */}
        <div className="relative bg-black rounded-lg overflow-hidden">
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-auto"
            style={{ maxHeight: '500px' }}
          />
          <canvas
            ref={canvasRef}
            className="absolute top-0 left-0 w-full h-full pointer-events-none"
          />
          
          {/* Stats Overlay */}
          {isStreaming && (
            <div className="absolute top-4 right-4 bg-black/80 text-white px-3 py-2 rounded-lg text-xs space-y-1">
              <div className="font-bold text-green-400">
                {usingInsightFace ? '🧠 SCRFD + ArcFace' : '📹 Haar + Facenet'}
              </div>
              <div>FPS: {fps}</div>
              <div>Detected: {facesDetected}</div>
              <div>Tracked: {facesTracked}</div>
              <div>Frame: {frameNumber}</div>
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="flex gap-3">
          {!isStreaming ? (
            <Button onClick={startTracking} className="flex-1">
              <Video className="mr-2 h-4 w-4" />
              Start Tracking
            </Button>
          ) : (
            <Button onClick={stopTracking} variant="destructive" className="flex-1">
              <VideoOff className="mr-2 h-4 w-4" />
              Stop Tracking
            </Button>
          )}
        </div>

        {/* Recognition Results */}
        {isStreaming && recognitions.length > 0 && (
          <div className="space-y-3">
            {recognizedUsers.length > 0 && (
              <div>
                <h3 className="font-semibold mb-2 flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                  Recognized Users
                </h3>
                <div className="flex flex-wrap gap-2">
                  {recognizedUsers.map((rec, i) => (
                    <Badge key={i} variant="success" className="text-sm">
                      {rec.face_id}: {rec.name} - {(rec.confidence * 100).toFixed(1)}%
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {unknownFaces.length > 0 && (
              <div>
                <h3 className="font-semibold mb-2 flex items-center gap-2">
                  <Users className="h-4 w-4 text-muted-foreground" />
                  Unknown Faces
                </h3>
                <Badge variant="secondary">
                  {unknownFaces.length} unrecognized face{unknownFaces.length > 1 ? 's' : ''}
                </Badge>
              </div>
            )}
          </div>
        )}

        {/* Instructions */}
        {!isStreaming && !error && (
          <Alert>
            <Activity className="h-4 w-4" />
            <AlertDescription>
              Click "Start Tracking" to begin real-time face recognition. Make sure your camera is working and you have registered users in the system.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}

