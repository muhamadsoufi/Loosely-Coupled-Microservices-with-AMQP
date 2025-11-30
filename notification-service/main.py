import asyncio
import logging
import uuid
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
from datetime import datetime

from config import settings
from models import TaskEvent, EventType, Notification, NotificationTemplate
from rabbitmq_client import RabbitMQConnection, RabbitMQProducer, RabbitMQConsumer
from db import MongoDBClient, NotificationRepository

# Setup logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models
class NotificationResponse(BaseModel):
    id: Optional[str] = None
    _id: Optional[str] = None
    event_type: str
    title: str
    message: str
    task_id: str
    read: bool
    created_at: str
    
    class Config:
        populate_by_name = True  # Allow both 'id' and '_id'

class NotificationStats(BaseModel):
    total: int
    unread: int
    by_type: dict

# Background task for consuming messages
async_task = None

async def process_event(event: TaskEvent):
    """Process incoming task event"""
    try:
        # Generate notification from event
        template = NotificationTemplate.generate(event)
        
        # Create notification
        notification = Notification(
            notification_id=str(uuid.uuid4()),
            event_type=event.event_type,
            title=template["title"],
            message=template["message"],
            task_id=event.task_id
        )
        
        # Save to database
        NotificationRepository.save_notification(notification)
        logger.info(f"📬 Notification created for event: {event.event_type}")
        
    except Exception as e:
        logger.error(f"✗ Error processing event: {e}")

async def start_consumer():
    """Start message consumer"""
    try:
        await RabbitMQConsumer.start_consuming(process_event)
    except Exception as e:
        logger.error(f"✗ Consumer error: {e}")
        # Retry after 5 seconds
        await asyncio.sleep(5)
        await start_consumer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("🚀 Starting Notification Service...")
    
    try:
        # Connect to RabbitMQ
        await RabbitMQConnection.connect()
        await RabbitMQProducer.initialize()
        
        # Connect to MongoDB
        MongoDBClient.connect()
        
        # Start consumer in background
        global async_task
        async_task = asyncio.create_task(start_consumer())
        
        logger.info("✓ Notification Service started successfully")
    except Exception as e:
        logger.error(f"✗ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Notification Service...")
    
    if async_task:
        async_task.cancel()
        try:
            await async_task
        except asyncio.CancelledError:
            pass
    
    await RabbitMQConnection.disconnect()
    MongoDBClient.disconnect()
    logger.info("✓ Notification Service shut down")

# Create FastAPI app
app = FastAPI(
    title="Notification Service",
    description="Async notification service using RabbitMQ",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files if static directory exists
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Routes

@app.get("/", tags=["UI"])
async def root():
    """Serve the notification dashboard UI"""
    index_file = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Notification Service", "docs": "/docs"}

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "notification-service",
        "version": "1.0.0"
    }

@app.get("/readiness", tags=["Health"])
async def readiness_check():
    """Readiness check endpoint"""
    try:
        # Check RabbitMQ
        channel = await RabbitMQConnection.get_channel()
        # Check MongoDB
        MongoDBClient.get_db()
        
        return {
            "status": "ready",
            "services": {
                "rabbitmq": "connected",
                "mongodb": "connected"
            }
        }
    except Exception as e:
        logger.error(f"✗ Readiness check failed: {e}")
        return {"status": "not_ready", "error": str(e)}, 503

@app.get("/notifications", response_model=List[NotificationResponse], tags=["Notifications"])
async def get_notifications(
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0)
):
    """Get all notifications with pagination"""
    try:
        notifications = NotificationRepository.get_notifications(limit, skip)
        for notif in notifications:
            if "_id" in notif and "id" not in notif:
                notif["id"] = notif["_id"]
        return [NotificationResponse(**n) for n in notifications]
    except Exception as e:
        logger.error(f"✗ Error getting notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/notifications/task/{task_id}", response_model=List[NotificationResponse], tags=["Notifications"])
async def get_task_notifications(task_id: str):
    """Get notifications for specific task"""
    try:
        notifications = NotificationRepository.get_notifications_by_task(task_id)
        for notif in notifications:
            if "_id" in notif and "id" not in notif:
                notif["id"] = notif["_id"]
        return [NotificationResponse(**n) for n in notifications]
    except Exception as e:
        logger.error(f"✗ Error getting task notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/notifications/{notification_id}/read", tags=["Notifications"])
async def mark_notification_read(notification_id: str):
    """Mark notification as read"""
    try:
        success = NotificationRepository.mark_as_read(notification_id)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        return {"status": "marked_as_read", "notification_id": notification_id}
    except Exception as e:
        logger.error(f"✗ Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/notifications/read-all", tags=["Notifications"])
async def mark_all_notifications_read():
    """Mark all notifications as read"""
    try:
        count = NotificationRepository.mark_all_as_read()
        return {
            "status": "all_marked_as_read",
            "count": count
        }
    except Exception as e:
        logger.error(f"✗ Error marking all as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/notifications/{notification_id}", tags=["Notifications"])
async def delete_notification(notification_id: str):
    """Delete notification"""
    try:
        success = NotificationRepository.delete_notification(notification_id)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        return {"status": "deleted", "notification_id": notification_id}
    except Exception as e:
        logger.error(f"✗ Error deleting notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", response_model=NotificationStats, tags=["Stats"])
async def get_notification_stats():
    """Get notification statistics"""
    try:
        notifications = NotificationRepository.get_notifications(limit=1000)
        unread = NotificationRepository.get_unread_count()
        
        by_type = {}
        for n in notifications:
            event_type = n["event_type"]
            by_type[event_type] = by_type.get(event_type, 0) + 1
        
        return NotificationStats(
            total=len(notifications),
            unread=unread,
            by_type=by_type
        )
    except Exception as e:
        logger.error(f"✗ Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.service_host,
        port=settings.service_port,
        log_level=settings.log_level.lower()
    )
