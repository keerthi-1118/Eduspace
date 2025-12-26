import os
import requests
import time
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List
from database import SessionLocal
import models
import schemas
from dotenv import load_dotenv
from pydantic import BaseModel
from file_extractor import extract_text_from_file, extract_text_from_url

# Cloudinary SDK (optional - falls back to REST API if not available)
try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_SDK_AVAILABLE = True
except ImportError:
    CLOUDINARY_SDK_AVAILABLE = False
    print("Cloudinary SDK not available, using REST API instead")

# Firebase Admin and Firestore
try:
    from firebase_admin import save_note_to_firestore, get_firestore_client
    FIRESTORE_AVAILABLE = True
except ImportError:
    FIRESTORE_AVAILABLE = False
    print("Firebase Admin not available, Firestore integration disabled")

load_dotenv()

router = APIRouter()
security = HTTPBearer(auto_error=False)

# Import Firebase configuration
try:
    from firebase_config import (
        FIREBASE_PROJECT_ID, FIREBASE_API_KEY, FIREBASE_AUTH_DOMAIN,
        CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET,
        GEMINI_API_KEY, verify_env_variables
    )
    # Verify environment variables on startup
    verify_env_variables()
except ImportError:
    # Fallback to direct environment variable access
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
    FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
    FIREBASE_AUTH_DOMAIN = os.getenv("FIREBASE_AUTH_DOMAIN")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
    print("Using direct environment variable access (firebase_config not available)")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """Verify Firebase token and return user"""
    if not credentials:
        # For development, allow anonymous access (you can remove this later)
        # For production, uncomment the next line:
        # raise HTTPException(status_code=401, detail="Authentication required")
        return None
    
    token = credentials.credentials
    if not FIREBASE_API_KEY:
        # Development mode - skip auth if Firebase not configured
        return None
    
    try:
        # Verify token using Firebase REST API
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={FIREBASE_API_KEY}"
        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, json={"idToken": token}, headers=headers, timeout=5)
        
        if resp.status_code == 200:
            users = resp.json().get("users", [])
            if users:
                user_info = users[0]
                # Get or create user in database
                user = db.query(models.User).filter(models.User.uid == user_info["localId"]).first()
                if not user:
                    user = models.User(uid=user_info["localId"], email=user_info.get("email", ""))
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                return user
        raise HTTPException(status_code=401, detail="Invalid Firebase token")
    except requests.RequestException as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")

def get_user_or_create_anonymous(db: Session, user_info: Optional[dict] = None):
    """Get user from token or create anonymous user for development"""
    if user_info:
        user = db.query(models.User).filter(models.User.uid == user_info["localId"]).first()
        if not user:
            user = models.User(uid=user_info["localId"], email=user_info.get("email", ""))
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    # Anonymous user for development
    anonymous_user = db.query(models.User).filter(models.User.uid == "anonymous").first()
    if not anonymous_user:
        anonymous_user = models.User(uid="anonymous", email="anonymous@edunex.local")
        db.add(anonymous_user)
        db.commit()
        db.refresh(anonymous_user)
    return anonymous_user

# --- User endpoints (signup/login handled by Firebase frontend) ---

# --- Notes CRUD ---
@router.post("/notes/", response_model=schemas.Note)
def create_note(note: schemas.NoteCreate, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    user = current_user or get_user_or_create_anonymous(db)
    db_note = models.Note(**note.dict(), owner_id=user.id)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note

@router.get("/notes/", response_model=list[schemas.Note])
def read_notes(db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    user = current_user or get_user_or_create_anonymous(db)
    notes = db.query(models.Note).filter(models.Note.owner_id == user.id).order_by(models.Note.created_at.desc()).all()
    return notes

@router.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    user = current_user or get_user_or_create_anonymous(db)
    note = db.query(models.Note).filter(models.Note.id == note_id, models.Note.owner_id == user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return {"ok": True}

# --- Projects CRUD ---
@router.post("/projects/", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    user = current_user or get_user_or_create_anonymous(db)
    db_project = models.Project(**project.dict(), owner_id=user.id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/projects/", response_model=list[schemas.Project])
def read_projects(db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    """Get all projects user owns or is a member of"""
    user = current_user or get_user_or_create_anonymous(db)
    
    # Get owned projects
    owned_projects = db.query(models.Project).filter(models.Project.owner_id == user.id).all()
    
    # Get projects where user is a member
    memberships = db.query(models.ProjectMember).filter(models.ProjectMember.user_id == user.id).all()
    member_project_ids = [m.project_id for m in memberships]
    member_projects = db.query(models.Project).filter(models.Project.id.in_(member_project_ids)).all()
    
    # Combine and deduplicate
    all_projects = {p.id: p for p in owned_projects + member_projects}
    return list(all_projects.values())

@router.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    user = current_user or get_user_or_create_anonymous(db)
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"ok": True}

# --- Tasks CRUD ---
@router.post("/tasks/", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    user = current_user or get_user_or_create_anonymous(db)
    task_data = task.dict()
    task_data["owner_id"] = user.id
    # Ensure status is valid
    if task_data.get("status") not in [models.TaskStatus.TODO.value, models.TaskStatus.IN_PROGRESS.value, models.TaskStatus.DONE.value]:
        task_data["status"] = models.TaskStatus.TODO.value
    db_task = models.Task(**task_data)
    db.add(db_task)
    
    # Log activity if project_id exists
    if task_data.get("project_id"):
        activity = models.ProjectActivity(
            project_id=task_data["project_id"],
            user_id=user.id,
            activity_type="task_create",
            activity_data={"task_title": task_data["title"]}
        )
        db.add(activity)
    
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/tasks/", response_model=list[schemas.Task])
def read_tasks(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Get all tasks, optionally filtered by project"""
    user = current_user or get_user_or_create_anonymous(db)
    query = db.query(models.Task).filter(
        (models.Task.owner_id == user.id) | (models.Task.assignee_id == user.id)
    )
    if project_id:
        query = query.filter(models.Task.project_id == project_id)
    return query.order_by(models.Task.created_at.desc()).all()

@router.put("/tasks/{task_id}", response_model=schemas.Task)
def update_task(
    task_id: int,
    task_update: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Update a task"""
    user = current_user or get_user_or_create_anonymous(db)
    task = db.query(models.Task).filter(
        (models.Task.id == task_id) & 
        ((models.Task.owner_id == user.id) | (models.Task.assignee_id == user.id))
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    
    # Log activity if project_id exists
    if task.project_id:
        activity = models.ProjectActivity(
            project_id=task.project_id,
            user_id=user.id,
            activity_type="task_update",
            activity_data={"task_id": task_id, "task_title": task.title, "status": task.status}
        )
        db.add(activity)
    
    db.commit()
    db.refresh(task)
    return task

@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    user = current_user or get_user_or_create_anonymous(db)
    task = db.query(models.Task).filter(
        (models.Task.id == task_id) & 
        ((models.Task.owner_id == user.id) | (models.Task.assignee_id == user.id))
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    project_id = task.project_id
    
    # Log activity if project_id exists
    if project_id:
        activity = models.ProjectActivity(
            project_id=project_id,
            user_id=user.id,
            activity_type="task_delete",
            activity_data={"task_id": task_id, "task_title": task.title}
        )
        db.add(activity)
    
    db.delete(task)
    db.commit()
    return {"ok": True}

# --- Upload endpoint (supports file upload, text notes, and links) ---
@router.post("/upload")
async def upload_file(
    file: Optional[UploadFile] = File(None),
    title: Optional[str] = Form(None),
    type: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    is_public: Optional[str] = Form("false"),
    content: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Upload file, text note, or link to database"""
    try:
        print("=" * 50)
        print("UPLOAD ENDPOINT CALLED")
        print("=" * 50)
        print(f"Type: {type}")
        print(f"Title: {title}")
        print(f"Has file: {file is not None}")
        print(f"File name: {file.filename if file else None}")
        print(f"Content length: {len(content) if content else 0}")
        print(f"Content preview: {content[:100] if content else None}")
        print(f"Subject: {subject}")
        print(f"Tags: {tags}")
        print(f"Is public: {is_public}")
        print("=" * 50)
        
        # Parse tags from comma-separated string
        tag_list = []
        if tags:
            tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        
        # Determine note type - use provided type, or infer from context
        if type:
            note_type = type.upper()
        elif file:
            note_type = "FILE"
        elif content and (content.startswith("http://") or content.startswith("https://")):
            note_type = "LINK"
        elif content:
            note_type = "TEXT"
        else:
            print(f"Error: No file, content, or type provided. file={file}, content={content}, type={type}")
            raise HTTPException(status_code=400, detail="Either file, content, or URL must be provided")
        
        print(f"Determined note_type: {note_type}")
        
        # Get note title
        if not title:
            if file and file.filename:
                note_title = file.filename.split('.')[0]
            elif content and note_type == "LINK":
                # Try to extract a title from URL
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(content)
                    note_title = parsed.netloc or "Link"
                except:
                    note_title = "Untitled Link"
            else:
                note_title = "Untitled"
        else:
            note_title = title
        
        file_url = None
        file_size = 0
        content_type = "text/plain"
        
        # Handle file upload (FILE type)
        extracted_text = None
        if note_type == "FILE":
            if not file:
                raise HTTPException(status_code=400, detail="File is required for FILE type")
            # Read file content
            file_content = await file.read()
            file_size = len(file_content)
            content_type = file.content_type or "application/octet-stream"
            
            # Extract text content from file
            try:
                extracted_text = extract_text_from_file(file_content, file.filename or "unknown", content_type)
                if extracted_text and len(extracted_text.strip()) > 10:  # Only store if meaningful content extracted
                    # Truncate if too long (store first 100k chars to avoid database issues)
                    max_content_length = 100000
                    original_length = len(extracted_text)
                    if len(extracted_text) > max_content_length:
                        extracted_text = extracted_text[:max_content_length] + "\n\n[Content truncated due to length...]"
                    print(f"Extracted {original_length} characters from {file.filename} (stored: {len(extracted_text)})")
                else:
                    extracted_text = None  # Don't store empty or very short extractions
            except Exception as e:
                print(f"Error extracting text from file: {e}")
                extracted_text = None
            
            # Try Cloudinary upload if configured
            if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY:
                try:
                    # Method 1: Use Cloudinary SDK (if available)
                    if CLOUDINARY_SDK_AVAILABLE and CLOUDINARY_API_SECRET:
                        try:
                            cloudinary.config(
                                cloud_name=CLOUDINARY_CLOUD_NAME,
                                api_key=CLOUDINARY_API_KEY,
                                api_secret=CLOUDINARY_API_SECRET
                            )
                            # Upload using SDK
                            upload_result = cloudinary.uploader.upload(
                                file_content,
                                resource_type="auto",
                                folder="edunex_uploads"  # Optional: organize files in folder
                            )
                            file_url = upload_result.get('secure_url') or upload_result.get('url')
                            print(f"File uploaded to Cloudinary (SDK): {file_url}")
                        except Exception as sdk_error:
                            print(f"Cloudinary SDK upload failed: {sdk_error}, trying REST API...")
                            file_url = None
                    
                    # Method 2: Use Cloudinary REST API (fallback or if SDK not available)
                    if not file_url:
                        upload_url = f"https://api.cloudinary.com/v1_1/{CLOUDINARY_CLOUD_NAME}/auto/upload"
                        
                        # Prepare file data
                        files_data = {
                            'file': (file.filename, file_content, file.content_type)
                        }
                        
                        # Upload preset must be configured as "Unsigned" in Cloudinary dashboard
                        upload_data = {
                            'upload_preset': 'ml_default',  # Change this to your preset name if different
                        }
                        
                        cloudinary_response = requests.post(
                            upload_url,
                            files=files_data,
                            data=upload_data,
                            timeout=30
                        )
                        
                        if cloudinary_response.status_code == 200:
                            cloudinary_data = cloudinary_response.json()
                            file_url = cloudinary_data.get('secure_url') or cloudinary_data.get('url')
                            print(f"File uploaded to Cloudinary (REST API): {file_url}")
                        else:
                            error_msg = cloudinary_response.text
                            print(f"Cloudinary upload failed: {cloudinary_response.status_code} - {error_msg}")
                            file_url = None
                            
                except Exception as e:
                    # Fallback to local storage if Cloudinary fails
                    print(f"Cloudinary upload error: {e}")
                    file_url = None
            
            # Fallback to local storage if Cloudinary not configured or failed
            if not file_url:
                from datetime import datetime
                from pathlib import Path
                
                UPLOAD_DIR = Path("uploads")
                UPLOAD_DIR.mkdir(exist_ok=True)
                
                file_extension = Path(file.filename).suffix if file.filename else ""
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}{file_extension}"
                file_path = UPLOAD_DIR / filename
                
                with open(file_path, "wb") as buffer:
                    buffer.write(file_content)
                
                # Use absolute URL for local files
                file_url = f"http://localhost:8000/uploads/{filename}"
        
        # Handle LINK type
        elif note_type == "LINK":
            if not content:
                raise HTTPException(status_code=400, detail="URL is required for LINK type")
            file_url = content  # Store the URL as file_url
            content_type = "text/url"
            file_size = len(content.encode('utf-8'))
        
        # Handle TEXT type
        elif note_type == "TEXT":
            if not content:
                raise HTTPException(status_code=400, detail="Content is required for TEXT type")
            # For text notes, we don't need a file_url, store None
            file_url = None
            content_type = "text/plain"
            file_size = len(content.encode('utf-8'))
        
        # Save note to database
        user = current_user or get_user_or_create_anonymous(db)
        
        # Store content in summary field for TEXT and LINK types
        # For FILE type, store optional content/description in summary
        if note_type == "TEXT":
            note_summary = content
        elif note_type == "LINK":
            note_summary = content  # Store the URL in summary as well for reference
        else:
            note_summary = content or ""  # Optional description for files
        
        # Save to PostgreSQL/SQLite database
        db_note = models.Note(
            title=note_title,
            file_url=file_url if file_url else None,  # Store URL or None
            summary=note_summary,  # Store content/text/URL description or AI summary
            extracted_content=extracted_text,  # Store extracted text from files
            owner_id=user.id
        )
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        
        # Save metadata to Firestore (if available)
        firestore_doc_id = None
        if FIRESTORE_AVAILABLE:
            try:
                firestore_note_data = {
                    "title": note_title,
                    "file_url": file_url if file_url else None,
                    "summary": note_summary,
                    "extracted_content": extracted_text,
                    "owner_id": user.id,
                    "note_type": note_type,
                    "file_size": file_size,
                    "content_type": content_type,
                    "tags": tag_list,
                    "subject": subject or "",
                    "is_public": is_public.lower() == "true" if is_public else False,
                }
                firestore_doc_id = save_note_to_firestore(firestore_note_data)
                if firestore_doc_id:
                    print(f"Note metadata saved to Firestore: {firestore_doc_id}")
            except Exception as e:
                print(f"Warning: Failed to save to Firestore: {e}")
                # Continue even if Firestore fails - database save already succeeded
        
        # Determine response URL
        if note_type == "LINK":
            response_url = content  # Use the URL from content
        elif note_type == "TEXT":
            response_url = None  # Text notes don't have a URL
        else:
            response_url = file_url if file_url else "#"
        
        # Determine response type for frontend
        if note_type in ["TEXT", "LINK"]:
            response_type = note_type.lower()
        else:
            response_type = content_type or "application/octet-stream"
        
        return {
            "id": str(db_note.id),
            "url": response_url or "",  # Return empty string if no URL
            "title": db_note.title,
            "type": response_type,
            "tags": tag_list,
            "size": f"{(file_size / (1024 * 1024)):.2f} MB" if file_size > 0 else "0 MB",
            "uploadDate": db_note.created_at.isoformat() if db_note.created_at else None,
            "message": f"{note_type} uploaded successfully" if note_type == "FILE" else f"{note_type} saved successfully",
            "content": content if note_type in ["TEXT", "LINK"] else None,  # Include content in response
            "firestore_id": firestore_doc_id  # Include Firestore document ID if available
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# --- AI Summary Endpoint (Gemini API) ---
class SummarizeRequest(BaseModel):
    text: Optional[str] = None
    resourceId: Optional[int] = None

@router.post("/summarize")
def summarize_text(request: SummarizeRequest, db: Session = Depends(get_db)):
    """Generate summary using Gemini API"""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    
    text = request.text
    resource_id = request.resourceId
    
    # If resourceId provided, get note from database
    if resource_id and not text:
        note = db.query(models.Note).filter(models.Note.id == resource_id).first()
        if note:
            # If note already has an AI-generated summary, return it
            if note.summary and not note.summary.startswith("http") and len(note.summary) > 100:
                # Check if it looks like an AI summary (not a URL or short text)
                return {"summary": note.summary}
            
            # Try to get text from extracted content
            if note.extracted_content:
                text = note.extracted_content
            # If no extracted content, try to extract from file URL
            elif note.file_url and note.file_url.startswith("http"):
                try:
                    extracted = extract_text_from_url(note.file_url)
                    if extracted and len(extracted) > 10:
                        text = extracted
                        # Update note with extracted content
                        note.extracted_content = extracted
                        db.commit()
                except Exception as e:
                    print(f"Error extracting from URL: {e}")
                    text = f"Summarize the following document: {note.title}"
            # Fallback to title if no content available
            elif note.file_url:
                # Try to extract from local file
                try:
                    from pathlib import Path
                    file_path = Path("uploads") / Path(note.file_url).name
                    if file_path.exists():
                        with open(file_path, "rb") as f:
                            file_content = f.read()
                        extracted = extract_text_from_file(file_content, file_path.name)
                        if extracted and len(extracted) > 10:
                            text = extracted
                            note.extracted_content = extracted
                            db.commit()
                        else:
                            text = f"Summarize the following document: {note.title}"
                    else:
                        text = f"Summarize the following document: {note.title}"
                except Exception as e:
                    print(f"Error extracting from local file: {e}")
                    text = f"Summarize the following document: {note.title}"
            else:
                # Use summary field if it contains content (for TEXT/LINK notes)
                if note.summary:
                    text = note.summary
                else:
                    text = f"Summarize the following document: {note.title}"
    
    if not text:
        raise HTTPException(status_code=400, detail="Text or resourceId required")
    
    try:
        # Use Gemini API
        # Limit text length to avoid token limits (Gemini has limits)
        max_text_length = 30000  # Approximate token limit
        if len(text) > max_text_length:
            text = text[:max_text_length] + "\n\n[Content truncated due to length...]"
        
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"You are an expert academic assistant. Summarize the following study material, extracting the key concepts, definitions, and main arguments. Present it in a clear, concise format suitable for a student's review. Focus on the most important information and structure it well.\n\n---\n\n{text}"
                }]
            }]
        }
        
        response = requests.post(api_url, json=payload, timeout=60)  # Increased timeout for large files
        
        if response.status_code == 200:
            result = response.json()
            # Extract text from Gemini response
            if "candidates" in result and len(result["candidates"]) > 0:
                summary_text = result["candidates"][0]["content"]["parts"][0]["text"]
                
                # Save summary to database if resourceId provided
                if resource_id:
                    note = db.query(models.Note).filter(models.Note.id == resource_id).first()
                    if note:
                        note.summary = summary_text
                        db.commit()
                
                return {"summary": summary_text}
            else:
                raise HTTPException(status_code=400, detail="Invalid response from Gemini API")
        else:
            error_detail = response.text
            raise HTTPException(status_code=response.status_code, detail=f"Gemini API error: {error_detail}")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to call Gemini API: {str(e)}")

# --- Search Endpoint ---
@router.get("/search")
def search_notes(
    q: str,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Search notes by title, content, or summary"""
    user = current_user or get_user_or_create_anonymous(db)
    
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
    
    search_query = f"%{q.strip()}%"
    
    # Search in title, summary, and extracted_content
    notes = db.query(models.Note).filter(
        models.Note.owner_id == user.id
    ).filter(
        (models.Note.title.ilike(search_query)) |
        (models.Note.summary.ilike(search_query)) |
        (models.Note.extracted_content.ilike(search_query))
    ).order_by(models.Note.created_at.desc()).all()
    
    return notes

# --- Projects Search ---
@router.get("/projects/search")
def search_projects(
    q: str,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Search projects by title or description"""
    user = current_user or get_user_or_create_anonymous(db)
    
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
    
    search_query = f"%{q.strip()}%"
    
    projects = db.query(models.Project).filter(
        models.Project.owner_id == user.id
    ).filter(
        (models.Project.title.ilike(search_query)) |
        (models.Project.description.ilike(search_query))
    ).order_by(models.Project.created_at.desc()).all()
    
    return projects

# --- Tasks Search ---
@router.get("/tasks/search")
def search_tasks(
    q: str,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Search tasks by title, description, or status"""
    user = current_user or get_user_or_create_anonymous(db)
    
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
    
    search_query = f"%{q.strip()}%"
    
    tasks = db.query(models.Task).filter(
        models.Task.owner_id == user.id
    ).filter(
        (models.Task.title.ilike(search_query)) |
        (models.Task.description.ilike(search_query)) |
        (models.Task.status.ilike(search_query))
    ).order_by(models.Task.created_at.desc()).all()
    
    return tasks
