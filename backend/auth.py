import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status
from jose import JWTError, jwt
from dotenv import load_dotenv
import firebase_config

# Load environment variables
load_dotenv()

# --- Configuration ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) # 24 hours

# --- Utils ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

# --- User Management (Firestore) ---
class User:
    def __init__(self, uid: str, email: str, username: str, provider: str, provider_id: str, avatar_url: Optional[str] = None, created_at: Optional[str] = None):
        self.id = uid
        self.email = email
        self.username = username
        self.provider = provider
        self.provider_id = provider_id
        self.avatar_url = avatar_url
        self.created_at = created_at or datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            "email": self.email,
            "username": self.username,
            "provider": self.provider,
            "provider_id": self.provider_id,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at
        }

def create_or_update_oauth_user(email: str, username: str, provider: str, provider_id: str, avatar_url: Optional[str] = None):
    db = firebase_config.get_firestore_db()
    
    # Check if user exists by email
    users_ref = db.collection('users')
    query = users_ref.where('email', '==', email).limit(1).stream()
    
    existing_user_doc = None
    for doc in query:
        existing_user_doc = doc
        break
    
    if existing_user_doc:
        # Update existing user
        user_ref = users_ref.document(existing_user_doc.id)
        update_data = {
            "provider": provider,
            "provider_id": provider_id,
        }
        if avatar_url and not existing_user_doc.to_dict().get("avatar_url"):
            update_data["avatar_url"] = avatar_url

        print(f"DEBUG: Updating user {existing_user_doc.id}. Provider: {provider}") 
        user_ref.update(update_data)
        
        data = existing_user_doc.to_dict()
        # Merge updates for the return object
        data.update(update_data)
        return User(
            uid=existing_user_doc.id,
            email=data.get("email"),
            username=data.get("username"),
            provider=data.get("provider"),
            provider_id=data.get("provider_id"),
            avatar_url=data.get("avatar_url"),
            created_at=data.get("created_at")
        )
    else:
        # Create new user
        # Handle username collisions
        base_username = username
        counter = 1
        while True:
            # Check username uniqueness
            username_query = users_ref.where('username', '==', username).limit(1).stream()
            if not any(username_query):
                break
            username = f"{base_username}{counter}"
            counter += 1
            
        new_user_data = {
            "email": email,
            "username": username,
            "provider": provider,
            "provider_id": provider_id,
            "avatar_url": avatar_url,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Add to Firestore
        update_time, doc_ref = users_ref.add(new_user_data)
        print(f"DEBUG: Created new user {doc_ref.id} for email {email}")
        
        return User(
            uid=doc_ref.id,
            **new_user_data
        )

def get_user_by_email(email: str) -> Optional[User]:
    db = firebase_config.get_firestore_db()
    users_ref = db.collection('users')
    query = users_ref.where('email', '==', email).limit(1).stream()
    
    for doc in query:
        data = doc.to_dict()
        return User(
            uid=doc.id,
            email=data.get("email"),
            username=data.get("username"),
            provider=data.get("provider"),
            provider_id=data.get("provider_id"),
            avatar_url=data.get("avatar_url"),
            created_at=data.get("created_at")
        )
    return None

# --- OAuth Handlers ---
async def get_google_auth_url(redirect_uri: str):
    if not GOOGLE_CLIENT_ID:
         raise HTTPException(status_code=500, detail="Google Client ID not configured")
         
    return f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri={redirect_uri}&scope=openid%20email%20profile"

async def get_github_auth_url(redirect_uri: str):
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GitHub Client ID not configured")
        
    return f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&redirect_uri={redirect_uri}&scope=user:email"

async def exchange_google_code(code: str, redirect_uri: str, client: Any):
    # Exchange code for token
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    
    response = await client.post(token_url, data=token_data)
    response.raise_for_status()
    tokens = response.json()
    
    # Get user info
    id_token = tokens.get("id_token")
    access_token = tokens.get("access_token")
    
    user_info_response = await client.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        params={"access_token": access_token},
        headers={"Authorization": f"Bearer {access_token}"}
    )
    user_info_response.raise_for_status()
    return user_info_response.json()

async def exchange_github_code(code: str, redirect_uri: str, client: Any):
    # Exchange code for token
    token_url = "https://github.com/login/oauth/access_token"
    token_data = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": redirect_uri
    }
    
    headers = {"Accept": "application/json"}
    response = await client.post(token_url, json=token_data, headers=headers)
    response.raise_for_status()
    tokens = response.json()
    
    if "error" in tokens:
        raise Exception(tokens.get("error_description", "GitHub OAuth error"))
        
    access_token = tokens.get("access_token")
    
    # Get user info
    user_response = await client.get(
        "https://api.github.com/user",
        headers={
            "Authorization": f"token {access_token}",
            "Accept": "application/json"
        }
    )
    user_response.raise_for_status()
    user_data = user_response.json()
    
    # Get user email (it might be private)
    email = user_data.get("email")
    if not email:
        emails_response = await client.get(
            "https://api.github.com/user/emails",
            headers={
                "Authorization": f"token {access_token}",
                "Accept": "application/json"
            }
        )
        emails_response.raise_for_status()
        emails = emails_response.json()
        
        # Find primary verified email
        for e in emails:
            if e.get("primary") and e.get("verified"):
                email = e.get("email")
                break
                
    if not email:
        raise Exception("Could not retrieve email from GitHub")
        
    return {
        "email": email,
        "name": user_data.get("name") or user_data.get("login"),
        "picture": user_data.get("avatar_url"),
        "sub": str(user_data.get("id"))
    }
