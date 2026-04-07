import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, url_for
from libs.db import db
from app.models.courseware import Courseware
from app.models.like import Like
from app.models.file import File as FileModel
from app.utils.simple_document_extractor import extract_document_content_simple, is_supported_document
from app.utils.office_converter import OfficeToPDFConverter
from libs.jwt_auth import token_required, role_required
from libs.response import success_response, created_response, bad_request_response, not_found_response, forbidden_response

courseware_bp = Blueprint('coursewares', __name__, url_prefix='/api/v2/coursewares')

UPLOAD_FOLDER = 'storage'
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


@courseware_bp.route('/upload', methods=['POST'])
@token_required
def upload_courseware():
    if 'document' not in request.files:
        return bad_request_response('请上传文档文件')
    
    if 'image' not in request.files:
        return bad_request_response('请上传图片文件')
    
    document = request.files['document']
    image = request.files['image']
    
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    
    if not title:
        return bad_request_response('标题不能为空')
    
    document_filename = document.filename
    image_filename = image.filename

    document_type = FileModel.detect_file_type(document_filename)
    image_type = FileModel.detect_file_type(image_filename)
    
    if document_type != FileModel.FILE_TYPE_DOCUMENT:
        return bad_request_response('文档格式不支持')
    
    if image_type != FileModel.FILE_TYPE_IMAGE:
        return bad_request_response('图片格式不支持')
    
    file_ext = os.path.splitext(document_filename)[1].lower().lstrip('.')
    new_document_filename = f"{uuid.uuid4().hex}.{file_ext}"
    
    img_ext = os.path.splitext(image_filename)[1].lower().lstrip('.')
    new_image_filename = f"{uuid.uuid4().hex}.{img_ext}"
    
    upload_document_path = os.path.join(UPLOAD_FOLDER, 'documents')
    upload_image_path = os.path.join(UPLOAD_FOLDER, 'images')
    
    os.makedirs(upload_document_path, exist_ok=True)
    os.makedirs(upload_image_path, exist_ok=True)
    
    document.save(os.path.join(upload_document_path, new_document_filename))
    image.save(os.path.join(upload_image_path, new_image_filename))
    
    document_size = os.path.getsize(os.path.join(upload_document_path, new_document_filename))
    image_size = os.path.getsize(os.path.join(upload_image_path, new_image_filename))
    
    document_file = FileModel(
        filename=new_document_filename,
        original_filename=document_filename,
        file_type=FileModel.FILE_TYPE_DOCUMENT,
        file_size=document_size,
        file_path=os.path.join(upload_document_path, new_document_filename),
        mime_type=document.mimetype,
        uploader_id=request.current_user_id
    )
    
    image_file = FileModel(
        filename=new_image_filename,
        original_filename=image_filename,
        file_type=FileModel.FILE_TYPE_IMAGE,
        file_size=image_size,
        file_path=os.path.join(upload_image_path, new_image_filename),
        mime_type=image.mimetype,
        uploader_id=request.current_user_id
    )
    
    db.session.add(document_file)
    db.session.add(image_file)
    db.session.commit()

    # 检测是否为Office文档，自动转换为PDF
    converter = OfficeToPDFConverter()
    if FileModel.is_office_document(document_file.file_path) and converter.libreoffice_path:
        try:
            print(f"[Office Conversion] Starting conversion for courseware document: {document_filename}")
            pdf_output_dir = os.path.join(UPLOAD_FOLDER, 'pdfs')
            pdf_path = converter.convert_to_pdf(document_file.file_path, pdf_output_dir)

            if pdf_path and os.path.exists(pdf_path):
                print(f"[Office Conversion] Conversion successful: {pdf_path}")

                # 创建PDF文件记录
                pdf_filename = os.path.basename(pdf_path)
                pdf_file_record = FileModel(
                    filename=pdf_filename,
                    original_filename=os.path.splitext(document_filename)[0] + '.pdf',
                    file_type=FileModel.FILE_TYPE_DOCUMENT,
                    file_size=os.path.getsize(pdf_path),
                    file_path=pdf_path,
                    mime_type='application/pdf',
                    uploader_id=request.current_user_id
                )

                db.session.add(pdf_file_record)
                db.session.commit()

                # 关联PDF到原文档文件
                document_file.pdf_file_id = pdf_file_record.id
                db.session.commit()

                print(f"[Office Conversion] PDF linked: doc_file_id={document_file.id}, pdf_file_id={pdf_file_record.id}")
            else:
                print(f"[Office Conversion] Conversion failed: {document_filename}")
        except Exception as e:
            print(f"[Office Conversion] Error during conversion: {str(e)}")
            # 转换失败不影响上传，只记录日志

    if not content and is_supported_document(document_filename):
        try:
            content = extract_document_content_simple(document_file.file_path)
        except Exception as e:
            content = f"文档内容提取失败: {str(e)}"

    courseware = Courseware(
        title=title,
        content=content,
        document_file_id=document_file.id,
        image_file_id=image_file.id,
        uploader_id=request.current_user_id
    )

    db.session.add(courseware)
    db.session.commit()

    return created_response('上传成功', {'courseware': courseware.to_dict(request.current_user_id)})


@courseware_bp.route('', methods=['GET'])
@courseware_bp.route('/', methods=['GET'])
@token_required
def list_coursewares():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    keyword = request.args.get('keyword', '')
    
    query = Courseware.query
    
    if keyword:
        query = query.filter(
            (Courseware.title.like(f'%{keyword}%')) |
            (Courseware.content.like(f'%{keyword}%'))
        )
    
    query = query.order_by(Courseware.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    coursewares = pagination.items
    
    return success_response('获取成功', {
        'coursewares': [c.to_dict(request.current_user_id) for c in coursewares],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@courseware_bp.route('/<int:courseware_id>', methods=['GET'])
@token_required
def get_courseware(courseware_id):
    courseware = Courseware.query.get(courseware_id)
    
    if not courseware:
        return not_found_response('教案课件不存在')
    
    return success_response('获取成功', {'courseware': courseware.to_dict(request.current_user_id)})


@courseware_bp.route('/<int:courseware_id>', methods=['PUT'])
@token_required
def update_courseware(courseware_id):
    if request.current_user_role not in [1, 3, 4]:
        return forbidden_response('无权限修改')
    
    courseware = Courseware.query.get(courseware_id)
    
    if not courseware:
        return not_found_response('教案课件不存在')
    
    if courseware.uploader_id != request.current_user_id and request.current_user_role != 1 and request.current_user_role != 4:
        return forbidden_response('无权限修改')
    
    data = request.get_json()
    
    if 'title' in data:
        courseware.title = data['title']
    
    if 'content' in data:
        courseware.content = data['content']
    
    courseware.updated_at = datetime.utcnow()
    db.session.commit()
    
    return success_response('更新成功', {'courseware': courseware.to_dict(request.current_user_id)})


@courseware_bp.route('/<int:courseware_id>', methods=['DELETE'])
@token_required
def delete_courseware(courseware_id):
    if request.current_user_role not in [1, 3, 4]:
        return forbidden_response('无权限删除')
    
    courseware = Courseware.query.get(courseware_id)
    
    if not courseware:
        return not_found_response('教案课件不存在')
    
    if courseware.uploader_id != request.current_user_id and request.current_user_role != 1 and request.current_user_role != 4:
        return forbidden_response('无权限删除')
    
    courseware.is_active = False
    db.session.commit()
    
    return success_response('删除成功')


@courseware_bp.route('/<int:courseware_id>/like', methods=['POST'])
@token_required
def toggle_like_courseware(courseware_id):
    courseware = Courseware.query.get(courseware_id)
    
    if not courseware:
        return not_found_response('教案课件不存在')
    
    existing_like = Like.query.filter_by(
        courseware_id=courseware_id,
        user_id=request.current_user_id
    ).first()
    
    if existing_like:
        db.session.delete(existing_like)
        is_liked = False
    else:
        new_like = Like(
            courseware_id=courseware_id,
            user_id=request.current_user_id
        )
        db.session.add(new_like)
        is_liked = True
    
    db.session.commit()
    
    return success_response('操作成功', {
        'courseware': courseware.to_dict(request.current_user_id),
        'is_liked': is_liked
    })
