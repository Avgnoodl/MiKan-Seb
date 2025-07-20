from fastapi import *
from database import *
from model import *
import os

# Base URL for constructing links to attachments
ATTACHMENT_BASE_URL = os.getenv("ATTACHMENT_BASE_URL", "http://localhost:8000")

router = APIRouter()
db_dependency = Annotated[Session, Depends(get_db)]

@router.get("/")
def get_project_boards(db: db_dependency):
    try:
        results = (
            db.query(
                Project.id.label("project_id"),
				Project.title.label("project_title"),
				# Project.created_at.label("project_created_at"),
                
				Task.id.label("task_id"),
				Task.title.label("task_title"),
				Task.description,
				Task.status,
				Task.due_date,
				Task.priority,
                
				User.id.label("assignee_id"),
				User.name.label("assignee_name"),
				User.username.label("assignee_username"),
                
				Comment.text.label("comment_text"),
				Comment.date.label("comment_date"),

				Attachment.id.label("attachment_id"),
				Attachment.title.label("attachment_name"),
				Attachment.type.label("attachment_type"),

				AIAttachment.title.label("ai_attachment_name"),
				AIAttachment.url.label("ai_attachment_url"),
                
				Autostart.title.label("autostart_name"),
				Autostart.url.label("autostart_url")
            )
            .outerjoin(Task, Task.project_id == Project.id)
            .outerjoin(User, Task.assignee_id == User.id)
            .outerjoin(Comment, Comment.task_id == Task.id)
            .outerjoin(Attachment, Attachment.task_id == Task.id)
            .outerjoin(AIAttachment, AIAttachment.task_id == Task.id)
            .outerjoin(Autostart, Autostart.task_id == Task.id)
            .all()
        )

        rows = [dict(row._mapping) for row in results]
        projects_map = {}
        task_tracker = {}

        for row in rows:
            project_id = row["project_id"]
            task_id = row["task_id"]
            status = row["status"] or "to-do"

            stage_map = {
                "to-do": "To Do",
                "in-progress": "In Progress",
                "done": "Done"
            }
            stage_title = stage_map.get(status, "To Do")

            # Init project if new
            if project_id not in projects_map:
                projects_map[project_id] = {
                    "id": project_id,
                    "title": row["project_title"],
                    "stages": {
                        "To Do": [],
                        "In Progress": [],
                        "Done": []
                    }
                }

            if not task_id:
                continue  # skip projects without tasks

            if task_id not in task_tracker:
                task_tracker[task_id] = {
                    "id": task_id,
                    "title": row["task_title"],
                    "assignee_id": row["assignee_id"],
                    "assignee": row["assignee_name"] or "Unassigned",
                    "dueDate": row["due_date"],
                    "priority": row["priority"],
                    "description": row["description"],
                    "comments": [],
                    "attachments": [],
                    "ai_attachments": [],
                    "autostart": [],
                    "subtasks": [],
                    "status": status,
                    "reporter": row["assignee_username"] or ""
                }
                projects_map[project_id]["stages"][stage_title].append(task_tracker[task_id])

            # Append related items
            if row["comment_text"]:
                task_tracker[task_id]["comments"].append({
                    "text": row["comment_text"],
                    "date": row["comment_date"].isoformat() if row["comment_date"] else None
                })

            if row["attachment_id"]:
                task_tracker[task_id]["attachments"].append({
                    "name": row["attachment_name"],
                    "url": f"{ATTACHMENT_BASE_URL}/attachments/download_file/{row['attachment_id']}",
                    "type": "link",
                })

            if row["ai_attachment_name"]:
                task_tracker[task_id]["ai_attachments"].append({
                    "name": row["ai_attachment_name"],
                    "url": row["ai_attachment_url"]
                })

            if row["autostart_name"]:
                task_tracker[task_id]["autostart"].append({
                    "name": row["autostart_name"],
                    "url": row["autostart_url"]
                })

        # Final formatting
        boards = []
        for project in projects_map.values():
            stages = []
            for idx, (title, tasks) in enumerate(project["stages"].items(), start=101):
                stages.append({"id": idx, "title": title, "tasks": tasks})
            boards.append({
                "id": project["id"],
                "title": project["title"],
                "stages": stages
            })

        return boards

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))