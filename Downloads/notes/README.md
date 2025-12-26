# Eduspace - The Future of Collaborative Learning

Eduspace is a full-stack web application designed to revolutionize collaborative learning. It combines AI-powered features, real-time collaboration, and intelligent note-taking capabilities.

## Project Overview

Eduspace provides a comprehensive platform for:
- **Note Taking & Summarization**: Create, organize, and summarize notes with AI assistance
- **Real-time Collaboration**: Work together with peers on projects and documents
- **AI-Powered Insights**: Leverage Google Gemini API for intelligent content generation
- **File Management**: Upload and manage project files efficiently
- **Knowledge Hub**: Access curated learning resources and materials
- **Analytics**: Track learning progress and engagement metrics

## Tech Stack

### Frontend
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite
- **Styling**: TailwindCSS (via lucide-react icons)
- **State Management**: React hooks
- **API Client**: Axios
- **Real-time**: Firebase for authentication and storage
- **AI Integration**: Google Gemini API
- **File Upload**: Cloudinary

### Backend
- **Framework**: FastAPI (Python)
- **Server**: Uvicorn
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT with python-jose
- **Real-time Communication**: WebSocket with python-socketio
- **File Processing**: PyPDF2, python-docx, Pillow, pytesseract
- **Cloud Storage**: Cloudinary
- **Firebase**: Firebase Admin SDK for authentication & Firestore

## Project Structure

```
.
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── database.py             # Database configuration
│   ├── models.py               # SQLAlchemy ORM models
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── routes.py               # Main API routes
│   ├── ai_routes.py            # AI-powered endpoints
│   ├── chat_routes.py          # Chat functionality
│   ├── collaboration_routes.py # Real-time collaboration
│   ├── websocket_routes.py     # WebSocket handlers
│   ├── analytics_routes.py     # Analytics endpoints
│   ├── file_extractor.py       # Document processing
│   ├── firebase_admin.py       # Firebase integration
│   ├── requirements.txt        # Python dependencies
│   └── uploads/               # File upload directory
│
└── frontend/
    ├── index.html             # HTML entry point
    ├── index.tsx              # React app entry
    ├── App.tsx                # Main app component
    ├── package.json           # Node dependencies
    ├── tsconfig.json          # TypeScript config
    ├── vite.config.ts         # Vite configuration
    ├── firebaseConfig.ts      # Firebase setup
    ├── components/            # React components
    │   ├── HomePage.tsx
    │   ├── LoginPage.tsx
    │   ├── KnowledgeHub.tsx
    │   ├── Projects.tsx
    │   ├── Tasks.tsx
    │   └── ...
    ├── services/              # API & external services
    │   ├── api.ts
    │   ├── geminiService.ts
    │   └── uploadService.ts
    └── utils/                 # Utility functions

```

## Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js 16+
- PostgreSQL database
- Google Cloud credentials for Gemini API
- Firebase project setup
- Cloudinary account

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
# Create .env file with:
# DATABASE_URL=postgresql://user:password@localhost/eduspace_db
# FIREBASE_CREDENTIALS_PATH=path/to/serviceAccountKey.json
# GOOGLE_API_KEY=your_google_api_key
# CLOUDINARY_CLOUD_NAME=your_cloudinary_name
# CLOUDINARY_API_KEY=your_cloudinary_key
# CLOUDINARY_API_SECRET=your_cloudinary_secret

# Run migrations
python migrate_database.py

# Start the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure Firebase
# Update firebaseConfig.ts with your Firebase credentials

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation powered by Swagger UI.

## Key Features

### 1. **AI-Powered Note Summarization**
- Automatically generate summaries of notes using Google Gemini API
- Extract key points and concepts from documents

### 2. **Real-time Collaboration**
- WebSocket-based real-time updates
- Live document editing and commenting
- Presence indicators for active users

### 3. **File Management**
- Support for PDF, DOCX, images, and more
- Automatic text extraction from documents
- Cloud storage via Cloudinary

### 4. **User Authentication**
- Firebase authentication integration
- JWT-based API authentication
- Role-based access control

### 5. **Analytics & Tracking**
- User engagement metrics
- Learning progress tracking
- Performance analytics

### 6. **Knowledge Hub**
- Curated learning resources
- Subject-wise categorization
- Resource recommendations

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://user:password@localhost:5432/eduspace_db
JWT_SECRET_KEY=your_secret_key
FIREBASE_CREDENTIALS_PATH=path/to/serviceAccountKey.json
GOOGLE_API_KEY=your_gemini_api_key
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Frontend (.env)
```
VITE_API_BASE_URL=http://localhost:8000
VITE_FIREBASE_API_KEY=your_firebase_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_firebase_auth_domain
VITE_FIREBASE_PROJECT_ID=your_firebase_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_storage_bucket
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
VITE_GOOGLE_GEMINI_API_KEY=your_gemini_api_key
```

## Running the Application

### Development Mode

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173` to access the application.

## Database Schema

The application uses PostgreSQL with the following main tables:
- `users` - User accounts and profiles
- `notes` - User notes
- `projects` - Collaborative projects
- `tasks` - Project tasks
- `files` - Uploaded files metadata
- `chat_messages` - Chat messages
- `collaborations` - Project collaborations

## Contributing

Contributions are welcome! Please follow these guidelines:
1. Create a feature branch (`git checkout -b feature/AmazingFeature`)
2. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
3. Push to the branch (`git push origin feature/AmazingFeature`)
4. Open a Pull Request

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Verify DATABASE_URL is correct
- Check database credentials

### Firebase Authentication Errors
- Verify Firebase credentials file
- Check Firebase project configuration
- Ensure CORS is properly configured

### AI API Errors
- Verify Google API key
- Check API quota limits
- Ensure proper IAM permissions

### WebSocket Connection Issues
- Check CORS configuration
- Verify WebSocket port accessibility
- Review browser console for errors

## Performance Optimization

- Frontend: Built with Vite for optimal bundling
- Backend: Async/await patterns for non-blocking I/O
- Database: Indexed queries for fast searches
- Caching: Redis integration (optional)

## Security Considerations

- JWT token-based authentication
- Input validation on all endpoints
- CORS configuration
- Environment-based sensitive data management
- SQL injection prevention via SQLAlchemy ORM

## Future Enhancements

- [ ] Mobile application
- [ ] Advanced analytics dashboard
- [ ] Integration with more AI models
- [ ] Offline mode support
- [ ] Video conferencing integration
- [ ] Advanced search capabilities
- [ ] Dark mode support

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@eduspace.com or open an issue on GitHub.

## Authors

- **Keerthi** - Lead Developer

---

**Last Updated**: December 2025

For more information, visit our website: [www.eduspace.com](https://www.eduspace.com)
