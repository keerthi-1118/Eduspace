from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import Optional, List
from database import SessionLocal
import models
import schemas
from routes import get_current_user, get_user_or_create_anonymous

router = APIRouter(prefix="/projects", tags=["Chat"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_project_access(project_id: int, user: models.User, db: Session):
    """Check if user has access to project"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.owner_id == user.id:
        return project
    
    membership = db.query(models.ProjectMember).filter(
        and_(
            models.ProjectMember.project_id == project_id,
            models.ProjectMember.user_id == user.id
        )
    ).first()
    
    if not membership and not project.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return project

# Chat Messages
@router.get("/{project_id}/chat", response_model=List[schemas.ChatMessage])
async def get_chat_messages(
    project_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Get chat messages for a project"""
    user = current_user or get_user_or_create_anonymous(db)
    project = check_project_access(project_id, user, db)
    
    messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.project_id == project_id
    ).order_by(desc(models.ChatMessage.created_at)).limit(limit).all()
    
    # Reverse to show oldest first
    return list(reversed(messages))

@router.post("/{project_id}/chat", response_model=schemas.ChatMessage)
async def send_chat_message(
    project_id: int,
    message: schemas.ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Send a chat message"""
    user = current_user or get_user_or_create_anonymous(db)
    project = check_project_access(project_id, user, db)
    
    db_message = models.ChatMessage(
        project_id=project_id,
        user_id=user.id,
        message=message.message
    )
    db.add(db_message)
    
    # Log activity
    activity = models.ProjectActivity(
        project_id=project_id,
        user_id=user.id,
        activity_type="chat_message",
        activity_data={"message_preview": message.message[:50]}
    )
    db.add(activity)
    
    db.commit()
    db.refresh(db_message)
    return db_message

@router.delete("/{project_id}/chat/{message_id}")
async def delete_chat_message(
    project_id: int,
    message_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Delete a chat message (only own messages or if leader)"""
    user = current_user or get_user_or_create_anonymous(db)
    project = check_project_access(project_id, user, db)
    
    db_message = db.query(models.ChatMessage).filter(
        and_(
            models.ChatMessage.id == message_id,
            models.ChatMessage.project_id == project_id
        )
    ).first()
    if not db_message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if user can delete (owner of message or project leader)
    can_delete = (
        db_message.user_id == user.id or
        project.owner_id == user.id or
        db.query(models.ProjectMember).filter(
            and_(
                models.ProjectMember.project_id == project_id,
                models.ProjectMember.user_id == user.id,
                models.ProjectMember.role == models.ProjectRole.LEADER.value
            )
        ).first()
    )
    
    if not can_delete:
        raise HTTPException(status_code=403, detail="Cannot delete this message")
    
    db.delete(db_message)
    db.commit()
    return {"message": "Message deleted successfully"}

