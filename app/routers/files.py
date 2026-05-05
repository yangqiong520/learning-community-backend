import os
import uuid
from flask import Blueprint, request, send_from_directory, jsonify, url_for
from werkzeug.utils import secure_filename
from libs.db import db
from app.models.file import File
from app.models.user import User
from libs.jwt_auth import token_required
from libs.response import success_response, created_response, bad_request_response, not_found_response, forbidden_response
from app.utils.office_converter import OfficeToPDFConverter
from app.utils.pdf_to_image import PDFToImageConverter

files_bp = Blueprint('files', __name__, url_prefix='/api/v2/files')

UPLOAD_FOLDER = 'storage'
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

def upload_file_logic(file):
    """
    文件上传逻辑，供其他模块调用
    """
    if not file or file.filename == '':
        return None

    if request.content_length and request.content_length > MAX_FILE_SIZE:
        return None

    file_type = File.detect_file_type(file.filename)
    original_filename = file.filename

    if not original_filename or original_filename == '':
        return None

    file_ext = os.path.splitext(original_filename)[1].lower().lstrip('.')
    new_filename = f"{uuid.uuid4().hex}.{file_ext}"

    if file_type == File.FILE_TYPE_IMAGE:
        upload_path = os.path.join(UPLOAD_FOLDER, 'images')
    elif file_type == File.FILE_TYPE_VIDEO:
        upload_path = os.path.join(UPLOAD_FOLDER, 'videos')
    elif file_type == File.FILE_TYPE_DOCUMENT:
        upload_path = os.path.join(UPLOAD_FOLDER, 'documents')
    else:
        upload_path = os.path.join(UPLOAD_FOLDER, 'others')

    file_path = os.path.join(upload_path, new_filename)

    file.save(file_path)
    file_size = os.path.getsize(file_path)
    mime_type = file.content_type

    file_record = File(
        filename=new_filename,
        original_filename=original_filename,
        file_type=file_type,
        file_size=file_size,
        file_path=file_path,
        mime_type=mime_type,
        uploader_id=request.current_user_id
    )

    db.session.add(file_record)
    db.session.commit()

    # 检测是否为Office文档，自动转换为PDF
    converter = OfficeToPDFConverter()
    img_converter = PDFToImageConverter()
    if File.is_office_document(file_path) and converter.libreoffice_path:
        try:
            print(f"[Office Conversion] Starting conversion for: {original_filename}")
            pdf_output_dir = os.path.join(UPLOAD_FOLDER, 'pdfs')
            pdf_path = converter.convert_to_pdf(file_path, pdf_output_dir)
            
            if pdf_path and os.path.exists(pdf_path):
                print(f"[Office Conversion] Conversion successful: {pdf_path}")
                
                # 创建PDF文件记录
                pdf_filename = os.path.basename(pdf_path)
                pdf_file_record = File(
                    filename=pdf_filename,
                    original_filename=os.path.splitext(original_filename)[0] + '.pdf',
                    file_type=File.FILE_TYPE_DOCUMENT,
                    file_size=os.path.getsize(pdf_path),
                    file_path=pdf_path,
                    mime_type='application/pdf',
                    uploader_id=request.current_user_id
                )
                
                db.session.add(pdf_file_record)
                db.session.commit()
                
                # 关联PDF到原文件
                file_record.pdf_file_id = pdf_file_record.id
                db.session.commit()
                
                print(f"[Office Conversion] PDF linked: file_id={file_record.id}, pdf_file_id={pdf_file_record.id}")
                
                # 自动从PDF生成预览图片
                if img_converter.imagick_path:
                    try:
                        print(f"[Image Generation] Starting preview image generation for: {pdf_filename}")
                        image_output_dir = os.path.join(UPLOAD_FOLDER, 'images')
                        os.makedirs(image_output_dir, exist_ok=True)
                        
                        # 生成缩略图（更适合预览）
                        image_path = img_converter.pdf_to_thumbnail(pdf_path, image_output_dir, width=400, height=300)
                        
                        if image_path and os.path.exists(image_path):
                            print(f"[Image Generation] Preview image generated: {image_path}")
                            
                            # 创建图片文件记录
                            image_filename = os.path.basename(image_path)
                            image_file_record = File(
                                filename=image_filename,
                                original_filename=f"{os.path.splitext(original_filename)[0]}_preview.jpg",
                                file_type=File.FILE_TYPE_IMAGE,
                                file_size=os.path.getsize(image_path),
                                file_path=image_path,
                                mime_type='image/jpeg',
                                uploader_id=request.current_user_id
                            )
                            
                            db.session.add(image_file_record)
                            db.session.commit()
                            
                            # 关联图片到原文件
                            file_record.image_file_id = image_file_record.id
                            db.session.commit()
                            
                            print(f"[Image Generation] Image linked: file_id={file_record.id}, image_file_id={image_file_record.id}")
                        else:
                            print(f"[Image Generation] Preview image generation failed for: {pdf_filename}")
                    except Exception as e:
                        print(f"[Image Generation] Error during image generation: {str(e)}")
                        # 图片生成失败不影响上传，只记录日志
                else:
                    print(f"[Image Generation] ImageMagick not found, skipping preview image generation")
            else:
                print(f"[Office Conversion] Conversion failed: {original_filename}")
        except Exception as e:
            print(f"[Office Conversion] Error during conversion: {str(e)}")
            # 转换失败不影响上传，只记录日志

    return file_record.to_dict()

@files_bp.route('/upload', methods=['POST'])
@token_required
def upload_file():
    if 'file' not in request.files:
        return bad_request_response('没有上传文件')
    
    file = request.files['file']
    
    # 上传文件逻辑
    file_record = upload_file_logic(file)
    
    if not file_record:
        return bad_request_response('文件上传失败')
    
    return created_response('上传成功', {
        'file': file_record
    })

@files_bp.route('/preview/<int:file_id>', methods=['GET'])
@token_required
def get_file_preview(file_id):
    """获取文件预览URL（Office文档返回PDF预览URL）"""
    file_record = File.query.get(file_id)
    
    if not file_record or not file_record.is_active:
        return not_found_response('文件不存在')
    
    # 优先返回PDF URL（如果Office文档已转换）
    if file_record.pdf_file_id:
        pdf_file = File.query.get(file_record.pdf_file_id)
        if pdf_file and pdf_file.is_active and os.path.exists(pdf_file.file_path):
            return success_response('获取成功', {
                'file_id': file_record.id,
                'preview_url': url_for('files.serve_file', file_id=pdf_file.id, _external=True),
                'preview_type': 'pdf'
            })
    
    # PDF文件直接返回
    if file_record.file_type == File.FILE_TYPE_DOCUMENT and file_record.original_filename.lower().endswith('.pdf'):
        return success_response('获取成功', {
            'file_id': file_record.id,
            'preview_url': url_for('files.serve_file', file_id=file_record.id, _external=True),
            'preview_type': 'pdf'
        })
    
    # 图片文件直接返回
    if file_record.file_type == File.FILE_TYPE_IMAGE:
        return success_response('获取成功', {
            'file_id': file_record.id,
            'preview_url': url_for('files.serve_file', file_id=file_record.id, _external=True),
            'preview_type': 'image'
        })
    
    # 其他文件类型不支持预览
    return bad_request_response('此文件类型不支持预览')

@files_bp.route('/<int:file_id>', methods=['GET'])
@token_required
def get_file(file_id):
    """获取文件信息"""
    file_record = File.query.get(file_id)
    
    if not file_record:
        return not_found_response('文件不存在')
    
    if not file_record.is_active:
        return forbidden_response('文件已被删除')
    
    return success_response('获取成功', {'file': file_record.to_dict()})

@files_bp.route('/url/<int:file_id>', methods=['GET'])
@token_required
def get_file_url(file_id):
    """获取文件下载URL"""
    file_record = File.query.get(file_id)
    
    if not file_record:
        return not_found_response('文件不存在')
    
    if not file_record.is_active:
        return forbidden_response('文件已被删除')
    
    from flask import url_for
    
    file_url = url_for('files.serve_file', file_id=file_record.id, _external=True)
    
    return success_response('获取成功', {
        'file_id': file_record.id,
        'file_url': file_url,
        'original_filename': file_record.original_filename
    })

@files_bp.route('/serve/<int:file_id>', methods=['GET'])
@token_required
def serve_file(file_id):
    """返回文件内容（需要认证）"""
    file_record = File.query.get(file_id)
    
    if not file_record:
        return not_found_response('文件不存在')
    
    if not file_record.is_active:
        return forbidden_response('文件已被删除')
    
    file_path = file_record.file_path
    if not os.path.exists(file_path):
        return not_found_response('文件不存在')
    
    # 根据文件类型设置 Content-Type
    if file_record.file_type == File.FILE_TYPE_IMAGE:
        content_type = file_record.mime_type or 'image/jpeg'
    elif file_record.file_type == File.FILE_TYPE_VIDEO:
        content_type = file_record.mime_type or 'video/mp4'
    elif file_record.file_type == File.FILE_TYPE_DOCUMENT:
        # 对于Office文档，提示用户下载PDF版本
        content_type = file_record.mime_type or 'application/octet-stream'
    else:
        content_type = 'application/octet-stream'
    
    return send_from_directory(
        os.path.dirname(file_path),
        os.path.basename(file_path),
        mimetype=content_type,
        as_attachment=(file_record.file_type != File.FILE_TYPE_IMAGE)
    )

@files_bp.route('/serve-image/<int:file_id>', methods=['GET'])
def serve_image_public(file_id):
    """公开的图片服务接口，用于加载预览图片（不需要认证）"""
    file_record = File.query.get(file_id)
    
    if not file_record:
        return not_found_response('文件不存在')
    
    if not file_record.is_active:
        return forbidden_response('文件已被删除')
    
    # 只允许访问图片类型的文件
    if file_record.file_type != File.FILE_TYPE_IMAGE:
        return bad_request_response('此接口仅支持图片文件')
    
    file_path = file_record.file_path
    if not os.path.exists(file_path):
        return not_found_response('文件不存在')
    
    content_type = file_record.mime_type or 'image/jpeg'
    
    return send_from_directory(
        os.path.dirname(file_path),
        os.path.basename(file_path),
        mimetype=content_type,
        as_attachment=False
    )

@files_bp.route('/serve-video/<int:file_id>', methods=['GET'])
def serve_video_public(file_id):
    """公开的视频服务接口，用于播放视频（不需要认证）"""
    file_record = File.query.get(file_id)
    
    if not file_record:
        return not_found_response('文件不存在')
    
    if not file_record.is_active:
        return forbidden_response('文件已被删除')
    
    # 只允许访问视频类型的文件
    if file_record.file_type != File.FILE_TYPE_VIDEO:
        return bad_request_response('此接口仅支持视频文件')
    
    file_path = file_record.file_path
    if not os.path.exists(file_path):
        return not_found_response('文件不存在')
    
    content_type = file_record.mime_type or 'video/mp4'
    
    return send_from_directory(
        os.path.dirname(file_path),
        os.path.basename(file_path),
        mimetype=content_type,
        as_attachment=False
    )

@files_bp.route('', methods=['GET'])
@token_required
def list_files():
    """获取文件列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    file_type = request.args.get('type')
    keyword = request.args.get('keyword', '')
    uploader_id = request.args.get('uploader_id', type=int)
    
    query = File.query
    
    if file_type:
        query = query.filter_by(file_type=file_type)
    
    if uploader_id:
        query = query.filter_by(uploader_id=uploader_id)
    
    if keyword:
        query = query.filter(
            (File.original_filename.like(f'%{keyword}%')) |
            (File.filename.like(f'%{keyword}%'))
        )
    
    query = query.filter_by(is_active=True)
    query = query.order_by(File.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    files = pagination.items
    
    return success_response('获取成功', {
        'files': [file.to_dict() for file in files],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })

@files_bp.route('/<int:file_id>', methods=['DELETE'])
@token_required
def delete_file(file_id):
    """删除文件"""
    file_record = File.query.get(file_id)
    
    if not file_record:
        return not_found_response('文件不存在')
    
    if file_record.uploader_id != request.current_user_id:
        return forbidden_response('无权限删除此文件')
    
    if os.path.exists(file_record.file_path):
        os.remove(file_record.file_path)
    
    db.session.delete(file_record)
    db.session.commit()
    
    return success_response('删除成功')
