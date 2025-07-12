# SkillSwap API Backend

A comprehensive Flask REST API backend for the SkillSwap platform, featuring Firebase authentication and Firestore database integration.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (for development scripts)
npm install
```

### 2. Configure Environment

```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit .env file with your Firebase configuration
nano backend/.env
```

### 3. Firebase Setup

1. Download your Firebase Admin SDK credentials JSON file
2. Place it in the `backend/` directory as `firebase-credentials.json`
3. Update your `.env` file with Firebase configuration

### 4. Run the Server

```bash
# Run backend only
npm run backend

# Or run both frontend and backend (when frontend is configured)
npm run dev

# Or run directly with Python
cd backend && python run_server.py
```

## 📡 API Endpoints

### 🔐 Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - Login user
- `POST /api/logout` - Logout user

### 👤 User Profile
- `GET /api/me` - Get current user profile
- `PUT /api/me/update` - Update user profile
- `GET /api/me/skills` - Get user's skills
- `POST /api/me/skills/add` - Add skill to user
- `POST /api/me/skills/remove` - Remove skill from user
- `GET /api/me/swap-requests` - Get user's swap requests
- `GET /api/me/transactions` - Get user's transactions
- `GET /api/me/reviews` - Get user's reviews

### 👥 Public Users
- `GET /api/users` - List public users
- `GET /api/users/<user_id>` - Get user profile
- `GET /api/users/<user_id>/skills` - Get user's skills
- `GET /api/users/<user_id>/reviews` - Get user's reviews

### 🧠 Skills
- `GET /api/skills` - List all skills
- `GET /api/skills/search?query=python` - Search skills

### 🔁 Swap Requests
- `POST /api/swap-requests` - Create swap request
- `PUT /api/swap-requests/<id>/update` - Update request status

### ⭐ Reviews
- `POST /api/reviews` - Create review
- `GET /api/reviews/<user_id>` - Get user reviews

### 📣 System Messages
- `GET /api/system-messages` - Get active messages
- `POST /api/system-messages/create` - Create message (admin)

## 🔒 Authentication

All protected endpoints require a Firebase ID token in the Authorization header:

```
Authorization: Bearer <firebase_id_token>
```

## 🛠️ Development

### Project Structure

```
backend/
├── app.py                 # Flask application factory
├── api_routes.py          # API route definitions
├── firebase_config.py     # Firebase configuration and auth class
├── complete_database.py   # Database operations class
├── run_server.py          # Server runner script
├── requirements.txt       # Python dependencies
└── .env                   # Environment variables
```

### Adding New Endpoints

1. Add route to `api_routes.py`
2. Use `@require_auth` decorator for protected routes
3. Call methods on `firebase_auth` instance
4. Return responses using `handle_response()`

### Error Handling

The API includes comprehensive error handling:
- Token verification errors (401)
- Missing data errors (400)
- Server errors (500)
- Not found errors (404)

## 🔧 Configuration

### Environment Variables

- `FIREBASE_API_KEY` - Firebase API key
- `FIREBASE_AUTH_DOMAIN` - Firebase auth domain
- `FIREBASE_PROJECT_ID` - Firebase project ID
- `FIREBASE_STORAGE_BUCKET` - Firebase storage bucket
- `FIREBASE_MESSAGING_SENDER_ID` - Firebase messaging sender ID
- `FIREBASE_APP_ID` - Firebase app ID
- `FIREBASE_CREDENTIALS_PATH` - Path to Firebase admin credentials
- `FLASK_ENV` - Flask environment (development/production)
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 5000)

## 🚀 Deployment

### Production Setup

1. Set `FLASK_ENV=production` in environment
2. Use a production WSGI server like Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Health Check

The API includes a health check endpoint at `/health` for monitoring.

## 📝 API Response Format

All API responses follow a consistent format:

```json
{
  "success": true,
  "data": {...},
  "message": "Operation successful"
}
```

Error responses:

```json
{
  "success": false,
  "error": "Error description"
}
```

## 🔍 Testing

Test the API using curl, Postman, or any HTTP client:

```bash
# Health check
curl http://localhost:5000/health

# Register user
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","name":"Test User"}'

# Get skills (requires auth token)
curl -X GET http://localhost:5000/api/skills \
  -H "Authorization: Bearer <your_firebase_token>"
```