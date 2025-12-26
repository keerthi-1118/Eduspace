import os
import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from database import SessionLocal
import models
import schemas
from routes import get_current_user, get_user_or_create_anonymous

router = APIRouter(prefix="/ai", tags=["AI"])

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def call_gemini_api(prompt: str, context: Optional[str] = None, max_tokens: int = 2000):
    """Call Gemini API for text generation"""
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    
    full_prompt = prompt
    if context:
        full_prompt = f"Context: {context}\n\n{prompt}"
    
    try:
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            json={
                "contents": [{
                    "parts": [{"text": full_prompt}]
                }]
            },
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        
        if "candidates" in result and len(result["candidates"]) > 0:
            return result["candidates"][0]["content"]["parts"][0]["text"]
        else:
            raise HTTPException(status_code=500, detail="No response from AI")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"AI API error: {str(e)}")

# AI Mentor
@router.post("/mentor")
async def ai_mentor(
    request: schemas.AIMentorRequest,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """AI Mentor for debugging, documentation, and workflow assistance"""
    user = current_user or get_user_or_create_anonymous(db)
    
    context = ""
    if request.project_id:
        project = db.query(models.Project).filter(models.Project.id == request.project_id).first()
        if project:
            # Get project files as context
            files_context = []
            for file in project.files[:10]:  # Limit to 10 files
                files_context.append(f"File: {file.file_path}\n{file.content[:500]}")
            context = "\n\n".join(files_context)
            
            # Get project tasks
            tasks = db.query(models.Task).filter(models.Task.project_id == request.project_id).all()
            if tasks:
                tasks_context = "\n".join([f"- {t.title}: {t.status}" for t in tasks[:10]])
                context += f"\n\nTasks:\n{tasks_context}"
    
    prompt = f"""You are an AI coding mentor. Help the user with their request.

User request: {request.prompt}

Provide helpful, clear, and concise assistance. If it's about code, provide code examples. If it's about workflow, provide step-by-step guidance.
"""
    
    response = await call_gemini_api(prompt, context)
    return {"response": response, "type": "mentor"}

# AI Summarizer
@router.post("/summarize")
async def ai_summarize(
    request: schemas.AISummaryRequest,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """AI Summarizer for notes, chat, or projects"""
    user = current_user or get_user_or_create_anonymous(db)
    
    text_to_summarize = request.text
    
    if request.resource_id and request.resource_type:
        if request.resource_type == "note":
            note = db.query(models.Note).filter(models.Note.id == request.resource_id).first()
            if note:
                text_to_summarize = note.extracted_content or note.summary or note.title
        elif request.resource_type == "chat":
            # Get chat messages
            messages = db.query(models.ChatMessage).filter(
                models.ChatMessage.project_id == request.resource_id
            ).order_by(models.ChatMessage.created_at).limit(100).all()
            text_to_summarize = "\n".join([f"{m.user.email if m.user else 'User'}: {m.message}" for m in messages])
        elif request.resource_type == "project":
            project = db.query(models.Project).filter(models.Project.id == request.resource_id).first()
            if project:
                text_to_summarize = f"{project.title}\n{project.description}"
                # Include tasks
                tasks = db.query(models.Task).filter(models.Task.project_id == request.resource_id).all()
                if tasks:
                    text_to_summarize += f"\n\nTasks:\n" + "\n".join([f"- {t.title}" for t in tasks])
    
    if not text_to_summarize:
        raise HTTPException(status_code=400, detail="No text to summarize")
    
    prompt = f"""Please provide a concise summary of the following content. Focus on key points, main ideas, and important details.

Content:
{text_to_summarize[:10000]}  # Limit to 10k chars

Summary:"""
    
    response = await call_gemini_api(prompt, max_tokens=1000)
    return {"summary": response, "type": "summary"}

# AI StudyFlow
@router.post("/studyflow")
async def ai_studyflow(
    request: schemas.AIStudyFlowRequest,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """AI StudyFlow: Convert notes to summaries or flashcards"""
    user = current_user or get_user_or_create_anonymous(db)
    
    note = db.query(models.Note).filter(models.Note.id == request.note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    content = note.extracted_content or note.summary or note.title
    if not content:
        raise HTTPException(status_code=400, detail="Note has no content to convert")
    
    if request.format == "flashcards":
        prompt = f"""Convert the following content into flashcards in JSON format. Each flashcard should have a "question" and "answer" field.

Content:
{content[:5000]}

Format the response as a JSON array of flashcards. Example format:
[
  {{"question": "What is...?", "answer": "It is..."}},
  {{"question": "How does...?", "answer": "It works by..."}}
]

Flashcards:"""
    else:  # summary
        prompt = f"""Create a comprehensive study summary from the following content. Organize it into clear sections with key concepts, definitions, and important points.

Content:
{content[:5000]}

Study Summary:"""
    
    response = await call_gemini_api(prompt, max_tokens=2000)
    
    return {
        "format": request.format,
        "content": response,
        "note_id": request.note_id
    }

# AI Resource Finder
@router.post("/resource-finder")
async def ai_resource_finder(
    request: schemas.AIResourceFinderRequest,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """AI Resource Finder: Suggest related materials for projects"""
    user = current_user or get_user_or_create_anonymous(db)
    
    context = ""
    if request.project_id:
        project = db.query(models.Project).filter(models.Project.id == request.project_id).first()
        if project:
            context = f"Project: {project.title}\nDescription: {project.description}\n"
            # Get project files to understand tech stack
            file_types = set([f.file_type for f in project.files])
            if file_types:
                context += f"Technologies: {', '.join(file_types)}\n"
    
    prompt = f"""Based on the following query and context, suggest relevant learning resources, documentation, tutorials, or tools that would be helpful.

Query: {request.query}
{context}

Provide a list of suggestions with:
1. Resource name
2. Type (documentation, tutorial, tool, etc.)
3. Brief description
4. Why it's relevant

Suggestions:"""
    
    response = await call_gemini_api(prompt, max_tokens=1500)
    
    return {
        "query": request.query,
        "suggestions": response,
        "project_id": request.project_id
    }

