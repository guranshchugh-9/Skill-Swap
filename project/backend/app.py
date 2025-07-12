from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import auth
import os
from dotenv import load_dotenv
from firebase_config import firebase_auth
from api_routes import api

# Load environment variables
load_dotenv()

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Enable CORS for all routes (development-safe)
    CORS(app, origins="*", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # Initialize Firebase Auth
    if not firebase_auth.initialize():
        print("❌ Failed to initialize Firebase Auth")
        return None
    
    # Register API blueprint
    app.register_blueprint(api)
    
    # Health check endpoint
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "message": "SkillSwap API is running",
            "firebase_initialized": firebase_auth.initialized
        })
    
    # Root endpoint
    @app.route("/", methods=["GET"])
    def root():
        return jsonify({
            "message": "SkillSwap API Server",
            "version": "1.0.0",
            "endpoints": "/api/*"
        })
    
    return app

if __name__ == "__main__":
    app = create_app()
    if app:
        print("🚀 Starting SkillSwap API Server...")
        print("📡 API endpoints available at: http://localhost:5000/api/*")
        print("🔧 Health check: http://localhost:5000/health")
        app.run(debug=True, host="0.0.0.0", port=5000)
    else:
        print("❌ Failed to create Flask application")