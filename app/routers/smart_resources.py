import os
import uuid
from flask import Blueprint, request
from werkzeug.utils import secure_filename
from libs.db import db
from app.models.smart_resource import SmartResource
from app.models.like import Like
from app.models.file import File as FileModel
from app.models.user import User
from libs.jwt_auth import token_required, role_required
from libs.response import success_response, created_response, bad_request_response, not_found_response, forbidden_response, error_response
from app.utils.video_processor import VideoProcessor

smart_resources_bp = Blueprint('smart_resources', __name__, url_prefix='/api/v2/smart-resources')

UPLOAD_FOLDER = 'storage'
MAX_FILE_SIZE = 500 * 1024 * 1024
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm', '3gp'}

video_processor = VideoProcessor()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


def save_video_file(file):
    if not file or file.filename == '':
        return None

    if not allowed_file(file.filename):
        return None

    if request.content_length and request.content_length > MAX_FILE_SIZE:
        return None

    original_filename = file.filename
    file_ext = os.path.splitext(original_filename)[1].lower().lstrip('.')
    new_filename = f"{uuid.uuid4().hex}.{file_ext}"

    upload_path = os.path.join(UPLOAD_FOLDER, 'videos')
    os.makedirs(upload_path, exist_ok=True)

    file_path = os.path.join(upload_path, new_filename)
    file.save(file_path)
    file_size = os.path.getsize(file_path)
    mime_type = file.content_type or 'video/mp4'

    file_record = FileModel(
        filename=new_filename,
        original_filename=original_filename,
        file_type=FileModel.FILE_TYPE_VIDEO,
        file_size=file_size,
        file_path=file_path,
        mime_type=mime_type,
        uploader_id=request.current_user_id
    )

    db.session.add(file_record)
    db.session.commit()

    return file_record


@smart_resources_bp.route('', methods=['GET'])
@token_required
def get_smart_resources():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        search = request.args.get('search', '', type=str)
        sort_by = request.args.get('sort_by', 'created_at', type=str)
        sort_order = request.args.get('sort_order', 'desc', type=str)

        if page < 1:
            return bad_request_response('页码必须大于0')
        if per_page < 1 or per_page > 100:
            return bad_request_response('每页数量必须在1-100之间')

        query = SmartResource.query

        if search:
            query = query.filter(SmartResource.title.like(f'%{search}%'))

        if sort_by == 'play_count':
            if sort_order == 'asc':
                query = query.order_by(SmartResource.play_count.asc())
            else:
                query = query.order_by(SmartResource.play_count.desc())
        elif sort_by == 'created_at':
            if sort_order == 'asc':
                query = query.order_by(SmartResource.created_at.asc())
            else:
                query = query.order_by(SmartResource.created_at.desc())
        else:
            query = query.order_by(SmartResource.created_at.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        resources = pagination.items

        return success_response('获取成功', {
            'resources': [resource.to_dict(request.current_user_id) for resource in resources],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
    except Exception as e:
        return error_response(f'获取失败: {str(e)}')


@smart_resources_bp.route('', methods=['POST'])
@role_required(User.ROLE_SUPER_ADMIN, User.ROLE_ADMIN, User.ROLE_TEACHER)
def create_smart_resource():
    try:
        title = request.form.get('title', '').strip()
        video = request.files.get('video')

        if not title:
            return bad_request_response('标题不能为空')
        if len(title) > 200:
            return bad_request_response('标题不能超过200个字符')

        if not video or video.filename == '':
            return bad_request_response('请上传视频文件')

        if not allowed_file(video.filename):
            return bad_request_response('不支持的视频格式')

        video_file = save_video_file(video)

        if not video_file:
            return bad_request_response('视频上传失败')

        if not video_processor.is_valid_video(video_file.file_path):
            db.session.delete(video_file)
            db.session.commit()
            return bad_request_response('上传的视频文件无效')

        duration = video_processor.get_video_duration(video_file.file_path)

        thumbnail_path = video_processor.extract_thumbnail(
            video_file.file_path,
            os.path.join(UPLOAD_FOLDER, 'images')
        )

        if not thumbnail_path:
            db.session.delete(video_file)
            db.session.commit()
            return error_response('提取视频缩略图失败')

        thumbnail_file_record = FileModel(
            filename=os.path.basename(thumbnail_path),
            original_filename=f"{title}_thumb.jpg",
            file_type=FileModel.FILE_TYPE_IMAGE,
            file_size=os.path.getsize(thumbnail_path),
            file_path=thumbnail_path,
            mime_type='image/jpeg',
            uploader_id=request.current_user_id
        )

        db.session.add(thumbnail_file_record)
        db.session.commit()

        smart_resource = SmartResource(
            title=title,
            video_file_id=video_file.id,
            thumbnail_file_id=thumbnail_file_record.id,
            duration=duration,
            play_count=0,
            uploader_id=request.current_user_id
        )

        db.session.add(smart_resource)
        db.session.commit()

        return created_response('上传成功', {'resource': smart_resource.to_dict()})
    except Exception as e:
        db.session.rollback()
        return error_response(f'上传失败: {str(e)}')


@smart_resources_bp.route('/<int:resource_id>', methods=['GET'])
@token_required
def get_smart_resource(resource_id):
    try:
        resource = SmartResource.query.get(resource_id)

        if not resource:
            return not_found_response('智能资源不存在')

        return success_response('获取成功', {'resource': resource.to_dict(request.current_user_id)})
    except Exception as e:
        return error_response(f'获取失败: {str(e)}')


@smart_resources_bp.route('/<int:resource_id>', methods=['DELETE'])
@token_required
def delete_smart_resource(resource_id):
    try:
        resource = SmartResource.query.get(resource_id)

        if not resource:
            return not_found_response('智能资源不存在')

        user_role = request.current_user_role

        if resource.uploader_id != request.current_user_id and user_role not in [User.ROLE_SUPER_ADMIN, User.ROLE_ADMIN]:
            return forbidden_response('无权删除该智能资源')

        video_file = FileModel.query.get(resource.video_file_id)
        thumbnail_file = FileModel.query.get(resource.thumbnail_file_id)

        db.session.delete(resource)

        if video_file:
            try:
                if os.path.exists(video_file.file_path):
                    os.remove(video_file.file_path)
                db.session.delete(video_file)
            except Exception as e:
                print(f"删除视频文件失败: {e}")

        if thumbnail_file:
            try:
                if os.path.exists(thumbnail_file.file_path):
                    os.remove(thumbnail_file.file_path)
                db.session.delete(thumbnail_file)
            except Exception as e:
                print(f"删除缩略图文件失败: {e}")

        db.session.commit()

        return success_response('删除成功')
    except Exception as e:
        db.session.rollback()
        return error_response(f'删除失败: {str(e)}')


@smart_resources_bp.route('/<int:resource_id>/play', methods=['POST'])
@token_required
def increment_play_count(resource_id):
    try:
        resource = SmartResource.query.get(resource_id)

        if not resource:
            return not_found_response('智能资源不存在')

        resource.play_count += 1
        db.session.commit()

        return success_response('播放次数已更新', {
            'play_count': SmartResource.format_play_count(resource.play_count)
        })
    except Exception as e:
        db.session.rollback()
        return error_response(f'更新失败: {str(e)}')


@smart_resources_bp.route('/<int:resource_id>/like', methods=['POST'])
@token_required
def toggle_like(resource_id):
    try:
        resource = SmartResource.query.get(resource_id)

        if not resource:
            return not_found_response('智能资源不存在')

        existing_like = Like.query.filter_by(
            smart_resource_id=resource_id,
            user_id=request.current_user_id
        ).first()

        if existing_like:
            db.session.delete(existing_like)
            db.session.commit()
            return success_response('已取消点赞', {'is_liked': False})
        else:
            new_like = Like(
                smart_resource_id=resource_id,
                user_id=request.current_user_id
            )
            db.session.add(new_like)
            db.session.commit()
            return success_response('点赞成功', {'is_liked': True})
    except Exception as e:
        db.session.rollback()
        return error_response(f'操作失败: {str(e)}')


@smart_resources_bp.route('/<int:resource_id>/like-status', methods=['GET'])
@token_required
def get_like_status(resource_id):
    try:
        resource = SmartResource.query.get(resource_id)

        if not resource:
            return not_found_response('智能资源不存在')

        is_liked = Like.query.filter_by(
            smart_resource_id=resource_id,
            user_id=request.current_user_id
        ).first() is not None

        return success_response('获取成功', {'is_liked': is_liked})
    except Exception as e:
        return error_response(f'获取失败: {str(e)}')


@smart_resources_bp.route('/liked', methods=['GET'])
@token_required
def get_liked_resources():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)

        if page < 1:
            return bad_request_response('页码必须大于0')
        if per_page < 1 or per_page > 100:
            return bad_request_response('每页数量必须在1-100之间')

        query = Like.query.filter(
            Like.smart_resource_id.isnot(None),
            Like.user_id == request.current_user_id
        )

        pagination = query.order_by(Like.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        likes = pagination.items
        resources = [like.smart_resource for like in likes if like.smart_resource]

        return success_response('获取成功', {
            'resources': [resource.to_dict(request.current_user_id) for resource in resources],
            'total': len(resources),
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        return error_response(f'获取失败: {str(e)}')
