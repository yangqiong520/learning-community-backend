from app.models.conversation_participant import ConversationParticipant

def mask_phone_number(phone):
    if not phone or len(phone) < 7:
        return phone
    return phone[:3] + '****' + phone[-4:]


def get_user_display_name(user_id, current_user_id, user_remarks, users_dict):
    remark = user_remarks.get(f'{current_user_id}_{user_id}')
    if remark:
        return remark
    user = users_dict.get(user_id)
    return user.username if user else None


def get_conversation_display_name(conversation, current_user_id, user_remarks, users_dict):
    if conversation.type == 'group':
        return conversation.name or '群聊'
    
    participant = conversation.participants.filter(
        ConversationParticipant.user_id != current_user_id,
        ConversationParticipant.left_at.is_(None)
    ).first()
    
    if not participant:
        return '未知用户'
    
    display_name = participant.nickname
    if not display_name:
        display_name = get_user_display_name(
            participant.user_id, 
            current_user_id, 
            user_remarks, 
            users_dict
        )
    
    return display_name or '未知用户'


def update_unread_count(conversation_id, current_user_id, db):
    from app.models.message import Message
    from app.models.conversation_participant import ConversationParticipant
    
    participant = ConversationParticipant.query.filter_by(
        conversation_id=conversation_id,
        user_id=current_user_id
    ).first()
    
    if participant:
        last_message = Message.query.filter_by(
            conversation_id=conversation_id
        ).order_by(Message.created_at.desc()).first()
        
        if last_message:
            new_unread = Message.query.filter(
                Message.conversation_id == conversation_id,
                Message.sender_id != current_user_id,
                Message.is_deleted == False,
                Message.id > (participant.last_read_message_id or 0)
            ).count()
            
            participant.unread_count = new_unread
            db.session.commit()
