import logging
from typing import List, Optional
from datetime import datetime
import uuid
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config import settings
from models import Notification, EventType

logger = logging.getLogger(__name__)

class MongoDBClient:
    _client = None
    _db = None
    
    @classmethod
    def connect(cls):
        """Connect to MongoDB"""
        try:
            cls._client = MongoClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            # Verify connection
            cls._client.admin.command('ping')
            cls._db = cls._client[settings.mongodb_db]
            logger.info(f"✓ Connected to MongoDB: {settings.mongodb_uri}")
            return cls._db
        except ConnectionFailure as e:
            logger.error(f"✗ Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    def disconnect(cls):
        """Disconnect from MongoDB"""
        if cls._client:
            cls._client.close()
            logger.info("✓ Disconnected from MongoDB")
    
    @classmethod
    def get_db(cls):
        """Get MongoDB database"""
        if cls._db is None:
            cls.connect()
        return cls._db

class NotificationRepository:
    """MongoDB operations for notifications"""
    
    COLLECTION_NAME = "notifications"
    
    @classmethod
    def _get_collection(cls):
        db = MongoDBClient.get_db()
        collection = db[cls.COLLECTION_NAME]
        # Create indexes
        collection.create_index("task_id")
        collection.create_index("created_at")
        collection.create_index([("created_at", -1)])
        return collection
    
    @classmethod
    def save_notification(cls, notification: Notification) -> str:
        """Save notification to database"""
        try:
            collection = cls._get_collection()
            result = collection.insert_one(notification.to_dict())
            logger.info(f"✓ Saved notification: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"✗ Failed to save notification: {e}")
            raise
    
    @classmethod
    def get_notifications(cls, limit: int = 50, skip: int = 0) -> List[dict]:
        """Get all notifications with pagination"""
        try:
            collection = cls._get_collection()
            notifications = list(collection
                .find()
                .sort("created_at", -1)
                .skip(skip)
                .limit(limit))
            
            # Convert ObjectId to string for JSON serialization
            for notif in notifications:
                if "_id" in notif:
                    notif["_id"] = str(notif["_id"])
            
            return notifications
        except Exception as e:
            logger.error(f"✗ Failed to get notifications: {e}")
            return []
    
    @classmethod
    def get_notifications_by_task(cls, task_id: str) -> List[dict]:
        """Get notifications for specific task"""
        try:
            collection = cls._get_collection()
            notifications = list(collection
                .find({"task_id": task_id})
                .sort("created_at", -1))
            
            for notif in notifications:
                if "_id" in notif:
                    notif["_id"] = str(notif["_id"])
            
            return notifications
        except Exception as e:
            logger.error(f"✗ Failed to get task notifications: {e}")
            return []
    
    @classmethod
    def mark_as_read(cls, notification_id: str) -> bool:
        """Mark notification as read"""
        try:
            collection = cls._get_collection()
            result = collection.update_one(
                {"_id": notification_id},
                {"$set": {"read": True}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"✗ Failed to mark notification as read: {e}")
            return False
    
    @classmethod
    def mark_all_as_read(cls) -> int:
        """Mark all notifications as read"""
        try:
            collection = cls._get_collection()
            result = collection.update_many(
                {"read": False},
                {"$set": {"read": True}}
            )
            return result.modified_count
        except Exception as e:
            logger.error(f"✗ Failed to mark all as read: {e}")
            return 0
    
    @classmethod
    def delete_notification(cls, notification_id: str) -> bool:
        """Delete notification"""
        try:
            collection = cls._get_collection()
            result = collection.delete_one({"_id": notification_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"✗ Failed to delete notification: {e}")
            return False
    
    @classmethod
    def get_unread_count(cls) -> int:
        """Get count of unread notifications"""
        try:
            collection = cls._get_collection()
            return collection.count_documents({"read": False})
        except Exception as e:
            logger.error(f"✗ Failed to get unread count: {e}")
            return 0
    
    @classmethod
    def clear_old_notifications(cls, days: int = 30) -> int:
        """Delete notifications older than specified days"""
        try:
            collection = cls._get_collection()
            cutoff_date = datetime.utcnow().replace(
                day=datetime.utcnow().day - days
            ).isoformat()
            
            result = collection.delete_many(
                {"created_at": {"$lt": cutoff_date}}
            )
            return result.deleted_count
        except Exception as e:
            logger.error(f"✗ Failed to clear old notifications: {e}")
            return 0
