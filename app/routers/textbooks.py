import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, url_for
from libs.db import db
from app.models.textbook import Textbook
from app.models.like import Like
from app.models.file import File as FileModel
from app.utils.simple_document_extractor import extract_document_content_simple, is_supported_document
from app.utils.office_converter import OfficeToPDFConverter
from app.utils.pdf_to_image import PDFToImageConverter
from libs.jwt_auth import token_required, role_required
from libs.response import success_response, created_response, bad_request_response, not_found_response, forbidden_response, error_response

textbook_bp = Blueprint('textbooks', __name__, url_prefix='/api/v2/textbooks')

UPLOAD_FOLDER = 'storage'
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

converter = OfficeToPDFConverter()
img_converter = PDFToImageConverter()


@textbook_bp.route('/upload', methods=['POST'])
@token_required
def upload_textbook():
    if 'document' not in request.files:
        return bad_request_response('请上传文档文件')
    
    # 图片是可选的，如果没有上传，将使用文档自动生成的预览图片
    image = request.files.get('image')
    
    document = request.files['document']
    
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    
    if not title:
        return bad_request_response('标题不能为空')
    
    document_filename = document.filename
    
    document_type = FileModel.detect_file_type(document_filename)
    
    if document_type != FileModel.FILE_TYPE_DOCUMENT:
        return bad_request_response('文档格式不支持')
    
    file_ext = os.path.splitext(document_filename)[1].lower().lstrip('.')
    new_document_filename = f"{uuid.uuid4().hex}.{file_ext}"
    
    upload_document_path = os.path.join(UPLOAD_FOLDER, 'documents')
    
    os.makedirs(upload_document_path, exist_ok=True)
    
    document.save(os.path.join(upload_document_path, new_document_filename))
    document_size = os.path.getsize(os.path.join(upload_document_path, new_document_filename))
    
    document_file = FileModel(
        filename=new_document_filename,
        original_filename=document_filename,
        file_type=FileModel.FILE_TYPE_DOCUMENT,
        file_size=document_size,
        file_path=os.path.join(upload_document_path, new_document_filename),
        mime_type=document.mimetype,
        uploader_id=request.current_user_id
    )
    
    db.session.add(document_file)
    db.session.commit()
    print(f"[File Upload] Document saved with ID: {document_file.id}")

    # 检测是否为Office文档，自动转换为PDF
    pdf_file_path = None
    if FileModel.is_office_document(document_file.file_path) and converter.libreoffice_path:
        try:
            print(f"[Office Conversion] Starting conversion for textbook document: {document_filename}")
            pdf_output_dir = os.path.join(UPLOAD_FOLDER, 'pdfs')
            pdf_path = converter.convert_to_pdf(document_file.file_path, pdf_output_dir)

            if pdf_path and os.path.exists(pdf_path):
                print(f"[Office Conversion] Conversion successful: {pdf_path}")
                pdf_file_path = pdf_path

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

    # 如果文件本身就是PDF，或者Office文档转换成功，自动生成预览图片
    source_pdf_path = pdf_file_path if pdf_file_path else (document_file.file_path if file_ext == 'pdf' else None)

    if source_pdf_path and img_converter.imagick_path:
        try:
            print(f"[Image Generation] Starting preview image generation for: {document_filename}")
            image_output_dir = os.path.join(UPLOAD_FOLDER, 'images')
            os.makedirs(image_output_dir, exist_ok=True)

            # 生成缩略图（更适合预览）
            image_path = img_converter.pdf_to_thumbnail(source_pdf_path, image_output_dir, width=400, height=300)

            if image_path and os.path.exists(image_path):
                print(f"[Image Generation] Preview image generated: {image_path}")

                # 创建图片文件记录
                image_filename = os.path.basename(image_path)
                image_file_record = FileModel(
                    filename=image_filename,
                    original_filename=f"{os.path.splitext(document_filename)[0]}_preview.jpg",
                    file_type=FileModel.FILE_TYPE_IMAGE,
                    file_size=os.path.getsize(image_path),
                    file_path=image_path,
                    mime_type='image/jpeg',
                    uploader_id=request.current_user_id
                )

                db.session.add(image_file_record)
                db.session.commit()

                # 关联图片到原文件
                document_file.image_file_id = image_file_record.id
                db.session.commit()

                print(f"[Image Generation] Image linked: file_id={document_file.id}, image_file_id={image_file_record.id}")
            else:
                print(f"[Image Generation] Preview image generation failed for: {document_filename}")
        except Exception as e:
            print(f"[Image Generation] Error during image generation: {str(e)}")
            # 图片生成失败不影响上传，只记录日志
    elif not img_converter.imagick_path and source_pdf_path:
        print(f"[Image Generation] ImageMagick not found, skipping preview image generation")
    
    # 图片是可选的，如果没有上传，将使用文档自动生成的预览图片
    image_file = None
    if image:
        # 手动上传的图片
        file_ext = os.path.splitext(image.filename)[1].lower().lstrip('.')
        new_image_filename = f"{uuid.uuid4().hex}.{file_ext}"
        upload_image_path = os.path.join(UPLOAD_FOLDER, 'images')
        os.makedirs(upload_image_path, exist_ok=True)
        
        image.save(os.path.join(upload_image_path, new_image_filename))
        image_size = os.path.getsize(os.path.join(upload_image_path, new_image_filename))
        
        image_file = FileModel(
            filename=new_image_filename,
            original_filename=image.filename,
            file_type=FileModel.detect_file_type(image.filename),
            file_size=image_size,
            file_path=os.path.join(upload_image_path, new_image_filename),
            mime_type=image.mimetype,
            uploader_id=request.current_user_id
        )
        
        db.session.add(image_file)
        db.session.commit()
        print(f"[File Upload] Image saved with ID: {image_file.id}")
    elif document_file and document_file.image_file_id:
        # 没有上传图片，但文档已经自动生成了预览图片
        image_file = FileModel.query.get(document_file.image_file_id)
        print(f"[File Upload] Using auto-generated preview image, ID: {image_file.id}")
    
    if not content and is_supported_document(document_filename):
        try:
            content = extract_document_content_simple(document_file.file_path)
        except Exception as e:
            content = f"文档内容提取失败: {str(e)}"
    
    textbook = Textbook(
        title=title,
        content=content,
        document_file_id=document_file.id,
        image_file_id=image_file.id if image_file else None,
        uploader_id=request.current_user_id
    )
    
    db.session.add(textbook)
    db.session.commit()
    
    return created_response('上传成功', {'textbook': textbook.to_dict(request.current_user_id)})


@textbook_bp.route('', methods=['GET'])
@textbook_bp.route('/', methods=['GET'])
@token_required
def list_textbooks():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    keyword = request.args.get('keyword', '')
    
    query = Textbook.query
    
    if keyword:
        query = query.filter(
            (Textbook.title.like(f'%{keyword}%')) |
            (Textbook.content.like(f'%{keyword}%'))
        )
    
    query = query.order_by(Textbook.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    textbooks = pagination.items
    
    return success_response('获取成功', {
        'textbooks': [t.to_dict(request.current_user_id) for t in textbooks],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })


@textbook_bp.route('/<int:textbook_id>', methods=['GET'])
@token_required
def get_textbook(textbook_id):
    textbook = Textbook.query.get(textbook_id)
    
    if not textbook:
        return not_found_response('教材不存在')
    
    return success_response('获取成功', {'textbook': textbook.to_dict(request.current_user_id)})


@textbook_bp.route('/<int:textbook_id>', methods=['PUT'])
@token_required
def update_textbook(textbook_id):
    if request.current_user_role not in [1, 3, 4]:
        return forbidden_response('无权限修改')
    
    textbook = Textbook.query.get(textbook_id)
    
    if not textbook:
        return not_found_response('教材不存在')
    
    if textbook.uploader_id != request.current_user_id and request.current_user_role != 1 and request.current_user_role != 4:
        return forbidden_response('无权限修改')
    
    data = request.get_json()
    
    if 'title' in data:
        textbook.title = data['title']
    
    if 'content' in data:
        textbook.content = data['content']
    
    textbook.updated_at = datetime.utcnow()
    db.session.commit()
    
    return success_response('更新成功', {'textbook': textbook.to_dict(request.current_user_id)})


@textbook_bp.route('/<int:textbook_id>', methods=['DELETE'])
@token_required
def delete_textbook(textbook_id):
    if request.current_user_role not in [1, 3, 4]:
        return forbidden_response('无权限删除')
    
    textbook = Textbook.query.get(textbook_id)
    
    if not textbook:
        return not_found_response('教材不存在')
    
    if textbook.uploader_id != request.current_user_id and request.current_user_role != 1 and request.current_user_role != 4:
        return forbidden_response('无权限删除')
    
    textbook.is_active = False
    db.session.commit()
    
    return success_response('删除成功')


@textbook_bp.route('/<int:textbook_id>/like', methods=['POST'])
@token_required
def toggle_like_textbook(textbook_id):
    try:
        textbook = Textbook.query.get(textbook_id)
        
        if not textbook:
            return not_found_response('教材不存在')
        
        existing_like = Like.query.filter_by(
            textbook_id=textbook_id,
            user_id=request.current_user_id
        ).first()
        
        if existing_like:
            db.session.delete(existing_like)
            is_liked = False
        else:
            new_like = Like(
                textbook_id=textbook_id,
                user_id=request.current_user_id
            )
            db.session.add(new_like)
            is_liked = True
        
        db.session.commit()
        
        return success_response('操作成功', {
            'textbook': textbook.to_dict(request.current_user_id),
            'is_liked': is_liked
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in toggle_like_textbook: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        return error_response(f'操作失败: {str(e)}')

@textbook_bp.route('/favorites', methods=['GET'])
@token_required
def get_textbook_favorites():
    """获取当前用户收藏的教材列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        
        # 查询用户收藏的教材，按收藏时间倒序，支持分页
        query = Like.query.filter(
            Like.user_id == request.current_user_id,
            Like.textbook_id != None
        )
        likes = query.order_by(Like.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # 构建结果列表
        result = []
        for like in likes.items:
            if like.textbook_id:
                textbook = Textbook.query.get(like.textbook_id)
                if textbook:
                    item = textbook.to_dict(request.current_user_id)
                    # 添加收藏时间
                    if like.created_at:
                        item['favorite_time'] = f"{like.created_at.year}.{like.created_at.month}.{like.created_at.day}"
                    else:
                        item['favorite_time'] = None
                    result.append(item)
        
        return success_response('获取收藏列表成功', {
            'textbooks': result,
            'total': likes.total,
            'page': page,
            'per_page': per_page,
            'pages': likes.pages
        })
    except Exception as e:
        return error_response(f'获取收藏列表失败: {str(e)}')
