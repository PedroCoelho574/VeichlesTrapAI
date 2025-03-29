from functools import wraps
from flask import request, jsonify
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
TOKEN_EXPIRE_HOURS = 24

# User database simulation (in production, use a real database)
users_db = {
    'admin': {
        'password': os.getenv('ADMIN_PASSWORD', 'admin123'),
        'role': 'admin'
    }
}

def generate_token(user_id):
    """Generate JWT token for authenticated user"""
    payload = {
        'user_id': user_id,
        'role': users_db.get(user_id, {}).get('role', 'user'),
        'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def register_user(username, password, role='user'):
    """Register a new user"""
    if username in users_db:
        return False
    users_db[username] = {
        'password': password,
        'role': role,
        'reset_token': None,
        'reset_expires': None
    }
    return True

def generate_reset_token(username):
    """Generate password reset token"""
    if username not in users_db:
        return None
    
    token = jwt.encode(
        {'user': username, 'exp': datetime.utcnow() + timedelta(hours=1)},
        SECRET_KEY,
        algorithm='HS256'
    )
    
    users_db[username]['reset_token'] = token
    users_db[username]['reset_expires'] = datetime.utcnow() + timedelta(hours=1)
    return token

def verify_reset_token(token):
    """Verify password reset token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        username = payload['user']
        
        if (users_db.get(username, {}).get('reset_token') == token and
            datetime.utcnow() < users_db[username]['reset_expires']):
            return username
    except:
        return None
    return None

def reset_password(username, new_password):
    """Reset user password"""
    if username not in users_db:
        return False
    
    users_db[username]['password'] = new_password
    users_db[username]['reset_token'] = None
    users_db[username]['reset_expires'] = None
    return True

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from headers
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
            
        payload = verify_token(token)
        if not payload:
            return jsonify({'message': 'Token is invalid or expired'}), 401
            
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
            
        payload = verify_token(token)
        if not payload or payload.get('role') != 'admin':
            return jsonify({'message': 'Admin privileges required'}), 403
            
        return f(*args, **kwargs)
    
    return decorated