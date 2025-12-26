from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import enum

# Enums for roles and statuses
class ProjectRole(str, enum.Enum):
    LEADER = "leader"
    DEVELOPER = "developer"
    DESIGNER = "designer"
    DOC_MANAGER = "doc_manager"
    VIEWER = "viewer"

class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class InviteStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, unique=True, index=True)  # Firebase UID
    email = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    notes = relationship("Note", back_populates="owner")
    projects = relationship("Project", back_populates="owner", foreign_keys="Project.owner_id")
    # Specify foreign_keys to resolve ambiguity (Task has both owner_id and assignee_id)
    # Using string-based foreign_keys since Task is defined later in the file
    tasks = relationship("Task", back_populates="owner", foreign_keys="Task.owner_id")
    assigned_tasks = relationship("Task", foreign_keys="Task.assignee_id")  # Tasks assigned to this user
    project_memberships = relationship("ProjectMember", back_populates="user")
    sent_invites = relationship("ProjectInvite", back_populates="inviter", foreign_keys="ProjectInvite.inviter_id")
    received_invites = relationship("ProjectInvite", back_populates="invitee", foreign_keys="ProjectInvite.invitee_id")

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    file_url = Column(String)
    summary = Column(Text)  # AI-generated summary
    extracted_content = Column(Text)  # Extracted text from files
    created_at = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="notes")

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    repository_url = Column(String, nullable=True)
    is_public = Column(Boolean, default=False)
    settings = Column(JSON, nullable=True)  # Store project settings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="projects", foreign_keys=[owner_id])
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    invites = relationship("ProjectInvite", back_populates="project", cascade="all, delete-orphan")
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    versions = relationship("ProjectVersion", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="project", cascade="all, delete-orphan")

class ProjectMember(Base):
    __tablename__ = "project_members"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    role = Column(String, default=ProjectRole.VIEWER.value)
    joined_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")

class ProjectInvite(Base):
    __tablename__ = "project_invites"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    inviter_id = Column(Integer, ForeignKey("users.id"))
    invitee_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null if email invite
    invitee_email = Column(String, nullable=True)  # Email if user doesn't exist yet
    token = Column(String, unique=True, index=True)  # Secure invite token
    role = Column(String, default=ProjectRole.VIEWER.value)
    status = Column(String, default=InviteStatus.PENDING.value)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="invites")
    inviter = relationship("User", back_populates="sent_invites", foreign_keys=[inviter_id])
    invitee = relationship("User", back_populates="received_invites", foreign_keys=[invitee_id])

class ProjectFile(Base):
    __tablename__ = "project_files"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    file_path = Column(String, index=True)  # Relative path in project
    content = Column(Text)  # File content
    file_type = Column(String)  # File extension/type
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    project = relationship("Project", back_populates="files")
    versions = relationship("FileVersion", back_populates="file", cascade="all, delete-orphan")

class FileVersion(Base):
    __tablename__ = "file_versions"
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("project_files.id"), index=True)
    content = Column(Text)
    version_number = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    change_summary = Column(Text, nullable=True)
    file = relationship("ProjectFile", back_populates="versions")

class ProjectVersion(Base):
    __tablename__ = "project_versions"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    snapshot_data = Column(JSON)  # Store project state snapshot
    version_name = Column(String)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    project = relationship("Project", back_populates="versions")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project", back_populates="chat_messages")
    user = relationship("User")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    status = Column(String, default=TaskStatus.TODO.value)
    priority = Column(String, default="medium")  # low, medium, high
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    due_date = Column(DateTime, nullable=True)
    labels = Column(JSON, nullable=True)  # Array of labels
    story_points = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))
    # Specify foreign_keys to resolve ambiguity (Task has both owner_id and assignee_id)
    owner = relationship("User", back_populates="tasks", foreign_keys=[owner_id])
    assignee = relationship("User", foreign_keys=[assignee_id])
    project = relationship("Project", back_populates="tasks")

class ProjectActivity(Base):
    __tablename__ = "project_activities"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    activity_type = Column(String)  # commit, file_edit, task_update, etc.
    activity_data = Column(JSON)  # Store activity details
    created_at = Column(DateTime, default=datetime.utcnow)
    project = relationship("Project")
    user = relationship("User")
