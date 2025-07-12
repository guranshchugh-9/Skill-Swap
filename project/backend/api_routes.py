from flask import Blueprint, request, jsonify
import firebase_admin
from firebase_admin import auth
from firebase_config import firebase_auth
import traceback

# Create API Blueprint
api = Blueprint('api', __name__)

# =============================================================================
# AUTHENTICATION HELPERS
# =============================================================================

def verify_token():
    """Verify Firebase ID token from Authorization header"""
    try:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None, {"success": False, "error": "Missing or invalid Authorization header"}, 401
        
        token = auth_header.split(" ")[1]
        decoded = auth.verify_id_token(token)
        return decoded["uid"], None, None
    except Exception as e:
        return None, {"success": False, "error": f"Invalid token: {str(e)}"}, 401

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        user_id, error, status = verify_token()
        if error:
            return jsonify(error), status
        request.user_id = user_id
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def handle_response(result):
    """Handle standard response format"""
    if isinstance(result, dict) and 'success' in result:
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    return jsonify(result)

# =============================================================================
# 🔐 AUTHENTICATION ROUTES
# =============================================================================

@api.route("/api/register", methods=["POST"])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        location = data.get('location', '')
        
        if not all([email, password, name]):
            return jsonify({"success": False, "error": "Email, password, and name are required"}), 400
        
        result = firebase_auth.register_user(email, password, name, location)
        return handle_response(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api.route("/api/login", methods=["POST"])
def login():
    """Login user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        email = data.get('email')
        password = data.get('password')
        
        if not all([email, password]):
            return jsonify({"success": False, "error": "Email and password are required"}), 400
        
        result = firebase_auth.login_user(email, password)
        return handle_response(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api.route("/api/logout", methods=["POST"])
def logout():
    """Logout user (handled client-side)"""
    return jsonify({"success": True, "message": "Logout successful"})

# =============================================================================
# 👤 USER PROFILE ROUTES
# =============================================================================

@api.route("/api/me", methods=["GET"])
@require_auth
def get_current_user():
    """Get current user profile"""
    try:
        result = firebase_auth.get_user_profile(request.user_id)
        return handle_response(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api.route("/api/me/update", methods=["PUT"])
@require_auth
def update_current_user():
    """Update current user profile"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        result = firebase_auth.update_user_profile(request.user_id, data)
        return handle_response(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api.route("/api/me/skills", methods=["GET"])
@require_auth
def get_current_user_skills():
    """Get current user's skills"""
    try:
        skill_type = request.args.get('type')  # 'offered' or 'wanted'
        result = firebase_auth.get_user_skills(request.user_id, skill_type)
        return handle_response(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api.route("/api/me/skills/add", methods=["POST"])
@require_auth
def add_user_skill():
    """Add skill to current user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        skill_name = data.get('skill_name')
        skill_type = data.get('skill_type')  # 'offered' or 'wanted'
        proficiency = data.get('proficiency', 'intermediate')
        description = data.get('description', '')
        
        if not all([skill_name, skill_type]):
            return jsonify({"success": False, "error": "Skill name and type are required"}), 400
        
        result = firebase_auth.add_user_skill(request.user_id, skill_name, skill_type, proficiency, description)
        return handle_response(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api.route("/api/me/skills/remove", methods=["POST"])
@require_auth
def remove_user_skill():
    """Remove skill from current user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        skill_name = data.get('skill_name')
        skill_type = data.get('skill_type')
        
        if not all([skill_name, skill_type]):
            return jsonify({"success": False, "error": "Skill name and type are required"}), 400
        
        result = firebase_auth.remove_user_skill(request.user_id, skill_name, skill_type)
        return handle_response(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api.route("/api/me/swap-requests", methods=["GET"])
@require_auth
def get_user_swap_requests():
    """Get current user's swap requests"""
    try:
        request_type = request.args.get('type', 'all')  # 'sent', 'received', 'all'
        result = firebase_auth.get_user_requests(request.user_id, request_type)
        return handle_response(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api.route("/api/me/transactions", methods=["GET"])
@require_auth
def get_user_transactions():
    """Get current user's transactions"""
    try:
        result = firebase_auth.get_user_transactions(request.user_id)
        return handle_response(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api.route("/api/me/reviews", methods=["GET"])
@require_auth
def get_user_reviews():
    """Get reviews for or by current user"""
    try:
        as_reviewee = request.args.get('as_reviewee', 'true').lower() == 'true'
        result = firebase_auth.get_user_reviews(request.user_id, as_reviewee)
        return handle_response(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =============================================================================
# 👥 PUBLIC USER ROUTES
# =============================================================================

@api.route("/api/users", methods=["GET"])
def get_public_users():
    """Get list of public users"""
    try:
        limit = int(request.args.get('limit', 50))
        result = firebase_auth.get_public_users(limit)
        return handle_response(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api.route("/api/users/<user_id>", methods=["GET"])
def get_user_profile(user_id):
    """Get public profile of a user"""
    try:
        result = firebase_auth.get_user_profile(user_id)
        return handle_response(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api.route("/api/users/<user_id>/skills", methods=["GET"])
def get_user_skills(user_id):
    """Get a user's skills"""
    try:
        skill_type = request.args.get('type')
        result = firebase_auth.get_user_skills(user_id, skill_type)
        return handle_response(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api.route("/api/users/<user_id>/reviews", methods=["GET"])
def get_user_public_reviews(user_id):
    """Get reviews for a user"""
    try:
        result = firebase_auth.get_user_reviews(user_id, as_reviewee=True)
        return handle_response(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =============================================================================
# 🧠 SKILLS ROUTES
# =============================================================================

@api.route("/api/skills", methods=["GET"])
def get_all_skills():
    """Get all available skills"""
    try:
        result = firebase_auth.get_all_skills()
        return handle_response(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api.route("/api/skills/search", methods=["GET"])
def search_skills():
    """Search skills"""
    try:
        query = request.args.get('query', '')
        category = request.args.get('category')
        
        if not query:
            return jsonify({"success": False, "error": "Query parameter is required"}), 400
        
        result = firebase_auth.search_skills(query, category)
        return handle_response(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =============================================================================
# 🔁 SWAP REQUEST ROUTES
# =============================================================================

@api.route("/api/swap-requests", methods=["POST"])
@require_auth
def create_swap_request():
    """Create a new skill swap request"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        receiver_id = data.get('receiver_id')
        offered_skill = data.get('offered_skill')
        requested_skill = data.get('requested_skill')
        message = data.get('message', '')
        
        if not all([receiver_id, offered_skill, requested_skill]):
            return jsonify({"success": False, "error": "Receiver ID, offered skill, and requested skill are required"}), 400
        
        result = firebase_auth.create_barter_request(request.user_id, receiver_id, offered_skill, requested_skill, message)
        return handle_response(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api.route("/api/swap-requests/<request_id>/update", methods=["PUT"])
@require_auth
def update_swap_request(request_id):
    """Accept/reject/cancel swap request"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        status = data.get('status')  # 'accepted', 'rejected', 'cancelled'
        response_message = data.get('response_message', '')
        
        if not status:
            return jsonify({"success": False, "error": "Status is required"}), 400
        
        result = firebase_auth.update_request_status(request_id, status, response_message)
        return handle_response(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =============================================================================
# 💳 TRANSACTION ROUTES
# =============================================================================

@api.route("/api/transactions/<transaction_id>", methods=["GET"])
@require_auth
def get_transaction_details(transaction_id):
    """Get details of a transaction"""
    try:
        # This would need to be implemented in the database class
        return jsonify({"success": False, "error": "Transaction details endpoint not implemented"}), 501
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =============================================================================
# ⭐ REVIEW ROUTES
# =============================================================================

@api.route("/api/reviews", methods=["POST"])
@require_auth
def create_review():
    """Create a new review"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        reviewee_id = data.get('reviewee_id')
        transaction_id = data.get('transaction_id')
        rating = data.get('rating')
        comment = data.get('comment')
        title = data.get('title', '')
        
        if not all([reviewee_id, transaction_id, rating, comment]):
            return jsonify({"success": False, "error": "Reviewee ID, transaction ID, rating, and comment are required"}), 400
        
        result = firebase_auth.create_review(request.user_id, reviewee_id, transaction_id, rating, comment, title)
        return handle_response(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api.route("/api/reviews/<user_id>", methods=["GET"])
def get_public_reviews(user_id):
    """Get public reviews for a user"""
    try:
        result = firebase_auth.get_user_reviews(user_id, as_reviewee=True)
        return handle_response(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =============================================================================
# 📣 SYSTEM MESSAGE ROUTES
# =============================================================================

@api.route("/api/system-messages", methods=["GET"])
def get_system_messages():
    """Get active system messages"""
    try:
        result = firebase_auth.get_active_messages()
        return handle_response(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api.route("/api/system-messages/create", methods=["POST"])
@require_auth
def create_system_message():
    """Create system message (admin only)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        title = data.get('title')
        message = data.get('message')
        message_type = data.get('message_type', 'announcement')
        
        if not all([title, message]):
            return jsonify({"success": False, "error": "Title and message are required"}), 400
        
        result = firebase_auth.create_system_message(request.user_id, title, message, message_type)
        return handle_response(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =============================================================================
# 🛡️ ADMIN ROUTES (Placeholder implementations)
# =============================================================================

@api.route("/api/admin/users", methods=["GET"])
@require_auth
def admin_get_all_users():
    """Admin: List all users"""
    try:
        # This would need admin permission check and implementation in database class
        return jsonify({"success": False, "error": "Admin users endpoint not implemented"}), 501
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api.route("/api/admin/users/<user_id>/ban", methods=["PUT"])
@require_auth
def admin_ban_user(user_id):
    """Admin: Ban or unban user"""
    try:
        # This would need admin permission check and implementation in database class
        return jsonify({"success": False, "error": "Admin ban user endpoint not implemented"}), 501
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api.route("/api/admin/swap-requests", methods=["GET"])
@require_auth
def admin_get_all_requests():
    """Admin: View all swap requests"""
    try:
        # This would need admin permission check and implementation in database class
        return jsonify({"success": False, "error": "Admin swap requests endpoint not implemented"}), 501
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =============================================================================
# 🔧 SETUP ROUTES
# =============================================================================

@api.route("/api/setup/sample-data", methods=["POST"])
def setup_sample_data():
    """Setup sample data for testing"""
    try:
        result = firebase_auth.setup_sample_data()
        return handle_response(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@api.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404

@api.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"success": False, "error": "Method not allowed"}), 405

@api.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "Internal server error"}), 500