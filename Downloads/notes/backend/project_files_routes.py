import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import Optional, List
from database import SessionLocal
import models
import schemas
from routes import get_current_user, get_user_or_create_anonymous

router = APIRouter(prefix="/projects", tags=["Project Files"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_project_access(project_id: int, user: models.User, db: Session, require_edit: bool = False):
    """Check if user has access to project"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Owner has full access
    if project.owner_id == user.id:
        return project, True
    
    # Check if user is a member
    membership = db.query(models.ProjectMember).filter(
        and_(
            models.ProjectMember.project_id == project_id,
            models.ProjectMember.user_id == user.id
        )
    ).first()
    
    if not membership and not project.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if require_edit:
        # Only leader, developer, designer can edit
        if membership.role not in [models.ProjectRole.LEADER.value, models.ProjectRole.DEVELOPER.value, models.ProjectRole.DESIGNER.value]:
            raise HTTPException(status_code=403, detail="Edit access denied")
    
    return project, membership is not None

# Project Files Management
@router.get("/{project_id}/files", response_model=List[schemas.ProjectFile])
async def get_project_files(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Get all files in a project"""
    user = current_user or get_user_or_create_anonymous(db)
    project, _ = check_project_access(project_id, user, db)
    return project.files

@router.post("/{project_id}/files", response_model=schemas.ProjectFile)
async def create_project_file(
    project_id: int,
    file: schemas.ProjectFileCreate,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Create a new file in a project"""
    user = current_user or get_user_or_create_anonymous(db)
    project, _ = check_project_access(project_id, user, db, require_edit=True)
    
    # Check if file already exists
    existing = db.query(models.ProjectFile).filter(
        and_(
            models.ProjectFile.project_id == project_id,
            models.ProjectFile.file_path == file.file_path
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="File already exists")
    
    db_file = models.ProjectFile(
        project_id=project_id,
        file_path=file.file_path,
        content=file.content,
        file_type=file.file_type,
        created_by_id=user.id
    )
    db.add(db_file)
    
    # Create initial version
    db_version = models.FileVersion(
        file_id=db_file.id,
        content=file.content,
        version_number=1,
        created_by_id=user.id,
        change_summary="Initial version"
    )
    db.add(db_version)
    
    # Log activity
    activity = models.ProjectActivity(
        project_id=project_id,
        user_id=user.id,
        activity_type="file_create",
        activity_data={"file_path": file.file_path, "file_type": file.file_type}
    )
    db.add(activity)
    
    db.commit()
    db.refresh(db_file)
    return db_file

@router.get("/{project_id}/files/{file_id}", response_model=schemas.ProjectFile)
async def get_project_file(
    project_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Get a specific file"""
    user = current_user or get_user_or_create_anonymous(db)
    project, _ = check_project_access(project_id, user, db)
    
    db_file = db.query(models.ProjectFile).filter(
        and_(
            models.ProjectFile.id == file_id,
            models.ProjectFile.project_id == project_id
        )
    ).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    return db_file

@router.put("/{project_id}/files/{file_id}", response_model=schemas.ProjectFile)
async def update_project_file(
    project_id: int,
    file_id: int,
    file_update: schemas.ProjectFileCreate,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Update a file in a project"""
    user = current_user or get_user_or_create_anonymous(db)
    project, _ = check_project_access(project_id, user, db, require_edit=True)
    
    db_file = db.query(models.ProjectFile).filter(
        and_(
            models.ProjectFile.id == file_id,
            models.ProjectFile.project_id == project_id
        )
    ).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Create new version before updating
    latest_version = db.query(models.FileVersion).filter(
        models.FileVersion.file_id == file_id
    ).order_by(desc(models.FileVersion.version_number)).first()
    
    version_number = (latest_version.version_number + 1) if latest_version else 1
    
    db_version = models.FileVersion(
        file_id=file_id,
        content=db_file.content,  # Save old content
        version_number=version_number,
        created_by_id=user.id,
        change_summary=f"Updated by {user.email}"
    )
    db.add(db_version)
    
    # Update file
    db_file.content = file_update.content
    db_file.file_path = file_update.file_path
    db_file.file_type = file_update.file_type
    db_file.updated_at = datetime.utcnow()
    
    # Log activity
    activity = models.ProjectActivity(
        project_id=project_id,
        user_id=user.id,
        activity_type="file_edit",
        activity_data={"file_path": file_update.file_path, "file_id": file_id}
    )
    db.add(activity)
    
    db.commit()
    db.refresh(db_file)
    return db_file

@router.delete("/{project_id}/files/{file_id}")
async def delete_project_file(
    project_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Delete a file from a project"""
    user = current_user or get_user_or_create_anonymous(db)
    project, _ = check_project_access(project_id, user, db, require_edit=True)
    
    db_file = db.query(models.ProjectFile).filter(
        and_(
            models.ProjectFile.id == file_id,
            models.ProjectFile.project_id == project_id
        )
    ).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Log activity
    activity = models.ProjectActivity(
        project_id=project_id,
        user_id=user.id,
        activity_type="file_delete",
        activity_data={"file_path": db_file.file_path, "file_id": file_id}
    )
    db.add(activity)
    
    db.delete(db_file)
    db.commit()
    return {"message": "File deleted successfully"}

# File Versions
@router.get("/{project_id}/files/{file_id}/versions", response_model=List[schemas.FileVersion])
async def get_file_versions(
    project_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Get all versions of a file"""
    user = current_user or get_user_or_create_anonymous(db)
    project, _ = check_project_access(project_id, user, db)
    
    db_file = db.query(models.ProjectFile).filter(
        and_(
            models.ProjectFile.id == file_id,
            models.ProjectFile.project_id == project_id
        )
    ).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    versions = db.query(models.FileVersion).filter(
        models.FileVersion.file_id == file_id
    ).order_by(desc(models.FileVersion.version_number)).all()
    
    return versions

@router.post("/{project_id}/files/{file_id}/versions/{version_id}/restore", response_model=schemas.ProjectFile)
async def restore_file_version(
    project_id: int,
    file_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Restore a file to a specific version"""
    user = current_user or get_user_or_create_anonymous(db)
    project, _ = check_project_access(project_id, user, db, require_edit=True)
    
    db_file = db.query(models.ProjectFile).filter(
        and_(
            models.ProjectFile.id == file_id,
            models.ProjectFile.project_id == project_id
        )
    ).first()
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    db_version = db.query(models.FileVersion).filter(
        and_(
            models.FileVersion.id == version_id,
            models.FileVersion.file_id == file_id
        )
    ).first()
    if not db_version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Create new version with restored content
    latest_version = db.query(models.FileVersion).filter(
        models.FileVersion.file_id == file_id
    ).order_by(desc(models.FileVersion.version_number)).first()
    
    version_number = (latest_version.version_number + 1) if latest_version else 1
    
    db_new_version = models.FileVersion(
        file_id=file_id,
        content=db_file.content,
        version_number=version_number,
        created_by_id=user.id,
        change_summary=f"Restored from version {db_version.version_number}"
    )
    db.add(db_new_version)
    
    # Restore content
    db_file.content = db_version.content
    db_file.updated_at = datetime.utcnow()
    
    # Log activity
    activity = models.ProjectActivity(
        project_id=project_id,
        user_id=user.id,
        activity_type="file_restore",
        activity_data={"file_path": db_file.file_path, "version_id": version_id}
    )
    db.add(activity)
    
    db.commit()
    db.refresh(db_file)
    return db_file

# Project Versions (Snapshots)
@router.post("/{project_id}/versions", response_model=schemas.ProjectVersion)
async def create_project_version(
    project_id: int,
    version: schemas.ProjectVersionCreate,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Create a project snapshot/version"""
    user = current_user or get_user_or_create_anonymous(db)
    project, _ = check_project_access(project_id, user, db, require_edit=True)
    
    # Create snapshot of all files
    snapshot_data = {
        "files": [
            {
                "file_path": f.file_path,
                "content": f.content,
                "file_type": f.file_type
            }
            for f in project.files
        ],
        "settings": project.settings,
        "created_at": datetime.utcnow().isoformat()
    }
    
    db_version = models.ProjectVersion(
        project_id=project_id,
        snapshot_data=snapshot_data,
        version_name=version.version_name,
        description=version.description,
        created_by_id=user.id
    )
    db.add(db_version)
    
    # Log activity
    activity = models.ProjectActivity(
        project_id=project_id,
        user_id=user.id,
        activity_type="version_create",
        activity_data={"version_name": version.version_name}
    )
    db.add(activity)
    
    db.commit()
    db.refresh(db_version)
    return db_version

@router.get("/{project_id}/versions", response_model=List[schemas.ProjectVersion])
async def get_project_versions(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Get all versions of a project"""
    user = current_user or get_user_or_create_anonymous(db)
    project, _ = check_project_access(project_id, user, db)
    
    versions = db.query(models.ProjectVersion).filter(
        models.ProjectVersion.project_id == project_id
    ).order_by(desc(models.ProjectVersion.created_at)).all()
    
    return versions

@router.post("/{project_id}/versions/{version_id}/restore")
async def restore_project_version(
    project_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Restore a project to a specific version"""
    user = current_user or get_user_or_create_anonymous(db)
    project, _ = check_project_access(project_id, user, db, require_edit=True)
    
    db_version = db.query(models.ProjectVersion).filter(
        and_(
            models.ProjectVersion.id == version_id,
            models.ProjectVersion.project_id == project_id
        )
    ).first()
    if not db_version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Restore files from snapshot
    snapshot_files = db_version.snapshot_data.get("files", [])
    
    # Delete existing files
    for file in project.files:
        db.delete(file)
    
    # Restore files
    for file_data in snapshot_files:
        db_file = models.ProjectFile(
            project_id=project_id,
            file_path=file_data["file_path"],
            content=file_data["content"],
            file_type=file_data["file_type"],
            created_by_id=user.id
        )
        db.add(db_file)
    
    # Restore settings if any
    if "settings" in db_version.snapshot_data:
        project.settings = db_version.snapshot_data["settings"]
    
    # Log activity
    activity = models.ProjectActivity(
        project_id=project_id,
        user_id=user.id,
        activity_type="version_restore",
        activity_data={"version_name": db_version.version_name, "version_id": version_id}
    )
    db.add(activity)
    
    db.commit()
    return {"message": "Project restored successfully"}

