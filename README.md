# 🎭 Face Recognition System

A modern, full-stack face recognition system with AI-powered facial recognition using DeepFace and a beautiful React frontend built with shadcn/ui.

![Tech Stack](https://img.shields.io/badge/React-18-blue)
![Tech Stack](https://img.shields.io/badge/FastAPI-Latest-green)
![Tech Stack](https://img.shields.io/badge/TypeScript-5.9-blue)
![Tech Stack](https://img.shields.io/badge/shadcn%2Fui-Latest-black)

## ✨ Features

- 🤖 **AI-Powered Recognition** - Uses DeepFace with Facenet512 (512-dimensional embeddings)
- 🎯 **ByteTrack Multi-Face Tracking** - Assigns unique IDs (Face_01, Face_02...) and tracks faces across frames
- 🎨 **Modern UI** - Beautiful interface built with shadcn/ui and Tailwind CSS
- 📷 **Live Camera Capture** - Take photos directly from your webcam
- 🎥 **Real-Time Face Tracking** - Continuous face detection and recognition via WebSocket
- 🔄 **No Duplicate Recognition** - Each face is recognized once and remembered
- 🛡️ **Duplicate Prevention** - Prevents same person from registering multiple times
- 👤 **User Registration** - Register users with their face images or camera
- 🔍 **Face Recognition** - Recognize and verify registered users
- 👥 **User Management** - View, manage, and delete users
- 📊 **Confidence Scores** - Get detailed recognition metrics
- 🌐 **REST API** - Full-featured API for integration
- ⚡ **Real-time Status** - Live server status monitoring

## 🏗️ Architecture

```
deep-system/
├── backend/                    # FastAPI Backend
│   ├── main.py                # API endpoints & WebSocket
│   ├── config.py              # Configuration
│   ├── services/              # Business logic
│   │   ├── face_recognition_service.py    # DeepFace integration
│   │   ├── byte_tracker.py                # ByteTrack algorithm
│   │   ├── advanced_tracking_service.py   # SCRFD + ByteTrack + ArcFace
│   │   └── live_tracking_service.py       # WebSocket streaming
│   ├── models/                # Data models
│   │   └── user.py
│   └── data/                  # Storage
│       ├── users/             # User database (JSON)
│       └── faces/             # Face images & embeddings
│
└── frontend/                   # React Frontend
    ├── src/
    │   ├── components/
    │   │   ├── ui/            # shadcn/ui components
    │   │   ├── RegisterUser.tsx
    │   │   ├── RecognizeUser.tsx
    │   │   ├── UsersList.tsx
    │   │   ├── CameraCapture.tsx
    │   │   └── LiveTracking.tsx
    │   ├── App.tsx
    │   └── main.tsx
    └── package.json
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 18+** (for frontend)
- pip (Python package manager)
- npm (Node package manager)

### 1. Backend Setup

```bash
# Navigate to backend
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start the backend server
python main.py
```

Backend will run at: **http://localhost:8003**

### 2. Frontend Setup

```bash
# Navigate to frontend (from project root)
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will run at: **http://localhost:5173**

### 3. Access the Application

Open your browser and go to: **http://localhost:5173**

The frontend will automatically proxy API calls to the backend.

## 📸 Screenshots & Usage

### Register a New User

1. Navigate to the **Register** tab
2. Enter a User ID (e.g., "john001")
3. Enter the user's full name
4. Upload a clear face image
5. Click **Register User**

### Recognize a User

1. Navigate to the **Recognize** tab
2. Upload a face image
3. Click **Recognize User**
4. View results with confidence score and user details

### Manage Users

- View all registered users in the **Registered Users** card
- Click the trash icon to delete a user
- Click refresh to reload the user list

## 🛠️ Technology Stack

### Backend

- **FastAPI** - Modern Python web framework
- **DeepFace** - Deep learning facial recognition
- **Facenet512** - 512-dimensional face embeddings
- **TensorFlow** - Deep learning backend
- **OpenCV** - Image processing
- **Uvicorn** - ASGI server

### Frontend

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool & dev server
- **shadcn/ui** - Beautiful UI components
- **Tailwind CSS** - Utility-first CSS
- **Radix UI** - Accessible component primitives
- **Lucide React** - Icon library

## 🎨 UI Components

The frontend uses shadcn/ui components for a consistent, accessible design:

- **Button** - Interactive buttons with variants
- **Card** - Content containers
- **Input** - Form inputs with labels
- **Tabs** - Tabbed navigation
- **Alert** - Status messages
- **Badge** - Status indicators
- **Separator** - Visual dividers

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/api/health` | Health check |
| POST | `/api/register` | Register new user |
| POST | `/api/recognize` | Recognize user |
| GET | `/api/users` | Get all users |
| GET | `/api/users/{id}` | Get user by ID |
| DELETE | `/api/users/{id}` | Delete user |

Full API documentation: **http://localhost:8003/docs**

## ⚙️ Configuration

### Backend Configuration

Edit `backend/config.py`:

```python
FACE_MODEL = "Facenet512"           # Recognition model
DISTANCE_METRIC = "cosine"          # Distance calculation
RECOGNITION_THRESHOLD = 0.4         # Recognition threshold
API_PORT = 8003                     # Server port
```

### Frontend Configuration

Edit `frontend/vite.config.ts`:

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8003',  // Backend URL
      changeOrigin: true,
    },
  },
}
```

## 🎯 How It Works

1. **Registration**:
   - User uploads a face image
   - DeepFace detects the face
   - Facenet512 generates a 512-dimensional embedding
   - Embedding and metadata stored

2. **Recognition**:
   - User uploads a face image
   - System generates embedding for the image
   - Compares against all stored embeddings using cosine distance
   - Returns match if distance < threshold (0.4)

## 📝 Best Practices

### Image Quality

✅ **Good:**
- Clear, well-lit images
- Front-facing photos
- Face occupies 30-50% of image
- Natural lighting

❌ **Bad:**
- Blurry or dark images
- Side-facing or angled
- Multiple faces
- Harsh shadows

### Recognition Accuracy

- Use similar lighting for registration and recognition
- Keep face angle consistent
- Adjust threshold in config if needed:
  - Lower (0.3) = more strict
  - Higher (0.5) = more lenient

## 🔧 Troubleshooting

### Backend Issues

**Server won't start:**
```bash
# Check if port 8003 is available
# Install dependencies
pip install -r requirements.txt
```

**No face detected:**
- Ensure face is clearly visible
- Check image quality
- Try different angle

### Frontend Issues

**Can't connect to backend:**
- Ensure backend is running on port 8003
- Check browser console for errors

**Build errors:**
```bash
# Clear node modules and reinstall
rm -rf node_modules
npm install
```

## 🚀 Production Deployment

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8003
```

### Frontend

```bash
cd frontend
npm run build
# Deploy the 'dist' folder to your hosting service
```

## 🔐 Security Considerations

⚠️ **Important**: This is a development version. For production:

- Add authentication and authorization
- Implement rate limiting
- Add input validation and sanitization
- Use HTTPS
- Store data securely (consider database)
- Add logging and monitoring
- Implement CORS properly
- Add API key authentication

## 📚 Documentation

- **Backend README**: [backend/README.md](backend/README.md)
- **Frontend README**: [frontend/README.md](frontend/README.md)
- **API Examples**: [backend/API_EXAMPLES.md](backend/API_EXAMPLES.md)
- **Quick Start**: [backend/QUICK_START.md](backend/QUICK_START.md)
- **Live Tracking Guide**: [LIVE_TRACKING.md](LIVE_TRACKING.md) ⭐
- **Camera Feature**: [CAMERA_FEATURE.md](CAMERA_FEATURE.md)
- **Duplicate Prevention**: [DUPLICATE_PREVENTION.md](DUPLICATE_PREVENTION.md) ⭐ **NEW!**

## 🤝 Contributing

This is an educational project. Feel free to fork and customize!

## 📄 License

Educational and development purposes.

## 🙏 Acknowledgments

- **DeepFace** - Face recognition library
- **shadcn/ui** - Beautiful UI components
- **FastAPI** - Modern Python web framework
- **Radix UI** - Accessible components

---

**Built with ❤️ using React, TypeScript, shadcn/ui, FastAPI, and DeepFace**

