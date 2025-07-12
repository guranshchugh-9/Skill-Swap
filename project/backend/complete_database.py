import firebase_admin
from firebase_admin import credentials, firestore
import requests
import json
from datetime import datetime, timedelta
import uuid



class SkillSwapDatabase:
    def __init__(self, firebase_config):
        self.db = None
        self.initialized = False
        self.api_key = firebase_config["apiKey"]
        
    def initialize(self):
        """Initialize Firebase Admin SDK"""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate("firebase-credentials.json")
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            self.initialized = True
            print(" Database initialized successfully")
            return True
            
        except Exception as e:
            print(f" Database initialization failed: {e}")
            return False

   
    # USERS COLLECTION
   
    
    def create_user_profile(self, user_id, email, name, location=""):
        """Create user profile in Users collection"""
        try:
            user_data = {
                'user_id': user_id,
                'email': email,
                'name': name,
                'location': location,
                'profile_photo': '',
                'availability': 'weekends',  # weekends, evenings, flexible, anytime
                'profile_visibility': 'public',  # public, private
                'role': 'user',  # user, admin
                'is_banned': False,
                'ban_reason': '',
                'banned_until': None,
                'rating_avg': 0.0,
                'rating_count': 0,
                'total_swaps': 0,
                'successful_swaps': 0,
                'pending_requests': 0,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'last_login': firestore.SERVER_TIMESTAMP
            }
            
            self.db.collection('users').document(user_id).set(user_data)
            return {'success': True, 'message': 'User profile created'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_user_profile(self, user_id):
        """Get user profile"""
        try:
            doc = self.db.collection('users').document(user_id).get()
            if doc.exists:
                return {'success': True, 'profile': doc.to_dict()}
            else:
                return {'success': False, 'error': 'User not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def update_user_profile(self, user_id, updates):
        """Update user profile"""
        try:
            updates['updated_at'] = firestore.SERVER_TIMESTAMP
            self.db.collection('users').document(user_id).update(updates)
            return {'success': True, 'message': 'Profile updated'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_public_users(self, limit=50):
        """Get all public user profiles"""
        try:
            users_ref = self.db.collection('users').where('profile_visibility', '==', 'public').where('is_banned', '==', False).limit(limit)
            users = []
            for doc in users_ref.stream():
                user_data = doc.to_dict()
                user_data['user_id'] = doc.id
                users.append(user_data)
            return {'success': True, 'users': users}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    
    # SKILLS COLLECTION
    
    def create_skill(self, name, description, category="General", created_by="system"):
        """Create a skill in Skills collection"""
        try:
            skill_id = name.lower().replace(' ', '_').replace('-', '_')
            skill_data = {
                'skill_id': skill_id,
                'name': name,
                'description': description,
                'category': category,
                'subcategory': '',
                'tags': [],
                'users_offering': 0,
                'users_wanting': 0,
                'total_swaps': 0,
                'popularity_score': 0.0,
                'is_approved': True,
                'is_flagged': False,
                'flag_count': 0,
                'created_by': created_by,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            self.db.collection('skills').document(skill_id).set(skill_data)
            return {'success': True, 'skill_id': skill_id}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_all_skills(self):
        """Get all approved skills"""
        try:
            skills_ref = self.db.collection('skills').where('is_approved', '==', True).where('is_flagged', '==', False)
            skills = []
            for doc in skills_ref.stream():
                skill_data = doc.to_dict()
                skills.append(skill_data)
            return {'success': True, 'skills': skills}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def search_skills(self, query, category=None):
        """Search skills by name or category"""
        try:
            skills_ref = self.db.collection('skills').where('is_approved', '==', True)
            
            skills = []
            for doc in skills_ref.stream():
                skill_data = doc.to_dict()
                # Simple text search
                if query.lower() in skill_data['name'].lower():
                    if category is None or skill_data.get('category') == category:
                        skills.append(skill_data)
            
            return {'success': True, 'skills': skills}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    
    # USER_SKILLS COLLECTION
    
    
    def add_user_skill(self, user_id, skill_name, skill_type, proficiency_level="intermediate", description=""):
        """Add skill to User_Skills collection"""
        try:
            # First, ensure skill exists in Skills collection
            skill_id = skill_name.lower().replace(' ', '_').replace('-', '_')
            skill_doc = self.db.collection('skills').document(skill_id).get()
            
            if not skill_doc.exists:
                # Create skill if it doesn't exist
                self.create_skill(skill_name, f"User-added skill: {skill_name}")
            
            # Create user-skill relationship
            user_skill_id = f"{user_id}_{skill_id}_{skill_type}"
            user_skill_data = {
                'user_skill_id': user_skill_id,
                'user_id': user_id,
                'skill_id': skill_id,
                'skill_name': skill_name,
                'type': skill_type,  # 'offered' or 'wanted'
                'proficiency_level': proficiency_level,  # beginner, intermediate, advanced, expert
                'experience_years': 0,
                'description': description,
                'certifications': [],
                'is_active': True,
                'available_for_swap': True,
                'max_concurrent_swaps': 2,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            self.db.collection('user_skills').document(user_skill_id).set(user_skill_data)
            
            # Update skill counters
            if skill_type == 'offered':
                self.db.collection('skills').document(skill_id).update({'users_offering': firestore.Increment(1)})
            else:
                self.db.collection('skills').document(skill_id).update({'users_wanting': firestore.Increment(1)})
            
            return {'success': True, 'message': 'Skill added successfully'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_user_skills(self, user_id, skill_type=None):
        """Get user's skills"""
        try:
            query = self.db.collection('user_skills').where('user_id', '==', user_id).where('is_active', '==', True)
            
            if skill_type:
                query = query.where('type', '==', skill_type)
            
            skills = []
            for doc in query.stream():
                skill_data = doc.to_dict()
                skills.append(skill_data)
            
            return {'success': True, 'skills': skills}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def remove_user_skill(self, user_id, skill_name, skill_type):
        """Remove user skill"""
        try:
            skill_id = skill_name.lower().replace(' ', '_').replace('-', '_')
            user_skill_id = f"{user_id}_{skill_id}_{skill_type}"
            
            self.db.collection('user_skills').document(user_skill_id).delete()
            
            # Update skill counters
            if skill_type == 'offered':
                self.db.collection('skills').document(skill_id).update({'users_offering': firestore.Increment(-1)})
            else:
                self.db.collection('skills').document(skill_id).update({'users_wanting': firestore.Increment(-1)})
            
            return {'success': True, 'message': 'Skill removed'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

   
    # BARTER_REQUESTS COLLECTION
    
    
    def create_barter_request(self, sender_id, receiver_id, offered_skill, requested_skill, message=""):
        """Create a skill swap request"""
        try:
            request_data = {
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'offered_skill_name': offered_skill,
                'requested_skill_name': requested_skill,
                'message': message,
                'proposed_duration': '2 weeks',
                'proposed_format': 'online',  # online, in_person, hybrid
                'proposed_schedule': 'weekends',
                'status': 'pending',  # pending, accepted, rejected, cancelled, completed
                'priority': 'normal',  # low, normal, high
                'response_message': '',
                'rejection_reason': '',
                'transaction_id': None,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'responded_at': None,
                'expires_at': datetime.now() + timedelta(days=7)  # Auto-expire in 7 days
            }
            
            doc_ref = self.db.collection('barter_requests').document()
            doc_ref.set(request_data)
            
           
            self.db.collection('users').document(receiver_id).update({'pending_requests': firestore.Increment(1)})
            
            return {'success': True, 'request_id': doc_ref.id}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_user_requests(self, user_id, request_type='all'):
        """Get user's barter requests"""
        try:
            requests = []
            
            if request_type in ['sent', 'all']:
                sent_query = self.db.collection('barter_requests').where('sender_id', '==', user_id)
                for doc in sent_query.stream():
                    request_data = doc.to_dict()
                    request_data['request_id'] = doc.id
                    request_data['type'] = 'sent'
                    requests.append(request_data)
            
            if request_type in ['received', 'all']:
                received_query = self.db.collection('barter_requests').where('receiver_id', '==', user_id)
                for doc in received_query.stream():
                    request_data = doc.to_dict()
                    request_data['request_id'] = doc.id
                    request_data['type'] = 'received'
                    requests.append(request_data)
            
            return {'success': True, 'requests': requests}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def update_request_status(self, request_id, status, response_message=""):
        """Update barter request status"""
        try:
            updates = {
                'status': status,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'responded_at': firestore.SERVER_TIMESTAMP,
                'response_message': response_message
            }
            
            self.db.collection('barter_requests').document(request_id).update(updates)
            
           
            if status == 'accepted':
                self.create_transaction_from_request(request_id)
            
            return {'success': True, 'message': 'Request status updated'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    
    # TRANSACTIONS COLLECTION
   
    
    def create_transaction_from_request(self, request_id):
        """Create transaction when request is accepted"""
        try:
            # Get request details
            request_doc = self.db.collection('barter_requests').document(request_id).get()
            if not request_doc.exists:
                return {'success': False, 'error': 'Request not found'}
            
            request_data = request_doc.to_dict()
            
            transaction_data = {
                'barter_request_id': request_id,
                'user1_id': request_data['sender_id'],
                'user2_id': request_data['receiver_id'],
                'user1_skill': request_data['offered_skill_name'],
                'user2_skill': request_data['requested_skill_name'],
                'status': 'in_progress',  # in_progress, completed, cancelled, disputed
                'start_date': firestore.SERVER_TIMESTAMP,
                'expected_end_date': datetime.now() + timedelta(weeks=2),
                'actual_end_date': None,
                'user1_confirmed': False,
                'user2_confirmed': False,
                'completion_percentage': 0,
                'sessions': [],
                'is_disputed': False,
                'dispute_reason': '',
                'admin_notes': '',
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            doc_ref = self.db.collection('transactions').document()
            doc_ref.set(transaction_data)
            
            # Update request with transaction ID
            self.db.collection('barter_requests').document(request_id).update({'transaction_id': doc_ref.id})
            
            return {'success': True, 'transaction_id': doc_ref.id}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_user_transactions(self, user_id):
        """Get user's transactions"""
        try:
            transactions = []
            
            # Transactions where user is user1
            query1 = self.db.collection('transactions').where('user1_id', '==', user_id)
            for doc in query1.stream():
                transaction_data = doc.to_dict()
                transaction_data['transaction_id'] = doc.id
                transaction_data['user_role'] = 'user1'
                transactions.append(transaction_data)
            
            # Transactions where user is user2
            query2 = self.db.collection('transactions').where('user2_id', '==', user_id)
            for doc in query2.stream():
                transaction_data = doc.to_dict()
                transaction_data['transaction_id'] = doc.id
                transaction_data['user_role'] = 'user2'
                transactions.append(transaction_data)
            
            return {'success': True, 'transactions': transactions}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    
    # REVIEWS COLLECTION
   
    
    def create_review(self, reviewer_id, reviewee_id, transaction_id, rating, comment, title=""):
        """Create review after transaction"""
        try:
            review_data = {
                'reviewer_id': reviewer_id,
                'reviewee_id': reviewee_id,
                'transaction_id': transaction_id,
                'rating': rating,  # 1-5 stars
                'title': title,
                'comment': comment,
                'skills_learned': [],
                'communication_rating': rating,
                'teaching_ability': rating,
                'reliability': rating,
                'overall_experience': rating,
                'is_public': True,
                'is_verified': True,
                'helpful_votes': 0,
                'is_flagged': False,
                'is_approved': True,
                'admin_notes': '',
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            doc_ref = self.db.collection('reviews').document()
            doc_ref.set(review_data)
            
            # Update reviewee's rating
            self.update_user_rating(reviewee_id)
            
            return {'success': True, 'review_id': doc_ref.id}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def update_user_rating(self, user_id):
        """Update user's average rating"""
        try:
            reviews_query = self.db.collection('reviews').where('reviewee_id', '==', user_id).where('is_approved', '==', True)
            reviews = list(reviews_query.stream())
            
            if reviews:
                total_rating = sum([r.to_dict()['rating'] for r in reviews])
                avg_rating = round(total_rating / len(reviews), 1)
                
                self.db.collection('users').document(user_id).update({
                    'rating_avg': avg_rating,
                    'rating_count': len(reviews)
                })
            
            return {'success': True}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_user_reviews(self, user_id, as_reviewee=True):
        """Get reviews for a user"""
        try:
            if as_reviewee:
                query = self.db.collection('reviews').where('reviewee_id', '==', user_id).where('is_public', '==', True)
            else:
                query = self.db.collection('reviews').where('reviewer_id', '==', user_id)
            
            reviews = []
            for doc in query.stream():
                review_data = doc.to_dict()
                review_data['review_id'] = doc.id
                reviews.append(review_data)
            
            return {'success': True, 'reviews': reviews}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

  
    # SYSTEM_MESSAGES COLLECTION
   
    
    def create_system_message(self, admin_id, title, message, message_type="announcement"):
        """Create platform-wide message"""
        try:
            message_data = {
                'admin_id': admin_id,
                'admin_name': 'Admin',  # Get from user profile
                'title': title,
                'message': message,
                'type': message_type,  # announcement, maintenance, feature_update, warning
                'priority': 'normal',  # low, normal, high, urgent
                'target_audience': 'all',  # all, users, admins, specific
                'target_user_ids': [],
                'target_roles': ['user'],
                'is_active': True,
                'is_dismissible': True,
                'show_until': datetime.now() + timedelta(days=7),
                'display_location': 'banner',  # banner, modal, notification
                'view_count': 0,
                'dismissal_count': 0,
                'click_count': 0,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'published_at': firestore.SERVER_TIMESTAMP
            }
            
            doc_ref = self.db.collection('system_messages').document()
            doc_ref.set(message_data)
            
            return {'success': True, 'message_id': doc_ref.id}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_active_messages(self):
        """Get active system messages"""
        try:
            query = self.db.collection('system_messages').where('is_active', '==', True)
            messages = []
            
            for doc in query.stream():
                message_data = doc.to_dict()
                message_data['message_id'] = doc.id
                
                # Check if message is still valid
                if message_data.get('show_until') and message_data['show_until'] > datetime.now():
                    messages.append(message_data)
            
            return {'success': True, 'messages': messages}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

    
    # SAMPLE DATA SETUP
    
    
    def setup_sample_data(self):
        """Create sample data for testing"""
        try:
            # Sample skills
            sample_skills = [
                {'name': 'JavaScript Programming', 'description': 'Modern JavaScript development', 'category': 'Programming'},
                {'name': 'Python Programming', 'description': 'Python for web development and data science', 'category': 'Programming'},
                {'name': 'Graphic Design', 'description': 'Visual design and branding', 'category': 'Design'},
                {'name': 'Photography', 'description': 'Digital photography and editing', 'category': 'Creative'},
                {'name': 'Spanish Language', 'description': 'Conversational and business Spanish', 'category': 'Languages'},
                {'name': 'Guitar Playing', 'description': 'Acoustic and electric guitar', 'category': 'Music'},
                {'name': 'Cooking', 'description': 'International cuisine and baking', 'category': 'Lifestyle'},
                {'name': 'Digital Marketing', 'description': 'Social media and online marketing', 'category': 'Business'},
                {'name': 'Data Science', 'description': 'Data analysis and machine learning', 'category': 'Programming'},
                {'name': 'UI/UX Design', 'description': 'User interface and experience design', 'category': 'Design'}
            ]
            
            for skill in sample_skills:
                self.create_skill(skill['name'], skill['description'], skill['category'])
            
            print(" Sample skills created successfully")
            
            # Sample system message
            self.create_system_message(
                'admin',
                'Welcome to Skill Swap Platform!',
                'Start connecting with other learners and share your skills today.',
                'announcement'
            )
            
            print("Sample system message created")
            return {'success': True, 'message': 'Sample data created successfully'}
            
        except Exception as e:
            print(f" Error creating sample data: {e}")
            return {'success': False, 'error': str(e)}