import { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { Camera, X, RefreshCw } from 'lucide-react';
import { Alert, AlertDescription } from './ui/alert';

interface CameraCaptureProps {
  onCapture: (file: File) => void;
  onClose: () => void;
}

export function CameraCapture({ onCapture, onClose }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string>('');
  const [isCameraReady, setIsCameraReady] = useState(false);

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
    };
  }, []);

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user',
        },
        audio: false,
      });

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        setStream(mediaStream);
        setIsCameraReady(true);
        setError('');
      }
    } catch (err) {
      setError(
        'Unable to access camera. Please ensure you have granted camera permissions.'
      );
      console.error('Camera access error:', err);
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsCameraReady(false);
  };

  const capturePhoto = () => {
    if (!videoRef.current) return;

    const video = videoRef.current;
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.drawImage(video, 0, 0);

    canvas.toBlob((blob) => {
      if (!blob) return;

      const file = new File([blob], `camera-capture-${Date.now()}.jpg`, {
        type: 'image/jpeg',
      });

      onCapture(file);
      stopCamera();
      onClose();
    }, 'image/jpeg', 0.95);
  };

  const retryCamera = () => {
    stopCamera();
    setError('');
    startCamera();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
      <div className="bg-background rounded-lg shadow-lg max-w-2xl w-full overflow-hidden">
        <div className="p-4 border-b flex items-center justify-between">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Camera className="h-5 w-5" />
            Camera Capture
          </h3>
          <Button variant="ghost" size="icon" onClick={() => {
            stopCamera();
            onClose();
          }}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="p-6">
          {error ? (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>
                {error}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={retryCamera}
                  className="mt-2"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Try Again
                </Button>
              </AlertDescription>
            </Alert>
          ) : (
            <>
              <div className="relative bg-black rounded-lg overflow-hidden mb-4">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  muted
                  className="w-full h-auto"
                  style={{ maxHeight: '500px' }}
                />
                {!isCameraReady && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-white text-center">
                      <Camera className="h-12 w-12 mx-auto mb-2 animate-pulse" />
                      <p>Starting camera...</p>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex gap-3">
                <Button
                  onClick={capturePhoto}
                  disabled={!isCameraReady}
                  className="flex-1"
                >
                  <Camera className="mr-2 h-4 w-4" />
                  Capture Photo
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    stopCamera();
                    onClose();
                  }}
                >
                  Cancel
                </Button>
              </div>

              <p className="text-sm text-muted-foreground mt-4 text-center">
                Position your face in the center and click "Capture Photo"
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

