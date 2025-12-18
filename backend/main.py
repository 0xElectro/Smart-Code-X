import os
import time
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv
import uuid
import urllib.parse

import auth
import firebase_config
import orchestrator
import zipfile
import shutil
import tempfile


# Load environment variables
load_dotenv()

app = FastAPI(title="SmartCodeX Backend")

# Auth Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Models ---
class UserUpdate(BaseModel):
    username: str

class ReviewCreate(BaseModel):
    file_name: str
    total_issues: int
    issues: List[dict]
    # Add other fields as necessary from ReviewResult type

class ReviewResponse(BaseModel):
    id: str
    file_name: str
    total_issues: int
    created_at: str
    # Simplified for list view

# --- CORS Configuration ---
origins = [
    "http://localhost:5173",  # Vite Dev Server
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Dependencies ---
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = auth.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    email = payload.get("sub")
    user = auth.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# --- Auth Routes ---

@app.get("/auth/google/login")
async def login_google():
    redirect_uri = "http://localhost:8000/auth/google/callback"
    return RedirectResponse(await auth.get_google_auth_url(redirect_uri))

@app.get("/auth/google/callback")
async def callback_google(code: str):
    redirect_uri = "http://localhost:8000/auth/google/callback"
    async with httpx.AsyncClient() as client:
        try:
            user_info = await auth.exchange_google_code(code, redirect_uri, client)
            print(f"DEBUG: Google User Info: {user_info}")
        except Exception as e:
             print(f"DEBUG: Google Exchange Error: {e}")
             raise HTTPException(status_code=400, detail=f"Google OAuth failed: {str(e)}")

    try:
        user = auth.create_or_update_oauth_user(
            email=user_info["email"],
            username=user_info.get("name", "").replace(" ", "_").lower(), # Fallback username
            provider="google",
            provider_id=user_info["id"],
            avatar_url=user_info.get("picture")
        )
    except Exception as e:
        print(f"DEBUG: Firestore Create/Update Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    # Create JWT
    access_token = auth.create_access_token(data={"sub": user.email})
    
    # Redirect to frontend with token
    return RedirectResponse(f"http://localhost:5173/auth/callback?token={access_token}")

@app.get("/auth/github/login")
async def login_github():
    redirect_uri = "http://localhost:8000/auth/github/callback"
    return RedirectResponse(await auth.get_github_auth_url(redirect_uri))

@app.get("/auth/github/callback")
async def callback_github(code: str):
    redirect_uri = "http://localhost:8000/auth/github/callback"
    async with httpx.AsyncClient() as client:
        try:
             user_info = await auth.exchange_github_code(code, redirect_uri, client)
             print(f"DEBUG: GitHub User Info: {user_info}")
        except Exception as e:
            print(f"DEBUG: GitHub Exchange Error: {e}")
            raise HTTPException(status_code=400, detail=f"GitHub OAuth failed: {str(e)}")

    try:
        user = auth.create_or_update_oauth_user(
            email=user_info["email"],
            username=user_info["name"].replace(" ", "_").lower(), # Fallback username
            provider="github",
            provider_id=user_info["sub"],
            avatar_url=user_info.get("picture")
        )
    except Exception as e:
        print(f"DEBUG: Firestore Create/Update Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    # Create JWT
    access_token = auth.create_access_token(data={"sub": user.email})
    
    # Redirect to frontend with token
    return RedirectResponse(f"http://localhost:5173/auth/callback?token={access_token}")

@app.get("/auth/me")
async def read_users_me(current_user: auth.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "createdAt": current_user.created_at,
        "avatar_url": current_user.avatar_url
    }

@app.post("/auth/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: auth.User = Depends(get_current_user)
):
    try:
        bucket = firebase_config.get_storage_bucket()
        if not bucket:
            raise HTTPException(status_code=500, detail="Storage not configured")

        # Create unique filename
        file_extension = os.path.splitext(file.filename)[1]
        blob_name = f"avatars/{current_user.id}_{int(time.time())}{file_extension}"
        blob = bucket.blob(blob_name)

        # Generate unique token for the file
        new_token = str(uuid.uuid4())
        metadata = {"firebaseStorageDownloadTokens": new_token}
        blob.metadata = metadata

        # Upload file
        blob.upload_from_file(file.file, content_type=file.content_type)
        
        # Construct token-based URL
        encoded_blob_name = urllib.parse.quote(blob_name, safe='')
        avatar_url = f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}/o/{encoded_blob_name}?alt=media&token={new_token}"

        # Update Firestore
        db = firebase_config.get_firestore_db()
        users_ref = db.collection('users')
        users_ref.document(current_user.id).update({"avatar_url": avatar_url})
        
        return {"avatar_url": avatar_url}
    except Exception as e:
        print(f"DEBUG: Avatar Upload Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/auth/profile")
async def update_profile(
    user_update: UserUpdate,
    current_user: auth.User = Depends(get_current_user)
):
    db = firebase_config.get_firestore_db()
    users_ref = db.collection('users')
    
    # Check uniqueness
    query = users_ref.where('username', '==', user_update.username).limit(1).stream()
    existing_user_doc = None
    for doc in query:
        existing_user_doc = doc
        break
        
    if existing_user_doc and existing_user_doc.id != current_user.id:
        raise HTTPException(status_code=400, detail="Username already taken")

    # Update
    users_ref.document(current_user.id).update({"username": user_update.username})
    
    # Return updated user structure
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": user_update.username,
        "createdAt": current_user.created_at,
        "avatar_url": current_user.avatar_url
    }

# --- Review Routes ---

@app.get("/reviews")
async def get_reviews(current_user: auth.User = Depends(get_current_user)):
    db = firebase_config.get_firestore_db()
    
    # Query reviews by user_id
    reviews_ref = db.collection('reviews')
    query = reviews_ref.where('user_id', '==', current_user.id).order_by('created_at', direction=firebase_config.firestore.Query.DESCENDING).stream()
    
    reviews = []
    for doc in query:
        data = doc.to_dict()
        data['id'] = doc.id
        reviews.append(data)
        
    return reviews

@app.post("/reviews")
async def create_review(
    review: dict, # Accept generic dict for flexibility or define strict schema
    current_user: auth.User = Depends(get_current_user)
):
    db = firebase_config.get_firestore_db()
    reviews_ref = db.collection('reviews')
    
    new_review = review.copy()
    new_review['user_id'] = current_user.id
    new_review['created_at'] = datetime.utcnow().isoformat()
    
    update_time, doc_ref = reviews_ref.add(new_review)
    
    new_review['id'] = doc_ref.id
    return new_review

@app.delete("/reviews/{review_id}")
async def delete_review(
    review_id: str,
    current_user: auth.User = Depends(get_current_user)
):
    db = firebase_config.get_firestore_db()
    review_ref = db.collection('reviews').document(review_id)
    
    # Check ownership
    review = review_ref.get()
    if not review.exists:
        raise HTTPException(status_code=404, detail="Review not found")
        
    review_data = review.to_dict()
    if review_data.get('user_id') != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this review")
        

    # Delete
    review_ref.delete()
    return {"status": "success"}

# --- Analysis Routes ---

@app.post("/analyze/upload-zip")
async def analyze_uploaded_zip(
    file: UploadFile = File(...),
    current_user: auth.User = Depends(get_current_user)
):
    path_to_zip = ""
    extract_folder = ""
    
    try:
        # Check if file is zip
        if not file.filename.endswith(".zip"):
            raise HTTPException(status_code=400, detail="Only ZIP files are allowed")

        # 1. Save ZIP locally to temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
            path_to_zip = tmp_zip.name
            shutil.copyfileobj(file.file, tmp_zip)

        # 2. Extract ZIP
        extract_folder = tempfile.mkdtemp()
        with zipfile.ZipFile(path_to_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_folder)

        # 3. Upload extracted files to Firebase Storage
        bucket = firebase_config.get_storage_bucket()
        if not bucket:
             raise HTTPException(status_code=500, detail="Storage not configured")
        
        project_id = str(uuid.uuid4())
        # Cloud path: projects/{user_id}/{project_id}/...
        cloud_base_path = f"projects/{current_user.id}/{project_id}/"
        
        print(f"DEBUG: Uploading extracted files to {cloud_base_path}")
        
        files_uploaded = 0
        for root, dirs, files in os.walk(extract_folder):
            for filename in files:
                local_path = os.path.join(root, filename)
                # Relative path in the zip
                relative_path = os.path.relpath(local_path, extract_folder)
                # Cloud blob path
                blob_path = f"{cloud_base_path}{relative_path}"
                
                blob = bucket.blob(blob_path)
                blob.upload_from_filename(local_path)
                files_uploaded += 1
        
        print(f"DEBUG: Uploaded {files_uploaded} files to cloud.")

        # 4. Trigger Analysis via Orchestrator (Cloud Based)
        # The orchestrator will download from cloud_base_path and analyze
        print(f"DEBUG: Triggering orchestrator for {cloud_base_path}")
        try:
            analysis_result = orchestrator.run_analysis_from_cloud(cloud_base_path)
        except Exception as e:
             # Log full trace
             import traceback
             traceback.print_exc()
             raise HTTPException(status_code=500, detail=f"Orchestrator failed: {str(e)}")

        # 5. Store Review Result in Firestore
        # Convert analysis result to match Review schema if needed
        # For now, we return the raw orchestrator result or save it
        
        # Determine total issues
        total_issues = 0
        issues = []
        
        # Example structure from orchestrator:
        # { "agents": { "SAA": [issues...], "SCAA": {...}, ... } }
        
        # Flatten SAA issues for simple count
        if "agents" in analysis_result and "SAA" in analysis_result["agents"]:
            saa_issues = analysis_result["agents"]["SAA"]
            if isinstance(saa_issues, list):
                total_issues += len(saa_issues)
                issues.extend(saa_issues)
        
        # Create Review Record
        db = firebase_config.get_firestore_db()
        reviews_ref = db.collection('reviews')
        
        new_review = {
            "user_id": current_user.id,
            "project_id": project_id,
            "file_name": file.filename, # Using zip name as ref
            "total_issues": total_issues,
            "issues": issues, # Stores SAA issues mainly
            "raw_analysis": analysis_result, # Store full detailed result
            "created_at": datetime.utcnow().isoformat(),
            "cloud_path": cloud_base_path
        }
        
        update_time, doc_ref = reviews_ref.add(new_review)
        new_review['id'] = doc_ref.id
        
        return new_review

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"DEBUG: Upload/Analyze Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup local temps
        if path_to_zip and os.path.exists(path_to_zip):
            os.remove(path_to_zip)
        if extract_folder and os.path.exists(extract_folder):
            shutil.rmtree(extract_folder)

@app.get("/")
def read_root():
    return {"message": "Welcome to SmartCodeX Backend (Firebase Enabled)"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
