import { useState, useEffect } from 'react';
import { RegisterUser } from './components/RegisterUser';
import { RecognizeUser } from './components/RecognizeUser';
import { UsersList } from './components/UsersList';
import { LiveTracking } from './components/LiveTracking';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Badge } from './components/ui/badge';
import { Activity } from 'lucide-react';

function App() {
  const [serverStatus, setServerStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const checkServerStatus = async () => {
    try {
      const response = await fetch('/api/health');
      if (response.ok) {
        setServerStatus('online');
      } else {
        setServerStatus('offline');
      }
    } catch (error) {
      setServerStatus('offline');
    }
  };

  useEffect(() => {
    checkServerStatus();
    const interval = setInterval(checkServerStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleUserRegistered = () => {
    setRefreshTrigger((prev) => prev + 1);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-pink-50 dark:from-gray-900 dark:via-purple-900 dark:to-blue-900">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl flex items-center justify-center">
              <Activity className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
              Face Recognition System
            </h1>
      </div>
          <p className="text-muted-foreground text-lg">
            Register and recognize faces using AI-powered deep learning
          </p>
          <div className="flex items-center justify-center gap-2 mt-4">
            <Badge 
              variant={serverStatus === 'online' ? 'success' : serverStatus === 'offline' ? 'destructive' : 'secondary'}
            >
              {serverStatus === 'online' ? '● Server Online' : serverStatus === 'offline' ? '● Server Offline' : '● Checking...'}
            </Badge>
          </div>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="register" className="space-y-6">
          <TabsList className="grid w-full max-w-2xl mx-auto grid-cols-3">
            <TabsTrigger value="register">Register</TabsTrigger>
            <TabsTrigger value="recognize">Recognize</TabsTrigger>
            <TabsTrigger value="live">Live Tracking</TabsTrigger>
          </TabsList>

          <TabsContent value="register" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              <RegisterUser onUserRegistered={handleUserRegistered} />
              <UsersList refreshTrigger={refreshTrigger} />
            </div>
          </TabsContent>

          <TabsContent value="recognize" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              <RecognizeUser />
              <UsersList refreshTrigger={refreshTrigger} />
            </div>
          </TabsContent>

          <TabsContent value="live" className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              <LiveTracking />
              <UsersList refreshTrigger={refreshTrigger} />
            </div>
          </TabsContent>
        </Tabs>

        {/* Footer */}
        <div className="mt-12 text-center text-sm text-muted-foreground">
          <p>Built with React, TypeScript, shadcn/ui, and FastAPI</p>
          <p className="mt-1">Powered by DeepFace & Facenet512</p>
        </div>
      </div>
    </div>
  );
}

export default App;
