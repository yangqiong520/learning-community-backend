from libs.db import db
from app.models.notification import Notification

def create_message_notification(user_id, conversation_id, message_id, sender_name, content_preview):
    title = f'来自 {sender_name} 的新消息'
    content = content_preview[:100] if content_preview else '发了一条消息'
    
    notification = Notification(
        user_id=user_id,
        type='message',
        title=title,
        content=content,
        conversation_id=conversation_id,
        related_id=message_id,
        is_read=False
    )
    
    db.session.add(notification)
    db.session.commit()
    return notification


def create_system_notification(user_id, title, content):
    notification = Notification(
        user_id=user_id,
        type='system',
        title=title,
        content=content,
        is_read=False
    )
    
    db.session.add(notification)
    db.session.commit()
    return notification


def mark_notification_as_read(notification_id, user_id):
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if notification:
        notification.is_read = True
        db.session.commit()
    return notification


def mark_all_notifications_as_read(user_id):
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
