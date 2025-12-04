import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import { UserPlus, Loader2, CheckCircle2, XCircle, Camera, Upload } from 'lucide-react';
import { CameraCapture } from './CameraCapture';

interface RegisterResult {
  success: boolean;
  message: string;
  data?: {
    user_id: string;
    name: string;
    registered_at: string;
    embedding_size: number;
  };
}

export function RegisterUser({ onUserRegistered }: { onUserRegistered: () => void }) {
  const [userId, setUserId] = useState('');
  const [name, setName] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RegisterResult | null>(null);
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
        message: 'Please upload an image or capture a photo with camera',
      });
      return;
    }

    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append('user_id', userId);
    formData.append('name', name);
    formData.append('file', file, file.name);

    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setResult({ success: true, ...data });
        setUserId('');
        setName('');
        setFile(null);
        setPreview('');
        setIsFromCamera(false);
        onUserRegistered();
        // Reset file input
        const fileInput = document.getElementById('register-file') as HTMLInputElement;
        if (fileInput) fileInput.value = '';
      } else {
        setResult({ 
          success: false, 
          message: data.detail || 'Registration failed' 
        });
      }
    } catch (error) {
      setResult({ 
        success: false, 
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
          <UserPlus className="h-6 w-6" />
          Register New User
        </CardTitle>
        <CardDescription>
          Register a new user with their face image
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="user-id">User ID</Label>
            <Input
              id="user-id"
              placeholder="e.g., user001"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="user-name">Full Name</Label>
            <Input
              id="user-name"
              placeholder="e.g., John Doe"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="register-file">Face Image</Label>
            <div className="flex gap-2">
              <Input
                id="register-file"
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
                Processing...
              </>
            ) : (
              'Register User'
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
          <Alert variant={result.success ? 'success' : 'destructive'} className="mt-4">
            {result.success ? (
              <CheckCircle2 className="h-4 w-4" />
            ) : (
              <XCircle className="h-4 w-4" />
            )}
            <AlertTitle>
              {result.success ? 'Success!' : 'Error'}
            </AlertTitle>
            <AlertDescription>
              {result.message}
              {result.data && (
                <div className="mt-2 text-xs">
                  <p>User ID: {result.data.user_id}</p>
                  <p>Name: {result.data.name}</p>
                  <p>Embedding Size: {result.data.embedding_size}</p>
                </div>
              )}
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}

