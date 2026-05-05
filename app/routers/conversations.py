from flask import Blueprint, request
from libs.db import db
from libs.jwt_auth import token_required
from libs.response import success_response, created_response, bad_request_response, not_found_response, forbidden_response
from app.models.conversation import Conversation
from app.models.conversation_participant import ConversationParticipant
from app.models.message import Message
from app.models.user_remark import UserRemark
from app.models.notification import Notification
from app.models.user import User
from app.utils.conversation_utils import mask_phone_number, get_user_display_name, get_conversation_display_name, update_unread_count
from app.services.notification_service import create_message_notification

conversations_bp = Blueprint('conversations', __name__, url_prefix='/api/v2/conversations')


def check_conversation_permission(conversation_id, user_id):
    participant = ConversationParticipant.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id
    ).first()
    return participant is not None and participant.left_at is None


def get_participant_role(conversation_id, user_id):
    participant = ConversationParticipant.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id,
        left_at=None
    ).first()
    return participant.role if participant else None


@conversations_bp.route('', methods=['GET'])
@token_required
def get_conversations():
    user_id = request.current_user_id
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    conv_type = request.args.get('type')
    
    query = db.session.query(Conversation, ConversationParticipant).join(
        ConversationParticipant,
        Conversation.id == ConversationParticipant.conversation_id
    ).filter(
        ConversationParticipant.user_id == user_id,
        ConversationParticipant.left_at.is_(None),
        Conversation.deleted_at.is_(None)
    )
    
    if conv_type:
        query = query.filter(Conversation.type == conv_type)
    
    conversations = query.order_by(Conversation.updated_at.desc()).all()
    
    user_remarks = {f'{ur.user_id}_{ur.target_user_id}': ur.remark for ur in UserRemark.query.filter_by(user_id=user_id).all()}
    users_dict = {u.id: u for u in User.query.all()}
    
    result = []
    for conv, participant in conversations:
        display_name = get_conversation_display_name(conv, user_id, user_remarks, users_dict)
        
        last_message = Message.query.filter_by(
            conversation_id=conv.id,
            is_deleted=False
        ).order_by(Message.created_at.desc()).first()
        
        conv_data = {
            'id': conv.id,
            'type': conv.type,
            'name': display_name,
            'avatar': conv.avatar,
            'unread_count': participant.unread_count,
            'updated_at': conv.updated_at.isoformat() + 'Z' if conv.updated_at else None
        }
        
        # 对于直接对话，添加目标用户ID
        if conv.type == 'direct':
            target_participant = ConversationParticipant.query.filter(
                ConversationParticipant.conversation_id == conv.id,
                ConversationParticipant.user_id != user_id,
                ConversationParticipant.left_at.is_(None)
            ).first()
            if target_participant:
                conv_data['target_user_id'] = target_participant.user_id
        
        if last_message:
            conv_data['last_message'] = {
                'id': last_message.id,
                'sender_id': last_message.sender_id,
                'content': last_message.content if last_message.message_type == 'text' else None,
                'message_type': last_message.message_type,
                'created_at': last_message.created_at.isoformat() + 'Z' if last_message.created_at else None
            }
        
        result.append(conv_data)
    
    return success_response('获取成功', {
        'conversations': result,
        'total': len(result)
    })


@conversations_bp.route('/<int:conversation_id>', methods=['GET'])
@token_required
def get_conversation_detail(conversation_id):
    user_id = request.current_user_id
    
    if not check_conversation_permission(conversation_id, user_id):
        return forbidden_response('无权访问该会话')
    
    conv = Conversation.query.get(conversation_id)
    if not conv or conv.deleted_at:
        return not_found_response('会话不存在')
    
    user_remarks = {f'{ur.user_id}_{ur.target_user_id}': ur.remark for ur in UserRemark.query.filter_by(user_id=user_id).all()}
    users_dict = {u.id: u for u in User.query.all()}
    display_name = get_conversation_display_name(conv, user_id, user_remarks, users_dict)
    
    participants = ConversationParticipant.query.filter_by(
        conversation_id=conversation_id,
        left_at=None
    ).all()
    
    return success_response('获取成功', {
        'conversation': {
            'id': conv.id,
            'type': conv.type,
            'name': display_name,
            'avatar': conv.avatar,
            'creator_id': conv.creator_id,
            'created_at': conv.created_at.isoformat() + 'Z' if conv.created_at else None,
            'updated_at': conv.updated_at.isoformat() + 'Z' if conv.updated_at else None,
            'participants': [p.to_dict() for p in participants]
        }
    })


@conversations_bp.route('', methods=['POST'])
@token_required
def create_conversation():
    user_id = request.current_user_id
    data = request.get_json()
    
    if not data or not data.get('type'):
        return bad_request_response('会话类型不能为空')
    
    conv_type = data['type']
    
    if conv_type == 'direct':
        target_user_id = data.get('target_user_id')
        if not target_user_id:
            return bad_request_response('目标用户ID不能为空')
        
        if target_user_id == user_id:
            return bad_request_response('不能创建与自己的会话')
        
        # 查找已存在的直接对话
        user_participations = ConversationParticipant.query.filter_by(
            user_id=user_id,
            left_at=None
        ).all()
        
        existing_conv = None
        for p in user_participations:
            conv = Conversation.query.get(p.conversation_id)
            if conv and conv.type == 'direct' and conv.deleted_at is None:
                # 检查目标用户是否也参与了这个对话
                target_participation = ConversationParticipant.query.filter_by(
                    conversation_id=conv.id,
                    user_id=target_user_id,
                    left_at=None
                ).first()
                if target_participation:
                    existing_conv = conv
                    break
        
        if existing_conv:
            return success_response('会话已存在', {'conversation_id': existing_conv.id})
        
        conv = Conversation(type='direct', creator_id=user_id)
        db.session.add(conv)
        db.session.flush()
        
        db.session.add(ConversationParticipant(conversation_id=conv.id, user_id=user_id, role='owner'))
        db.session.add(ConversationParticipant(conversation_id=conv.id, user_id=target_user_id, role='owner'))
        
    elif conv_type == 'group':
        name = data.get('name')
        if not name:
            return bad_request_response('群聊名称不能为空')
        
        participant_ids = data.get('participant_ids', [])
        if user_id not in participant_ids:
            participant_ids.append(user_id)
        
        conv = Conversation(type='group', name=name, avatar=data.get('avatar'), creator_id=user_id)
        db.session.add(conv)
        db.session.flush()
        
        db.session.add(ConversationParticipant(conversation_id=conv.id, user_id=user_id, role='owner'))
        for pid in participant_ids:
            if pid != user_id:
                db.session.add(ConversationParticipant(conversation_id=conv.id, user_id=pid, role='member'))
    else:
        return bad_request_response('无效的会话类型')
    
    db.session.commit()
    return created_response('创建成功', {'conversation_id': conv.id})


@conversations_bp.route('/<int:conversation_id>', methods=['PUT'])
@token_required
def update_conversation(conversation_id):
    user_id = request.current_user_id
    data = request.get_json()
    
    conv = Conversation.query.get(conversation_id)
    if not conv or conv.deleted_at:
        return not_found_response('会话不存在')
    
    if conv.type == 'group':
        role = get_participant_role(conversation_id, user_id)
        if role not in ['owner', 'admin']:
            return forbidden_response('无权修改群聊信息')
        
        if 'name' in data:
            conv.name = data['name']
        if 'avatar' in data:
            conv.avatar = data['avatar']
    else:
        return bad_request_response('一对一会话不支持修改')
    
    db.session.commit()
    return success_response('更新成功')


@conversations_bp.route('/<int:conversation_id>', methods=['DELETE'])
@token_required
def delete_conversation(conversation_id):
    user_id = request.current_user_id
    
    if not check_conversation_permission(conversation_id, user_id):
        return forbidden_response('无权访问该会话')
    
    conv = Conversation.query.get(conversation_id)
    if not conv:
        return not_found_response('会话不存在')
    
    conv.deleted_at = db.func.now()
    db.session.commit()
    
    return success_response('删除成功')


@conversations_bp.route('/<int:conversation_id>/messages', methods=['GET'])
@token_required
def get_messages(conversation_id):
    user_id = request.current_user_id
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)
    
    if not check_conversation_permission(conversation_id, user_id):
        return forbidden_response('无权访问该会话')
    
    messages = Message.query.filter_by(
        conversation_id=conversation_id,
        is_deleted=False
    ).order_by(Message.created_at.desc()).paginate(page=page, per_page=page_size, error_out=False)
    
    user_remarks = {f'{ur.user_id}_{ur.target_user_id}': ur.remark for ur in UserRemark.query.filter_by(user_id=user_id).all()}
    users_dict = {u.id: u for u in User.query.all()}
    
    result = []
    for msg in reversed(messages.items):
        display_name = get_user_display_name(msg.sender_id, user_id, user_remarks, users_dict)
        msg_data = msg.to_dict(display_name=display_name)
        result.append(msg_data)
    
    return success_response('获取成功', {
        'messages': result,
        'total': messages.total,
        'page': page,
        'page_size': page_size,
        'pages': messages.pages
    })


@conversations_bp.route('/<int:conversation_id>/messages', methods=['POST'])
@token_required
def send_message(conversation_id):
    user_id = request.current_user_id
    data = request.get_json()
    
    if not check_conversation_permission(conversation_id, user_id):
        return forbidden_response('无权访问该会话')
    
    if not data or not data.get('message_type'):
        return bad_request_response('消息类型不能为空')
    
    message_type = data['message_type']
    
    if message_type == 'text' and not data.get('content'):
        return bad_request_response('文本内容不能为空')
    
    if message_type in ['image', 'file'] and not data.get('file_url'):
        return bad_request_response('文件URL不能为空')
    
    user = User.query.get(user_id)
    
    message = Message(
        conversation_id=conversation_id,
        sender_id=user_id,
        sender_username=user.username,
        sender_avatar=user.user_img,
        message_type=message_type,
        content=data.get('content'),
        file_url=data.get('file_url'),
        file_name=data.get('file_name'),
        file_size=data.get('file_size'),
        reply_to_id=data.get('reply_to_id')
    )
    
    db.session.add(message)
    db.session.flush()
    
    conv = Conversation.query.get(conversation_id)
    conv.updated_at = message.created_at
    
    participants = ConversationParticipant.query.filter(
        ConversationParticipant.conversation_id == conversation_id,
        ConversationParticipant.user_id != user_id,
        ConversationParticipant.left_at.is_(None)
    ).all()
    
    for p in participants:
        p.unread_count += 1
        create_message_notification(p.user_id, conversation_id, message.id, user.username, data.get('content', ''))
    
    db.session.commit()
    
    return created_response('发送成功', {'message': message.to_dict()})


@conversations_bp.route('/<int:conversation_id>/messages/<int:message_id>/read', methods=['POST'])
@token_required
def mark_message_read(conversation_id, message_id):
    user_id = request.current_user_id
    
    if not check_conversation_permission(conversation_id, user_id):
        return forbidden_response('无权访问该会话')
    
    message = Message.query.filter_by(id=message_id, conversation_id=conversation_id).first()
    if not message:
        return not_found_response('消息不存在')
    
    participant = ConversationParticipant.query.filter_by(
        conversation_id=conversation_id,
        user_id=user_id
    ).first()
    
    if participant:
        participant.last_read_message_id = message_id
        participant.unread_count = 0
        db.session.commit()
    
    return success_response('标记成功')


@conversations_bp.route('/user-remarks', methods=['GET'])
@token_required
def get_user_remarks():
    user_id = request.current_user_id
    remarks = UserRemark.query.filter_by(user_id=user_id).all()
    
    return success_response('获取成功', {
        'remarks': [r.to_dict() for r in remarks]
    })


@conversations_bp.route('/user-remarks', methods=['POST'])
@token_required
def create_user_remark():
    user_id = request.current_user_id
    data = request.get_json()
    
    if not data or not data.get('target_user_id') or not data.get('remark'):
        return bad_request_response('参数不完整')
    
    if data['target_user_id'] == user_id:
        return bad_request_response('不能给自己设置备注')
    
    existing = UserRemark.query.filter_by(
        user_id=user_id,
        target_user_id=data['target_user_id']
    ).first()
    
    if existing:
        existing.remark = data['remark']
    else:
        existing = UserRemark(
            user_id=user_id,
            target_user_id=data['target_user_id'],
            remark=data['remark']
        )
        db.session.add(existing)
    
    db.session.commit()
    return created_response('设置成功', {'remark': existing.to_dict()})


@conversations_bp.route('/user-remarks/<int:target_user_id>', methods=['DELETE'])
@token_required
def delete_user_remark(target_user_id):
    user_id = request.current_user_id
    
    remark = UserRemark.query.filter_by(user_id=user_id, target_user_id=target_user_id).first()
    if not remark:
        return not_found_response('备注不存在')
    
    db.session.delete(remark)
    db.session.commit()
    
    return success_response('删除成功')


@conversations_bp.route('/notifications', methods=['GET'])
@token_required
def get_notifications():
    user_id = request.current_user_id
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    is_read = request.args.get('is_read', type=bool)
    notif_type = request.args.get('type')
    
    query = Notification.query.filter_by(user_id=user_id)
    
    if is_read is not None:
        query = query.filter_by(is_read=is_read)
    
    if notif_type:
        query = query.filter_by(type=notif_type)
    
    notifications = query.order_by(Notification.created_at.desc()).paginate(
        page=page, per_page=page_size, error_out=False
    )
    
    return success_response('获取成功', {
        'notifications': [n.to_dict() for n in notifications.items],
        'total': notifications.total,
        'page': page,
        'page_size': page_size
    })


@conversations_bp.route('/notifications/<int:notification_id>/read', methods=['PUT'])
@token_required
def mark_notification_read(notification_id):
    user_id = request.current_user_id
    
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if not notification:
        return not_found_response('通知不存在')
    
    notification.is_read = True
    db.session.commit()
    
    return success_response('标记成功')


@conversations_bp.route('/notifications/read-all', methods=['PUT'])
@token_required
def mark_all_notifications_read():
    user_id = request.current_user_id
    
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    return success_response('标记成功')
