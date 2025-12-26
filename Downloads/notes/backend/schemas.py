from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    uid: str
    email: EmailStr
    name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    class Config:
        from_attributes = True

# Note Schemas
class NoteBase(BaseModel):
    title: str
    file_url: Optional[str] = None
    summary: Optional[str] = None
    extracted_content: Optional[str] = None

class NoteCreate(NoteBase):
    pass

class Note(NoteBase):
    id: int
    created_at: datetime
    owner_id: int
    class Config:
        from_attributes = True

# Project Schemas
class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    repository_url: Optional[str] = None
    is_public: bool = False
    settings: Optional[Dict[str, Any]] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectMemberBase(BaseModel):
    user_id: int
    role: str = "viewer"

class ProjectMember(ProjectMemberBase):
    id: int
    project_id: int
    joined_at: datetime
    user: Optional[User] = None
    class Config:
        from_attributes = True

class Project(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
    owner_id: int
    members: List[ProjectMember] = []
    class Config:
        from_attributes = True

# Project Invite Schemas
class ProjectInviteCreate(BaseModel):
    invitee_email: Optional[str] = None
    invitee_id: Optional[int] = None
    role: str = "viewer"

class ProjectInvite(BaseModel):
    id: int
    project_id: int
    inviter_id: int
    invitee_id: Optional[int] = None
    invitee_email: Optional[str] = None
    token: str
    role: str
    status: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    class Config:
        from_attributes = True

# Project File Schemas
class ProjectFileBase(BaseModel):
    file_path: str
    content: str
    file_type: str

class ProjectFileCreate(ProjectFileBase):
    pass

class ProjectFile(ProjectFileBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    created_by_id: Optional[int] = None
    class Config:
        from_attributes = True

class FileVersion(BaseModel):
    id: int
    file_id: int
    content: str
    version_number: int
    created_at: datetime
    created_by_id: Optional[int] = None
    change_summary: Optional[str] = None
    class Config:
        from_attributes = True

# Project Version Schemas
class ProjectVersionCreate(BaseModel):
    version_name: str
    description: Optional[str] = None

class ProjectVersion(BaseModel):
    id: int
    project_id: int
    snapshot_data: Dict[str, Any]
    version_name: str
    description: Optional[str] = None
    created_at: datetime
    created_by_id: Optional[int] = None
    class Config:
        from_attributes = True

# Chat Message Schemas
class ChatMessageCreate(BaseModel):
    message: str

class ChatMessage(BaseModel):
    id: int
    project_id: int
    user_id: int
    message: str
    created_at: datetime
    user: Optional[User] = None
    class Config:
        from_attributes = True

# Task Schemas
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "todo"
    priority: str = "medium"
    assignee_id: Optional[int] = None
    project_id: Optional[int] = None
    due_date: Optional[datetime] = None
    labels: Optional[List[str]] = None
    story_points: Optional[int] = None

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime
    owner_id: int
    assignee: Optional[User] = None
    class Config:
        from_attributes = True

# Activity Schemas
class ProjectActivity(BaseModel):
    id: int
    project_id: int
    user_id: int
    activity_type: str
    activity_data: Dict[str, Any]
    created_at: datetime
    user: Optional[User] = None
    class Config:
        from_attributes = True

# AI Schemas
class AISummaryRequest(BaseModel):
    text: Optional[str] = None
    resource_id: Optional[int] = None
    resource_type: Optional[str] = None  # note, chat, project

class AIStudyFlowRequest(BaseModel):
    note_id: int
    format: str = "summary"  # summary, flashcards

class AIResourceFinderRequest(BaseModel):
    query: str
    project_id: Optional[int] = None

class AIMentorRequest(BaseModel):
    prompt: str
    project_id: Optional[int] = None
    context_files: Optional[List[str]] = None

# Analytics Schemas
class ProgressAnalytics(BaseModel):
    project_id: int
    total_commits: int
    total_lines_changed: int
    tasks_completed: int
    tasks_in_progress: int
    tasks_todo: int
    member_contributions: Dict[str, Any]

class WeeklyReport(BaseModel):
    project_id: int
    week_start: datetime
    week_end: datetime
    summary: str
    activities: List[Dict[str, Any]]  # Flexible format for activities
    analytics: ProgressAnalytics
