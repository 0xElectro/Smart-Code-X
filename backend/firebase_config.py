import firebase_admin
from firebase_admin import credentials, firestore, storage
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Firebase App
if not firebase_admin._apps:
    cred_path = "serviceAccountKey.json"
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
        })
    else:
        print("Warning: serviceAccountKey.json not found. Firebase features will not work.")

def get_firestore_db():
    try:
        return firestore.client()
    except Exception as e:
        print(f"Error getting Firestore client: {e}")
        return None

def get_storage_bucket():
    try:
        return storage.bucket()
    except Exception as e:
        print(f"Error getting Storage bucket: {e}")
        return None
