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
        'role': 'admin',
        'permissions': ['manage_users', 'manage_cameras', 'view_reports']
    }
}

# Permissions mapping
PERMISSIONS = {
    'user': ['view_detections'],
    'operator': ['view_detections', 'upload_images'],
    'admin': ['manage_users', 'manage_cameras', 'view_reports']
}

def generate_token(user_id):
    """Generate JWT token for authenticated user"""
    user_data = users_db.get(user_id, {})
    payload = {
        'user_id': user_id,
        'role': user_data.get('role', 'user'),
        'permissions': user_data.get('permissions', PERMISSIONS.get(user_data.get('role', 'user'), [])),
        'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def register_user(username, password, role='user', custom_permissions=None):
    """Register a new user with specific permissions"""
    if username in users_db:
        return False
    
    permissions = custom_permissions if custom_permissions else PERMISSIONS.get(role, [])
    
    users_db[username] = {
        'password': password,
        'role': role,
        'permissions': permissions,
        'reset_token': None,
        'reset_expires': None
    }
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
        
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
            
        payload = verify_token(token)
        if not payload:
            return jsonify({'message': 'Token is invalid or expired'}), 401
        
        kwargs['current_user'] = {
            'username': payload['user_id'],
            'is_admin': payload.get('role') == 'admin',
            'permissions': payload.get('permissions', [])
        }
            
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
        
        kwargs['current_user'] = {
            'username': payload['user_id'],
            'is_admin': True,
            'permissions': payload.get('permissions', [])
        }
            
        return f(*args, **kwargs)
    
    return decorated

def permission_required(permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            
            if 'Authorization' in request.headers:
                token = request.headers['Authorization'].split(' ')[1]
            
            if not token:
                return jsonify({'message': 'Token is missing'}), 401
                
            payload = verify_token(token)
            if not payload:
                return jsonify({'message': 'Token is invalid or expired'}), 401
            
            user_permissions = payload.get('permissions', [])
            if permission not in user_permissions and payload.get('role') != 'admin':
                return jsonify({'message': f'Permission {permission} required'}), 403
            
            kwargs['current_user'] = {
                'username': payload['user_id'],
                'is_admin': payload.get('role') == 'admin',
                'permissions': user_permissions
            }
                
            return f(*args, **kwargs)
        
        return decorated
    return decorator

# Helper functions for password reset (keep existing implementation)
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
