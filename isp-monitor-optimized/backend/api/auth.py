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

# Enhanced authentication system
users_db = {}
token_blacklist = set()
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_TIME = timedelta(minutes=15)

def is_account_locked(username):
    """Check if account is temporarily locked due to failed attempts"""
    user = users_db.get(username)
    if not user:
        return False
        
    if user.get('failed_attempts', 0) >= MAX_LOGIN_ATTEMPTS:
        lock_time = user.get('lock_time')
        if lock_time and datetime.utcnow() < lock_time + LOCKOUT_TIME:
            return True
    return False

def record_failed_attempt(username):
    """Record failed login attempt"""
    if username not in users_db:
        return
        
    user = users_db[username]
    user['failed_attempts'] = user.get('failed_attempts', 0) + 1
    
    if user['failed_attempts'] >= MAX_LOGIN_ATTEMPTS:
        user['lock_time'] = datetime.utcnow()
        logger.warning(f"Account locked for user: {username}")

def reset_login_attempts(username):
    """Reset failed attempts counter on successful login"""
    if username in users_db:
        users_db[username]['failed_attempts'] = 0
        users_db[username]['lock_time'] = None

# Permissions mapping
PERMISSIONS = {
    'user': ['view_detections'],
    'operator': ['view_detections', 'upload_images'],
    'admin': ['manage_users', 'manage_cameras', 'view_reports']
}

def generate_tokens(user_id):
    """Generate access and refresh tokens for authenticated user"""
    user_data = users_db.get(user_id, {})
    
    # Access token payload
    access_payload = {
        'user_id': user_id,
        'role': user_data.get('role', 'user'),
        'permissions': user_data.get('permissions', PERMISSIONS.get(user_data.get('role', 'user'), [])),
        'exp': datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
        'type': 'access'
    }
    
    # Refresh token payload
    refresh_payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        'type': 'refresh'
    }
    
    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm='HS256')
    refresh_token = jwt.encode(refresh_payload, JWT_REFRESH_SECRET, algorithm='HS256')
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': TOKEN_EXPIRE_MINUTES * 60
    }

def refresh_access_token(refresh_token):
    """Generate new access token using refresh token"""
    try:
        payload = jwt.decode(refresh_token, JWT_REFRESH_SECRET, algorithms=['HS256'])
        if payload.get('type') != 'refresh':
            return None
            
        user_id = payload['user_id']
        if user_id not in users_db:
            return None
            
        return generate_tokens(user_id)
        
    except jwt.ExpiredSignatureError:
        logger.warning(f"Expired refresh token attempt for user {user_id}")
        return None
    except jwt.InvalidTokenError:
        logger.warning("Invalid refresh token attempt")
        return None

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
    """Verify JWT token with additional checks"""
    if token in token_blacklist:
        logger.warning("Blacklisted token attempt")
        return None
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        
        # Additional validation
        if payload.get('type') != 'access':
            logger.warning("Invalid token type")
            return None
            
        if payload['user_id'] not in users_db:
            logger.warning(f"Token for non-existent user: {payload['user_id']}")
            return None
            
        return payload
            
    except jwt.ExpiredSignatureError:
        logger.debug("Expired token attempt")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return None

def logout(token):
    """Invalidate token by adding it to blacklist"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        expiry = payload['exp'] - datetime.utcnow().timestamp()
        if expiry > 0:  # Only blacklist if token hasn't expired
            token_blacklist.add(token)
            logger.info(f"User {payload['user_id']} logged out")
            return True
    except:
        pass
    return False

def token_required(f):
    """Decorator to require valid JWT token with enhanced security"""
    @wraps(f)
    @limiter.limit("100 per minute")  # Rate limit protected endpoints
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            logger.warning("Missing token in request")
            return jsonify({
                'error': 'authentication_required',
                'message': 'Token is missing'
            }), 401
            
        payload = verify_token(token)
        if not payload:
            return jsonify({
                'error': 'invalid_token',
                'message': 'Token is invalid or expired'
            }), 401
        
        # Check if account is locked
        if is_account_locked(payload['user_id']):
            return jsonify({
                'error': 'account_locked',
                'message': 'Account temporarily locked due to multiple failed attempts'
            }), 403
        
        # Add user info to kwargs
        kwargs['current_user'] = {
            'username': payload['user_id'],
            'is_admin': payload.get('role') == 'admin',
            'permissions': payload.get('permissions', []),
            'token_exp': payload['exp']
        }
        
        # Log access
        logger.info(f"Authorized access for user: {payload['user_id']}")
            
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
