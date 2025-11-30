import json
import logging
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    TASK_DELETED = "task.deleted"

class TaskEvent:
    def __init__(self, event_type: EventType, task_id: str, description: str, 
                 is_completed: bool = False, timestamp: str = None):
        self.event_type = event_type
        self.task_id = task_id
        self.description = description
        self.is_completed = is_completed
        self.timestamp = timestamp or datetime.utcnow().isoformat()
    
    def to_json(self) -> str:
        return json.dumps({
            "event_type": self.event_type,
            "task_id": self.task_id,
            "description": self.description,
            "is_completed": self.is_completed,
            "timestamp": self.timestamp
        })
    
    @staticmethod
    def from_json(data: str) -> 'TaskEvent':
        obj = json.loads(data)
        return TaskEvent(
            event_type=obj["event_type"],
            task_id=obj["task_id"],
            description=obj["description"],
            is_completed=obj["is_completed"],
            timestamp=obj["timestamp"]
        )

class Notification:
    def __init__(self, notification_id: str, event_type: EventType, title: str, 
                 message: str, task_id: str, read: bool = False, 
                 created_at: str = None):
        self.notification_id = notification_id
        self.event_type = event_type
        self.title = title
        self.message = message
        self.task_id = task_id
        self.read = read
        self.created_at = created_at or datetime.utcnow().isoformat()
    
    def to_dict(self):
        return {
            "_id": self.notification_id,
            "event_type": self.event_type,
            "title": self.title,
            "message": self.message,
            "task_id": self.task_id,
            "read": self.read,
            "created_at": self.created_at
        }

class NotificationTemplate:
    TEMPLATES = {
        EventType.TASK_CREATED: {
            "title": "✨ New Task Created",
            "message": "Task '{description}' has been created"
        },
        EventType.TASK_UPDATED: {
            "title": "✏️ Task Updated",
            "message": "Task '{description}' has been updated"
        },
        EventType.TASK_COMPLETED: {
            "title": "✅ Task Completed",
            "message": "Congratulations! Task '{description}' is complete"
        },
        EventType.TASK_DELETED: {
            "title": "🗑️ Task Deleted",
            "message": "Task '{description}' has been deleted"
        }
    }
    
    @staticmethod
    def generate(event: TaskEvent) -> dict:
        template = NotificationTemplate.TEMPLATES.get(
            event.event_type,
            {"title": "Task Event", "message": "Event for task '{description}'"}
        )
        return {
            "title": template["title"],
            "message": template["message"].format(description=event.description)
        }
