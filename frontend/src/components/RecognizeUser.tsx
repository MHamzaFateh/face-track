import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import { Badge } from './ui/badge';
import { Scan, Loader2, CheckCircle2, XCircle, Info, Camera } from 'lucide-react';
import { CameraCapture } from './CameraCapture';

interface RecognizeResult {
  success: boolean;
  recognized: boolean;
  message: string;
  data?: {
    recognized: boolean;
    user_id?: string;
    name?: string;
    distance?: number;
    confidence?: number;
    threshold?: number;
    closest_distance?: number;
  };
}

export function RecognizeUser() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RecognizeResult | null>(null);
  const [showCamera, setShowCamera] = useState(false);
  const [isFromCamera, setIsFromCamera] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setIsFromCamera(false);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(selectedFile);
    }
  };

  const handleCameraCapture = (capturedFile: File) => {
    setFile(capturedFile);
    setIsFromCamera(true);
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreview(reader.result as string);
    };
    reader.readAsDataURL(capturedFile);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file) {
      setResult({
        success: false,
        recognized: false,
        message: 'Please upload an image or capture a photo with camera',
      });
      return;
    }

    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/recognize', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        // API returns user details directly
        setResult({
          success: true,
          recognized: data.recognized,
          message: data.recognized 
            ? `User recognized: ${data.name}` 
            : 'No matching user found in database',
          data: data
        });
      } else {
        setResult({ 
          success: false, 
          recognized: false,
          message: data.detail || 'Recognition failed' 
        });
      }
    } catch (error) {
      setResult({ 
        success: false, 
        recognized: false,
        message: `Error: ${error instanceof Error ? error.message : 'Unknown error'}` 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Scan className="h-6 w-6" />
          Recognize User
        </CardTitle>
        <CardDescription>
          Recognize a user from their face image
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="recognize-file">Face Image</Label>
            <div className="flex gap-2">
              <Input
                id="recognize-file"
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="flex-1"
                required={!file}
              />
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowCamera(true)}
                className="shrink-0"
              >
                <Camera className="h-4 w-4 mr-2" />
                Camera
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Upload an image or use your camera to capture a photo
            </p>
            {isFromCamera && file && (
              <p className="text-xs text-green-600 flex items-center gap-1">
                <Camera className="h-3 w-3" />
                Photo captured from camera
              </p>
            )}
          </div>

          {preview && (
            <div className="flex justify-center">
              <img
                src={preview}
                alt="Preview"
                className="max-h-64 rounded-lg border shadow-sm"
              />
            </div>
          )}

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              'Recognize User'
            )}
          </Button>
        </form>

        {showCamera && (
          <CameraCapture
            onCapture={handleCameraCapture}
            onClose={() => setShowCamera(false)}
          />
        )}

        {result && (
          <Alert 
            variant={result.recognized ? 'success' : result.success ? 'default' : 'destructive'} 
            className="mt-4"
          >
            {result.recognized ? (
              <CheckCircle2 className="h-4 w-4" />
            ) : result.success ? (
              <Info className="h-4 w-4" />
            ) : (
              <XCircle className="h-4 w-4" />
            )}
            <AlertTitle>
              {result.recognized ? 'User Recognized!' : result.success ? 'Not Recognized' : 'Error'}
            </AlertTitle>
            <AlertDescription>
              {result.data && result.data.recognized ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Badge className="bg-green-600">Match Found</Badge>
                  </div>
                  <div className="bg-background/50 rounded-lg p-4 space-y-2">
                    <div className="flex items-baseline gap-2">
                      <span className="text-sm text-muted-foreground">Name:</span>
                      <span className="text-lg font-semibold">{result.data.name}</span>
                    </div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-sm text-muted-foreground">User ID:</span>
                      <span className="font-medium">{result.data.user_id}</span>
                    </div>
                    {result.data.confidence !== undefined && (
                      <div className="flex items-baseline gap-2">
                        <span className="text-sm text-muted-foreground">Confidence:</span>
                        <span className="font-medium text-green-600">
                          {((1 - (result.data.distance || 0)) * 100).toFixed(1)}%
                        </span>
                      </div>
                    )}
                    {result.data.distance !== undefined && (
                      <div className="flex items-baseline gap-2">
                        <span className="text-sm text-muted-foreground">Distance:</span>
                        <span className="text-sm font-mono">{result.data.distance.toFixed(4)}</span>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div>
                  {result.message}
                  {result.data && !result.data.recognized && (
                    <div className="mt-3 text-sm text-muted-foreground">
                      <p>No matching user found in the database.</p>
                      {result.data.distance !== undefined && (
                        <p className="mt-1">Distance: {result.data.distance.toFixed(4)}</p>
                      )}
                    </div>
                  )}
                </div>
              )}
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}

