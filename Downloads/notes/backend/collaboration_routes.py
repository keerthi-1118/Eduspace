import os
import secrets
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Optional, List
from database import SessionLocal
import models
import schemas
from routes import get_current_user, get_user_or_create_anonymous

router = APIRouter(prefix="/collaboration", tags=["Collaboration"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Project Members Management
@router.get("/projects/{project_id}/members", response_model=List[schemas.ProjectMember])
async def get_project_members(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Get all members of a project"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if user has access
    user = current_user or get_user_or_create_anonymous(db)
    is_member = (
        project.owner_id == user.id or
        db.query(models.ProjectMember).filter(
            and_(
                models.ProjectMember.project_id == project_id,
                models.ProjectMember.user_id == user.id
            )
        ).first()
    )
    if not is_member and not project.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return project.members

@router.post("/projects/{project_id}/members", response_model=schemas.ProjectMember)
async def add_project_member(
    project_id: int,
    member: schemas.ProjectMemberBase,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Add a member to a project (requires leader role)"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    user = current_user or get_user_or_create_anonymous(db)
    
    # Check if user is leader or owner
    is_leader = project.owner_id == user.id
    if not is_leader:
        membership = db.query(models.ProjectMember).filter(
            and_(
                models.ProjectMember.project_id == project_id,
                models.ProjectMember.user_id == user.id,
                models.ProjectMember.role == models.ProjectRole.LEADER.value
            )
        ).first()
        if not membership:
            raise HTTPException(status_code=403, detail="Only leaders can add members")
    
    # Check if member already exists
    existing = db.query(models.ProjectMember).filter(
        and_(
            models.ProjectMember.project_id == project_id,
            models.ProjectMember.user_id == member.user_id
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Member already exists")
    
    db_member = models.ProjectMember(
        project_id=project_id,
        user_id=member.user_id,
        role=member.role
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

@router.put("/projects/{project_id}/members/{member_id}", response_model=schemas.ProjectMember)
async def update_member_role(
    project_id: int,
    member_id: int,
    role_data: dict,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Update a member's role (requires leader role)"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    user = current_user or get_user_or_create_anonymous(db)
    
    # Check if user is leader or owner
    is_leader = project.owner_id == user.id
    if not is_leader:
        membership = db.query(models.ProjectMember).filter(
            and_(
                models.ProjectMember.project_id == project_id,
                models.ProjectMember.user_id == user.id,
                models.ProjectMember.role == models.ProjectRole.LEADER.value
            )
        ).first()
        if not membership:
            raise HTTPException(status_code=403, detail="Only leaders can update roles")
    
    db_member = db.query(models.ProjectMember).filter(
        and_(
            models.ProjectMember.id == member_id,
            models.ProjectMember.project_id == project_id
        )
    ).first()
    if not db_member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if "role" in role_data:
        db_member.role = role_data["role"]
    db.commit()
    db.refresh(db_member)
    return db_member

@router.delete("/projects/{project_id}/members/{member_id}")
async def remove_project_member(
    project_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Remove a member from a project (requires leader role)"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    user = current_user or get_user_or_create_anonymous(db)
    
    # Check if user is leader or owner
    is_leader = project.owner_id == user.id
    if not is_leader:
        membership = db.query(models.ProjectMember).filter(
            and_(
                models.ProjectMember.project_id == project_id,
                models.ProjectMember.user_id == user.id,
                models.ProjectMember.role == models.ProjectRole.LEADER.value
            )
        ).first()
        if not membership:
            raise HTTPException(status_code=403, detail="Only leaders can remove members")
    
    db_member = db.query(models.ProjectMember).filter(
        and_(
            models.ProjectMember.id == member_id,
            models.ProjectMember.project_id == project_id
        )
    ).first()
    if not db_member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    db.delete(db_member)
    db.commit()
    return {"message": "Member removed successfully"}

# Project Invites
@router.post("/projects/{project_id}/invites", response_model=schemas.ProjectInvite)
async def create_project_invite(
    project_id: int,
    invite: schemas.ProjectInviteCreate,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Create a project invite"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    user = current_user or get_user_or_create_anonymous(db)
    
    # Check if user is leader or owner
    is_leader = project.owner_id == user.id
    if not is_leader:
        membership = db.query(models.ProjectMember).filter(
            and_(
                models.ProjectMember.project_id == project_id,
                models.ProjectMember.user_id == user.id,
                models.ProjectMember.role == models.ProjectRole.LEADER.value
            )
        ).first()
        if not membership:
            raise HTTPException(status_code=403, detail="Only leaders can invite members")
    
    # Generate secure token
    token = secrets.token_urlsafe(32)
    
    # Find invitee by email or ID
    invitee_id = invite.invitee_id
    if invite.invitee_email and not invitee_id:
        invitee = db.query(models.User).filter(models.User.email == invite.invitee_email).first()
        if invitee:
            invitee_id = invitee.id
    
    db_invite = models.ProjectInvite(
        project_id=project_id,
        inviter_id=user.id,
        invitee_id=invitee_id,
        invitee_email=invite.invitee_email if not invitee_id else None,
        token=token,
        role=invite.role,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(db_invite)
    db.commit()
    db.refresh(db_invite)
    return db_invite

@router.get("/projects/{project_id}/invites", response_model=List[schemas.ProjectInvite])
async def get_project_invites(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Get all invites for a project"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    user = current_user or get_user_or_create_anonymous(db)
    
    # Check if user is leader or owner
    is_leader = project.owner_id == user.id
    if not is_leader:
        membership = db.query(models.ProjectMember).filter(
            and_(
                models.ProjectMember.project_id == project_id,
                models.ProjectMember.user_id == user.id,
                models.ProjectMember.role == models.ProjectRole.LEADER.value
            )
        ).first()
        if not membership:
            raise HTTPException(status_code=403, detail="Only leaders can view invites")
    
    return project.invites

@router.post("/invites/{token}/accept", response_model=schemas.ProjectMember)
async def accept_invite(
    token: str,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Accept a project invite"""
    invite = db.query(models.ProjectInvite).filter(
        and_(
            models.ProjectInvite.token == token,
            models.ProjectInvite.status == models.InviteStatus.PENDING.value
        )
    ).first()
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found or already used")
    
    if invite.expires_at and invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invite has expired")
    
    user = current_user or get_user_or_create_anonymous(db)
    
    # Check if user matches invite
    if invite.invitee_id and invite.invitee_id != user.id:
        raise HTTPException(status_code=403, detail="This invite is for a different user")
    if invite.invitee_email and user.email != invite.invitee_email:
        raise HTTPException(status_code=403, detail="This invite is for a different email")
    
    # Check if already a member
    existing = db.query(models.ProjectMember).filter(
        and_(
            models.ProjectMember.project_id == invite.project_id,
            models.ProjectMember.user_id == user.id
        )
    ).first()
    if existing:
        invite.status = models.InviteStatus.ACCEPTED.value
        db.commit()
        return existing
    
    # Add as member
    db_member = models.ProjectMember(
        project_id=invite.project_id,
        user_id=user.id,
        role=invite.role
    )
    db.add(db_member)
    invite.status = models.InviteStatus.ACCEPTED.value
    db.commit()
    db.refresh(db_member)
    return db_member

@router.delete("/invites/{invite_id}")
async def delete_invite(
    invite_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Delete a project invite"""
    invite = db.query(models.ProjectInvite).filter(models.ProjectInvite.id == invite_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    
    user = current_user or get_user_or_create_anonymous(db)
    
    # Check if user is leader or owner
    project = db.query(models.Project).filter(models.Project.id == invite.project_id).first()
    is_leader = project.owner_id == user.id
    if not is_leader:
        membership = db.query(models.ProjectMember).filter(
            and_(
                models.ProjectMember.project_id == invite.project_id,
                models.ProjectMember.user_id == user.id,
                models.ProjectMember.role == models.ProjectRole.LEADER.value
            )
        ).first()
        if not membership:
            raise HTTPException(status_code=403, detail="Only leaders can delete invites")
    
    db.delete(invite)
    db.commit()
    return {"message": "Invite deleted successfully"}

