#!/usr/bin/env python3
"""
SkillSwap API Server Runner
Handles development and production server startup
"""

import os
import sys
from app import create_app

def main():
    """Main server runner"""
    app = create_app()
    
    if not app:
        print("❌ Failed to create Flask application")
        sys.exit(1)
    
    # Get environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    
    print("🚀 Starting SkillSwap API Server...")
    print(f"📡 Server running at: http://{host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"📋 API endpoints: http://{host}:{port}/api/*")
    print(f"❤️  Health check: http://{host}:{port}/health")
    print("=" * 50)
    
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()