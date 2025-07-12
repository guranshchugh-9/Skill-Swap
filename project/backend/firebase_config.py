import os
import firebase_admin
from firebase_admin import credentials, firestore
import requests
from dotenv import load_dotenv
from complete_database import SkillSwapDatabase


load_dotenv()

# =============================================================================
# FIREBASE CONFIG FROM .ENV FILE
# =============================================================================

def get_firebase_config():
    """Get Firebase configuration from environment variables"""
    config = {
        "apiKey": os.getenv("FIREBASE_API_KEY"),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
        "projectId": os.getenv("FIREBASE_PROJECT_ID"),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.getenv("FIREBASE_APP_ID")
    }
    
    # Check if all required environment variables are set
    missing_vars = [key for key, value in config.items() if not value]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("📝 Please check your .env file and make sure all Firebase values are set")
        print("🔧 Your .env file should contain:")
        print("   FIREBASE_API_KEY=your_api_key")
        print("   FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com")
        print("   FIREBASE_PROJECT_ID=your_project_id")
        print("   FIREBASE_STORAGE_BUCKET=your_project.appspot.com")
        print("   FIREBASE_MESSAGING_SENDER_ID=your_sender_id")
        print("   FIREBASE_APP_ID=your_app_id")
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    return config

# Get Firebase configuration
FIREBASE_CONFIG = get_firebase_config()

class FirebaseAuth:
    def __init__(self):
        self.db_manager = SkillSwapDatabase(FIREBASE_CONFIG)
        self.initialized = False
        self.api_key = FIREBASE_CONFIG["apiKey"]
        print(f"🔧 Firebase API Key loaded: {self.api_key[:10]}..." if self.api_key else "❌ No API Key")
    
    def initialize(self):
        """Initialize Firebase and Database"""
        try:
            # Initialize Firebase Admin
            if not firebase_admin._apps:
                # Try to get credentials file
                creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
                
                if os.path.exists(creds_path):
                    cred = credentials.Certificate(creds_path)
                    firebase_admin.initialize_app(cred)
                    print(f" Firebase Admin initialized with credentials from: {creds_path}")
                else:
                    print(f"Firebase credentials file not found: {creds_path}")
                    return False
            
            # Initialize database manager
            if self.db_manager.initialize():
                self.initialized = True
                print("Firebase and Database initialized successfully")
                return True
            else:
                print(" Database manager initialization failed")
                return False
            
        except Exception as e:
            print(f"Firebase initialization failed: {e}")
            return False
    
    def register_user(self, email, password, name, location=""):
        """Register new user with complete profile"""
        try:
            # Create authentication user
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={self.api_key}"
            
            data = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            response = requests.post(url, json=data)
            result = response.json()
            
            if response.status_code == 200:
                # Create complete user profile using database manager
                profile_result = self.db_manager.create_user_profile(
                    result['localId'], email, name, location
                )
                
                if profile_result['success']:
                    return {
                        'success': True,
                        'user': result,
                        'message': 'User registered successfully'
                    }
                else:
                    return {'success': False, 'error': 'Failed to create user profile'}
            else:
                error_msg = result.get('error', {}).get('message', 'Registration failed')
                return {'success': False, 'error': error_msg}
                    
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def login_user(self, email, password):
        """Login user and get complete profile"""
        try:
            url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}"
            
            data = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            response = requests.post(url, json=data)
            result = response.json()
            
            if response.status_code == 200:
                # Get complete user profile
                profile_result = self.db_manager.get_user_profile(result['localId'])
                
                if profile_result['success']:
                    # Update last login
                    self.db_manager.update_user_profile(result['localId'], {
                        'last_login': firestore.SERVER_TIMESTAMP
                    })
                    
                    return {
                        'success': True,
                        'user': result,
                        'profile': profile_result['profile'],
                        'message': 'Login successful'
                    }
                else:
                    return {'success': False, 'error': 'Profile not found'}
            else:
                error_msg = result.get('error', {}).get('message', 'Login failed')
                return {'success': False, 'error': error_msg}
                    
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # =========================================================================
    # USER PROFILE METHODS
    # =========================================================================
    
    def get_user_profile(self, user_id):
        """Get user profile"""
        return self.db_manager.get_user_profile(user_id)
    
    def update_user_profile(self, user_id, updates):
        """Update user profile"""
        return self.db_manager.update_user_profile(user_id, updates)
    
    def get_public_users(self, limit=50):
        """Get public users for browsing"""
        return self.db_manager.get_public_users(limit)
    
    # =========================================================================
    # SKILLS METHODS
    # =========================================================================
    
    def get_all_skills(self):
        """Get all available skills"""
        return self.db_manager.get_all_skills()
    
    def search_skills(self, query, category=None):
        """Search skills"""
        return self.db_manager.search_skills(query, category)
    
    def add_user_skill(self, user_id, skill_name, skill_type, proficiency="intermediate", description=""):
        """Add skill to user"""
        return self.db_manager.add_user_skill(user_id, skill_name, skill_type, proficiency, description)
    
    def get_user_skills(self, user_id, skill_type=None):
        """Get user's skills"""
        return self.db_manager.get_user_skills(user_id, skill_type)
    
    def remove_user_skill(self, user_id, skill_name, skill_type):
        """Remove user skill"""
        return self.db_manager.remove_user_skill(user_id, skill_name, skill_type)
    
    # =========================================================================
    # BARTER REQUESTS METHODS
    # =========================================================================
    
    def create_barter_request(self, sender_id, receiver_id, offered_skill, requested_skill, message=""):
        """Create skill swap request"""
        return self.db_manager.create_barter_request(sender_id, receiver_id, offered_skill, requested_skill, message)
    
    def get_user_requests(self, user_id, request_type='all'):
        """Get user's barter requests"""
        return self.db_manager.get_user_requests(user_id, request_type)
    
    def update_request_status(self, request_id, status, response_message=""):
        """Update request status"""
        return self.db_manager.update_request_status(request_id, status, response_message)
    
    # =========================================================================
    # TRANSACTIONS METHODS
    # =========================================================================
    
    def get_user_transactions(self, user_id):
        """Get user's transactions"""
        return self.db_manager.get_user_transactions(user_id)
    
    # =========================================================================
    # REVIEWS METHODS
    # =========================================================================
    
    def create_review(self, reviewer_id, reviewee_id, transaction_id, rating, comment, title=""):
        """Create review after transaction"""
        return self.db_manager.create_review(reviewer_id, reviewee_id, transaction_id, rating, comment, title)
    
    def get_user_reviews(self, user_id, as_reviewee=True):
        """Get user reviews"""
        return self.db_manager.get_user_reviews(user_id, as_reviewee)
    
    # =========================================================================
    # SYSTEM MESSAGES METHODS
    # =========================================================================
    
    def get_active_messages(self):
        """Get active system messages"""
        return self.db_manager.get_active_messages()
    
    def create_system_message(self, admin_id, title, message, message_type="announcement"):
        """Create system message (admin only)"""
        return self.db_manager.create_system_message(admin_id, title, message, message_type)
    
    # =========================================================================
    # SETUP METHODS
    # =========================================================================
    
    def setup_sample_data(self):
        """Setup sample data for testing"""
        return self.db_manager.setup_sample_data()

# Global instance
firebase_auth = FirebaseAuth()
