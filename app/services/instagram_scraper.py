# Instagram OAuth Follower Tracker - Flask Backend
# This uses Instagram's OFFICIAL API - no scraping needed!

from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import requests
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instagram_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ============================================================================
# INSTAGRAM API CONFIGURATION
# ============================================================================
# You'll get these after registering your app at developers.facebook.com
INSTAGRAM_APP_ID = 'YOUR_APP_ID_HERE'
INSTAGRAM_APP_SECRET = 'YOUR_APP_SECRET_HERE'
REDIRECT_URI = 'http://localhost:5000/auth/callback'

# Instagram OAuth URLs
INSTAGRAM_AUTH_URL = 'https://api.instagram.com/oauth/authorize'
INSTAGRAM_TOKEN_URL = 'https://api.instagram.com/oauth/access_token'
INSTAGRAM_API_URL = 'https://graph.instagram.com'

# ============================================================================
# DATABASE MODELS
# ============================================================================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    instagram_id = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    access_token = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_scan = db.Column(db.DateTime)
    
    followers = db.relationship('Follower', backref='user', lazy=True, cascade='all, delete-orphan')
    following = db.relationship('Following', backref='user', lazy=True, cascade='all, delete-orphan')

class Follower(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    instagram_user_id = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    follows_back = db.Column(db.Boolean, default=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

class Following(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    instagram_user_id = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    follows_back = db.Column(db.Boolean, default=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

class UnfollowerHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    unfollower_username = db.Column(db.String(100), nullable=False)
    unfollowed_at = db.Column(db.DateTime, default=datetime.utcnow)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def get_instagram_followers(access_token, user_id):
    """Fetch followers from Instagram API"""
    url = f"{INSTAGRAM_API_URL}/{user_id}/followers"
    params = {
        'access_token': access_token,
        'fields': 'id,username,account_type'
    }
    
    followers = []
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'data' in data:
            followers = data['data']
            
            # Handle pagination
            while 'paging' in data and 'next' in data['paging']:
                response = requests.get(data['paging']['next'])
                data = response.json()
                if 'data' in data:
                    followers.extend(data['data'])
        
        return followers
    except Exception as e:
        print(f"Error fetching followers: {e}")
        return []

def get_instagram_following(access_token, user_id):
    """Fetch following from Instagram API"""
    url = f"{INSTAGRAM_API_URL}/{user_id}/following"
    params = {
        'access_token': access_token,
        'fields': 'id,username,account_type'
    }
    
    following = []
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'data' in data:
            following = data['data']
            
            # Handle pagination
            while 'paging' in data and 'next' in data['paging']:
                response = requests.get(data['paging']['next'])
                data = response.json()
                if 'data' in data:
                    following.extend(data['data'])
        
        return following
    except Exception as e:
        print(f"Error fetching following: {e}")
        return []

# ============================================================================
# ROUTES
# ============================================================================
@app.route('/')
def index():
    """Landing page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login')
def login():
    """Redirect to Instagram OAuth"""
    auth_url = (
        f"{INSTAGRAM_AUTH_URL}?"
        f"client_id={INSTAGRAM_APP_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope=user_profile,user_media&"
        f"response_type=code"
    )
    return redirect(auth_url)

@app.route('/auth/callback')
def callback():
    """Handle Instagram OAuth callback"""
    code = request.args.get('code')
    
    if not code:
        return "Error: No authorization code received", 400
    
    # Exchange code for access token
    token_data = {
        'client_id': INSTAGRAM_APP_ID,
        'client_secret': INSTAGRAM_APP_SECRET,
        'grant_type': 'authorization_code',
        'redirect_uri': REDIRECT_URI,
        'code': code
    }
    
    try:
        response = requests.post(INSTAGRAM_TOKEN_URL, data=token_data)
        data = response.json()
        
        if 'access_token' not in data:
            return f"Error: {data.get('error_message', 'Unknown error')}", 400
        
        access_token = data['access_token']
        instagram_user_id = data['user_id']
        
        # Get user info
        user_info_url = f"{INSTAGRAM_API_URL}/{instagram_user_id}"
        user_params = {
            'fields': 'id,username,account_type',
            'access_token': access_token
        }
        user_response = requests.get(user_info_url, params=user_params)
        user_data = user_response.json()
        
        username = user_data.get('username', 'unknown')
        
        # Create or update user in database
        user = User.query.filter_by(instagram_id=instagram_user_id).first()
        
        if not user:
            user = User(
                instagram_id=instagram_user_id,
                username=username,
                access_token=access_token
            )
            db.session.add(user)
        else:
            user.access_token = access_token
            user.username = username
        
        db.session.commit()
        
        # Store user in session
        session['user_id'] = user.id
        session['username'] = username
        
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        return f"Error during authentication: {str(e)}", 500

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    user = User.query.get(session['user_id'])
    
    # Get stats
    followers_count = Follower.query.filter_by(user_id=user.id).count()
    following_count = Following.query.filter_by(user_id=user.id).count()
    
    # Get unfollowers (people you follow but don't follow back)
    unfollowers = Following.query.filter_by(
        user_id=user.id,
        follows_back=False
    ).all()
    
    # Get recent unfollowers from history
    recent_unfollowers = UnfollowerHistory.query.filter_by(
        user_id=user.id
    ).order_by(UnfollowerHistory.unfollowed_at.desc()).limit(10).all()
    
    return render_template('dashboard.html',
        username=user.username,
        followers_count=followers_count,
        following_count=following_count,
        unfollowers=unfollowers,
        recent_unfollowers=recent_unfollowers,
        last_scan=user.last_scan
    )

@app.route('/scan', methods=['POST'])
@login_required
def scan():
    """Scan for new followers/following and detect unfollowers"""
    user = User.query.get(session['user_id'])
    
    try:
        # Fetch current followers
        print("Fetching followers...")
        followers_data = get_instagram_followers(user.access_token, user.instagram_id)
        
        # Fetch current following
        print("Fetching following...")
        following_data = get_instagram_following(user.access_token, user.instagram_id)
        
        # Create sets for comparison
        current_followers = {f['id']: f['username'] for f in followers_data}
        current_following = {f['id']: f['username'] for f in following_data}
        
        # Get previous followers
        previous_followers = {f.instagram_user_id: f.username for f in user.followers}
        
        # Detect unfollowers (people who were following but aren't anymore)
        unfollowers = set(previous_followers.keys()) - set(current_followers.keys())
        
        if unfollowers:
            for unfollower_id in unfollowers:
                username = previous_followers[unfollower_id]
                history = UnfollowerHistory(
                    user_id=user.id,
                    unfollower_username=username
                )
                db.session.add(history)
        
        # Clear old data
        Follower.query.filter_by(user_id=user.id).delete()
        Following.query.filter_by(user_id=user.id).delete()
        
        # Save followers
        for follower_id, username in current_followers.items():
            follows_back = follower_id in current_following
            follower = Follower(
                user_id=user.id,
                instagram_user_id=follower_id,
                username=username,
                follows_back=follows_back
            )
            db.session.add(follower)
        
        # Save following
        for following_id, username in current_following.items():
            follows_back = following_id in current_followers
            following = Following(
                user_id=user.id,
                instagram_user_id=following_id,
                username=username,
                follows_back=follows_back
            )
            db.session.add(following)
        
        # Update last scan time
        user.last_scan = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'followers': len(current_followers),
            'following': len(current_following),
            'new_unfollowers': len(unfollowers)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('index'))

# ============================================================================
# INITIALIZE DATABASE
# ============================================================================
with app.app_context():
    db.create_all()
    print("Database initialized!")

if __name__ == '__main__':
    print("="*70)
    print("Instagram OAuth Follower Tracker")
    print("="*70)
    print("\nIMPORTANT: Before running, you need to:")
    print("1. Go to https://developers.facebook.com")
    print("2. Create a new app")
    print("3. Add Instagram Basic Display product")
    print("4. Get your App ID and App Secret")
    print("5. Update INSTAGRAM_APP_ID and INSTAGRAM_APP_SECRET above")
    print("6. Add redirect URI: http://localhost:5000/auth/callback")
    print("\nStarting server at http://localhost:5000")
    print("="*70)
    
    app.run(debug=True, port=5000)