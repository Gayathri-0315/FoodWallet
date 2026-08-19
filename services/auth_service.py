import uuid
from datetime import datetime, timezone, timedelta
import jwt
from functools import wraps
from flask import request, jsonify, g, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Wallet, TokenBlocklist

# In-memory rate limiting dictionary { key: [timestamps] }
_rate_limits = {}

def check_rate_limit(key, max_requests=5, window_seconds=60):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=window_seconds)
    
    timestamps = _rate_limits.get(key, [])
    # filter out old timestamps
    timestamps = [t for t in timestamps if t > cutoff]
    
    if len(timestamps) >= max_requests:
        return False
    
    timestamps.append(now)
    _rate_limits[key] = timestamps
    return True

def hash_password(password):
    return generate_password_hash(password)

def verify_password(password_hash, password):
    return check_password_hash(password_hash, password)

def generate_jwt_token(user_id, role):
    now = datetime.now(timezone.utc)
    jti = str(uuid.uuid4())
    payload = {
        'sub': user_id,
        'role': role,
        'jti': jti,
        'iat': now,
        'exp': now + timedelta(days=7)
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def decode_jwt_token(token):
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        jti = payload.get('jti')
        if jti and db.session.query(TokenBlocklist).filter_by(jti=jti).first():
            return None # Revoked
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def revoke_token(token):
    payload = decode_jwt_token(token)
    if payload and 'jti' in payload:
        try:
            blocked = TokenBlocklist(jti=payload['jti'])
            db.session.add(blocked)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
    return False

def get_auth_token_from_request():
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    return request.args.get('token')

def customer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_auth_token_from_request()
        if not token:
            return jsonify({'error': 'Authentication token is missing', 'code': 'UNAUTHORIZED'}), 401
        
        payload = decode_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Token is invalid or expired', 'code': 'EXPIRED_TOKEN'}), 401
        
        user = db.session.get(User, payload['sub'])
        if not user or user.role != 'customer':
            return jsonify({'error': 'Customer authorization required', 'code': 'FORBIDDEN'}), 403
        
        g.user = user
        return f(*args, **kwargs)
    return decorated

def vendor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_auth_token_from_request()
        if not token:
            return jsonify({'error': 'Authentication token is missing', 'code': 'UNAUTHORIZED'}), 401
        
        payload = decode_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Token is invalid or expired', 'code': 'EXPIRED_TOKEN'}), 401
        
        if payload.get('role') != 'vendor':
            return jsonify({'error': 'Vendor authorization required. Access denied.', 'code': 'FORBIDDEN'}), 403
        
        user = db.session.get(User, payload['sub'])
        if not user or user.role != 'vendor':
            return jsonify({'error': 'Vendor authorization required. Access denied.', 'code': 'FORBIDDEN'}), 403
        
        g.user = user
        return f(*args, **kwargs)
    return decorated
