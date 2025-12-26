import os
import requests
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional, Dict, Any, List
from database import SessionLocal
import models
import schemas
from routes import get_current_user, get_user_or_create_anonymous

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

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

router = APIRouter(prefix="/analytics", tags=["Analytics"])

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

# Progress Analytics
@router.get("/projects/{project_id}/progress", response_model=schemas.ProgressAnalytics)
async def get_progress_analytics(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Get progress analytics for a project"""
    user = current_user or get_user_or_create_anonymous(db)
    project = check_project_access(project_id, user, db)
    
    # Get tasks
    tasks = db.query(models.Task).filter(models.Task.project_id == project_id).all()
    tasks_todo = len([t for t in tasks if t.status == models.TaskStatus.TODO.value])
    tasks_in_progress = len([t for t in tasks if t.status == models.TaskStatus.IN_PROGRESS.value])
    tasks_completed = len([t for t in tasks if t.status == models.TaskStatus.DONE.value])
    
    # Get activities (simulate commits and lines changed)
    activities = db.query(models.ProjectActivity).filter(
        models.ProjectActivity.project_id == project_id
    ).all()
    
    commits = [a for a in activities if a.activity_type in ["file_create", "file_edit", "version_create"]]
    total_commits = len(commits)
    
    # Estimate lines changed from file edits
    file_edits = [a for a in activities if a.activity_type == "file_edit"]
    total_lines_changed = sum([
        len(a.activity_data.get("content", "").split("\n")) if "content" in a.activity_data else 0
        for a in file_edits
    ])
    
    # Get member contributions
    member_contributions = {}
    for member in project.members:
        member_activities = db.query(models.ProjectActivity).filter(
            and_(
                models.ProjectActivity.project_id == project_id,
                models.ProjectActivity.user_id == member.user_id
            )
        ).all()
        member_contributions[member.user.email if member.user else "Unknown"] = {
            "commits": len([a for a in member_activities if a.activity_type in ["file_create", "file_edit"]]),
            "tasks_completed": len([t for t in tasks if t.assignee_id == member.user_id and t.status == models.TaskStatus.DONE.value]),
            "messages": len([a for a in member_activities if a.activity_type == "chat_message"])
        }
    
    # Owner contributions
    owner_activities = db.query(models.ProjectActivity).filter(
        and_(
            models.ProjectActivity.project_id == project_id,
            models.ProjectActivity.user_id == project.owner_id
        )
    ).all()
    owner_email = project.owner.email if project.owner else "Unknown"
    member_contributions[owner_email] = {
        "commits": len([a for a in owner_activities if a.activity_type in ["file_create", "file_edit"]]),
        "tasks_completed": len([t for t in tasks if t.owner_id == project.owner_id and t.status == models.TaskStatus.DONE.value]),
        "messages": len([a for a in owner_activities if a.activity_type == "chat_message"])
    }
    
    return schemas.ProgressAnalytics(
        project_id=project_id,
        total_commits=total_commits,
        total_lines_changed=total_lines_changed,
        tasks_completed=tasks_completed,
        tasks_in_progress=tasks_in_progress,
        tasks_todo=tasks_todo,
        member_contributions=member_contributions
    )

# Weekly Progress Report
@router.get("/projects/{project_id}/weekly-report", response_model=schemas.WeeklyReport)
async def get_weekly_report(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Generate AI-powered weekly progress report"""
    user = current_user or get_user_or_create_anonymous(db)
    project = check_project_access(project_id, user, db)
    
    # Get week range (last 7 days)
    week_end = datetime.utcnow()
    week_start = week_end - timedelta(days=7)
    
    # Get activities from this week
    activities = db.query(models.ProjectActivity).filter(
        and_(
            models.ProjectActivity.project_id == project_id,
            models.ProjectActivity.created_at >= week_start,
            models.ProjectActivity.created_at <= week_end
        )
    ).order_by(models.ProjectActivity.created_at).all()
    
    # Get analytics
    analytics = await get_progress_analytics(project_id, db, current_user)
    
    # Get tasks
    tasks = db.query(models.Task).filter(models.Task.project_id == project_id).all()
    
    # Prepare data for AI summary
    activities_summary = []
    for activity in activities:
        activities_summary.append({
            "type": activity.activity_type,
            "user": activity.user.email if activity.user else "Unknown",
            "timestamp": activity.created_at.isoformat(),
            "data": activity.activity_data
        })
    
    # Generate AI summary
    prompt = f"""Generate a weekly progress report for the project "{project.title}".

Project Description: {project.description}

Activities this week:
{str(activities_summary)[:3000]}

Tasks Status:
- Completed: {analytics.tasks_completed}
- In Progress: {analytics.tasks_in_progress}
- To Do: {analytics.tasks_todo}

Team Contributions:
{str(analytics.member_contributions)[:1000]}

Provide a comprehensive weekly report covering:
1. Key accomplishments
2. Progress made
3. Challenges faced
4. Next steps and recommendations

Weekly Report:"""
    
    try:
        summary = await call_gemini_api(prompt, max_tokens=2000)
    except Exception as e:
        summary = f"Error generating AI report: {str(e)}"
    
    # Convert activities to schema format
    activities_list = []
    for a in activities:
        activities_list.append({
            "id": a.id,
            "project_id": a.project_id,
            "user_id": a.user_id,
            "activity_type": a.activity_type,
            "activity_data": a.activity_data,
            "created_at": a.created_at.isoformat(),
            "user": {"id": a.user.id, "email": a.user.email} if a.user else None
        })
    
    return schemas.WeeklyReport(
        project_id=project_id,
        week_start=week_start,
        week_end=week_end,
        summary=summary,
        activities=activities_list,
        analytics=analytics
    )

# Project Activity Timeline
@router.get("/projects/{project_id}/timeline")
async def get_project_timeline(
    project_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)
):
    """Get project activity timeline"""
    user = current_user or get_user_or_create_anonymous(db)
    project = check_project_access(project_id, user, db)
    
    activities = db.query(models.ProjectActivity).filter(
        models.ProjectActivity.project_id == project_id
    ).order_by(models.ProjectActivity.created_at.desc()).limit(limit).all()
    
    timeline = []
    for activity in activities:
        timeline.append({
            "id": activity.id,
            "type": activity.activity_type,
            "user": activity.user.email if activity.user else "Unknown",
            "timestamp": activity.created_at.isoformat(),
            "data": activity.activity_data
        })
    
    return {"timeline": timeline}

