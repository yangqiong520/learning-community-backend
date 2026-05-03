import os
import uuid
from datetime import datetime
from flask import Blueprint, request, url_for
from libs.db import db
from app.models.teaching_plan import TeachingPlan
from app.models.like import Like
from libs.jwt_auth import token_required, role_required
from libs.response import success_response, created_response, bad_request_response, not_found_response, forbidden_response, error_response
from app.models.file import File as FileModel
from app.utils.simple_document_extractor import extract_document_content_simple, is_supported_document
from app.utils.office_converter import OfficeToPDFConverter
from app.utils.pdf_to_image import PDFToImageConverter

teaching_bp = Blueprint('teaching_plans', __name__, url_prefix='/api/v2/teaching_plans')

UPLOAD_FOLDER = 'storage'
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

converter = OfficeToPDFConverter()
img_converter = PDFToImageConverter()

def detect_file_type(filename):
    if not filename or '.' not in filename:
        return FileModel.FILE_TYPE_OTHER

    ext = os.path.splitext(filename)[1].lower().lstrip('.')

    for file_type, extensions in FileModel.FILE_EXTENSIONS.items():
        if ext in extensions:
            return file_type

    return FileModel.FILE_TYPE_OTHER

def save_file(file):
    print(f"DEBUG: save_file called with file: {file}")
    print(f"DEBUG: file.filename: {file.filename if file else 'None'}")
    print(f"DEBUG: file type: {type(file)}")
    
    if not file or file.filename == '':
        print(f"DEBUG: File is None or empty")
        return None

    file_size = len(file.read()) if hasattr(file, 'read') else 0
    file.seek(0)
    
    print(f"DEBUG: file_size: {file_size}")
    
    if file_size > MAX_FILE_SIZE:
        print(f"DEBUG: File size exceeds limit")
        return None

    file_type = detect_file_type(file.filename)
    original_filename = file.filename

    if not original_filename or original_filename == '':
        print(f"DEBUG: Invalid filename")
        return None

    file_ext = os.path.splitext(original_filename)[1].lower().lstrip('.')
    new_filename = f"{uuid.uuid4().hex}.{file_ext}"

    print(f"DEBUG: Detected file type: {file_type}")
    print(f"DEBUG: File extension: {file_ext}")
    print(f"DEBUG: New filename: {new_filename}")

    if file_type == FileModel.FILE_TYPE_IMAGE:
        upload_path = os.path.join(UPLOAD_FOLDER, 'images')
    elif file_type == FileModel.FILE_TYPE_VIDEO:
        upload_path = os.path.join(UPLOAD_FOLDER, 'videos')
    elif file_type == FileModel.FILE_TYPE_DOCUMENT:
        upload_path = os.path.join(UPLOAD_FOLDER, 'documents')
    else:
        upload_path = os.path.join(UPLOAD_FOLDER, 'others')

    file_path = os.path.join(upload_path, new_filename)

    print(f"DEBUG: Upload path: {file_path}")
    
    file.save(file_path)
    file_size_saved = os.path.getsize(file_path)

    print(f"DEBUG: File saved, size: {file_size_saved}")

    mime_type = file.content_type

    file_record = FileModel(
        filename=new_filename,
        original_filename=original_filename,
        file_type=file_type,
        file_size=file_size_saved,
        file_path=file_path,
        mime_type=mime_type,
        uploader_id=request.current_user_id
    )

    db.session.add(file_record)
    db.session.commit()
    
    print(f"DEBUG: File record created with ID: {file_record.id}")
    
    # 检测是否为Office文档，自动转换为PDF
    pdf_file_path = None
    if FileModel.is_office_document(file_path) and converter.libreoffice_path:
        try:
            print(f"[Office Conversion] Starting conversion for: {original_filename}")
            pdf_output_dir = os.path.join(UPLOAD_FOLDER, 'pdfs')
            os.makedirs(pdf_output_dir, exist_ok=True)
            pdf_path = converter.convert_to_pdf(file_path, pdf_output_dir)

            if pdf_path and os.path.exists(pdf_path):
                print(f"[Office Conversion] Conversion successful: {pdf_path}")
                pdf_file_path = pdf_path

                # 创建PDF文件记录
                pdf_filename = os.path.basename(pdf_path)
                pdf_file_record = FileModel(
                    filename=pdf_filename,
                    original_filename=os.path.splitext(original_filename)[0] + '.pdf',
                    file_type=FileModel.FILE_TYPE_DOCUMENT,
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
            else:
                print(f"[Office Conversion] Conversion failed: {original_filename}")
        except Exception as e:
            print(f"[Office Conversion] Error during conversion: {str(e)}")

    # 如果文件本身就是PDF，或者Office文档转换成功，自动生成预览图片
    source_pdf_path = pdf_file_path if pdf_file_path else (file_path if file_ext == 'pdf' else None)

    if source_pdf_path and img_converter.imagick_path:
        try:
            print(f"[Image Generation] Starting preview image generation for: {original_filename}")
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
                    original_filename=f"{os.path.splitext(original_filename)[0]}_preview.jpg",
                    file_type=FileModel.FILE_TYPE_IMAGE,
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
                print(f"[Image Generation] Preview image generation failed for: {original_filename}")
        except Exception as e:
            print(f"[Image Generation] Error during image generation: {str(e)}")
            # 图片生成失败不影响上传，只记录日志
    elif not img_converter.imagick_path and source_pdf_path:
        print(f"[Image Generation] ImageMagick not found, skipping preview image generation")
    
    return file_record

@teaching_bp.route('/upload', methods=['POST'])
@token_required
def create_teaching_plan():
    print(f"DEBUG: Request method: {request.method}")
    print(f"DEBUG: Request form keys: {list(request.form.keys())}")
    print(f"DEBUG: Request files keys: {list(request.files.keys())}")
    
    data = request.form.to_dict()
    
    print(f"DEBUG: Parsed form data: {data}")
    
    if 'title' not in data:
        return bad_request_response('标题不能为空')
    
    if 'document' not in request.files:
        return bad_request_response('请上传文档文件')
    
    # 图片是可选的，如果没有上传，将使用文档自动生成的预览图片
    image = request.files.get('image')
    
    title = data.get('title')
    content = data.get('content')  # 可选，客户端不提供时会自动提取
    
    print(f"DEBUG: title length: {len(title) if title else 0}")
    print(f"DEBUG: content length: {len(content) if content else 0}")
    print(f"DEBUG: content first 200 chars: {content[:200] if content else None}")
    newline_char = '\n'
    print(f"DEBUG: content newline count: {content.count(newline_char) if content else 0}")
    
    document = request.files.get('document')
    
    print(f"DEBUG: document file: {document}")
    print(f"DEBUG: image file: {image if image else '未提供'}")
    
    document_file = save_file(document)
    
    if not document_file:
        return bad_request_response('文档文件上传失败')
    
    # 图片是可选的，如果没有上传，将使用文档自动生成的预览图片
    image_file = None
    if image:
        image_file = save_file(image)
        print(f"DEBUG: 上传的图片文件记录ID: {image_file.id}")
    elif document_file and document_file.image_file_id:
        # 没有上传图片，但文档已经自动生成了预览图片
        image_file = FileModel.query.get(document_file.image_file_id)
        print(f"[DEBUG] 使用文档自动生成的预览图片，ID: {image_file.id}")
    else:
        # 没有上传图片，且文档也没有自动生成预览图片
        # 检测文档类型，如果是PDF，自动生成预览图
        document_type = detect_file_type(document.filename)
        if document_type == FileModel.FILE_TYPE_DOCUMENT:
            document_ext = os.path.splitext(document.filename)[1].lower().lstrip('.')
            if document_ext == 'pdf':
                # PDF文档，自动生成预览图
                if img_converter.imagick_path:
                    try:
                        print(f"[DEBUG] 自动生成PDF预览图: {document.filename}")
                        image_output_dir = os.path.join(upload_path, 'images')
                        os.makedirs(image_output_dir, exist_ok=True)
                        
                        image_path = img_converter.pdf_to_thumbnail(document_file.file_path, image_output_dir, width=400, height=300)
                        
                        if image_path and os.path.exists(image_path):
                            print(f"[DEBUG] PDF预览图生成成功: {image_path}")
                            
                            image_filename = os.path.basename(image_path)
                            image_file = FileModel(
                                filename=image_filename,
                                original_filename=f"{os.path.splitext(document.filename)[0]}_preview.jpg",
                                file_type=FileModel.FILE_TYPE_IMAGE,
                                file_size=os.path.getsize(image_path),
                                file_path=image_path,
                                mime_type='image/jpeg',
                                uploader_id=request.current_user_id
                            )
                            
                            db.session.add(image_file)
                            db.session.commit()
                            
                            # 关联图片到文档
                            document_file.image_file_id = image_file.id
                            db.session.commit()
                            
                            print(f"[DEBUG] PDF预览图关联成功: file_id={document_file.id}, image_file_id={image_file.id}")
                        else:
                            print(f"[DEBUG] PDF预览图生成失败: {document.filename}")
                    except Exception as e:
                        print(f"[DEBUG] PDF预览图生成错误: {str(e)}")
                else:
                    print(f"[DEBUG] ImageMagick not found, skipping PDF preview image generation")
            else:
                # 其他文档格式，必须上传图片
                return bad_request_response('请上传图片文件')
    
    # 如果没有提供content，自动提取文档内容
    if not content and document_file.file_path:
        print(f"DEBUG: 没有提供content，尝试自动提取文档内容")
        print(f"DEBUG: 文档路径: {document_file.file_path}")
        print(f"DEBUG: 支持的文档格式: {is_supported_document(document_file.file_path)}")
        
        if is_supported_document(document_file.file_path):
            try:
                content = extract_document_content_simple(document_file.file_path)
                print(f"DEBUG: 自动提取的内容长度: {len(content)} 字符")
                print(f"DEBUG: 提取的前200字符: {content[:200]}")
            except Exception as e:
                print(f"DEBUG: 文档内容提取失败: {e}")
                content = f"文档内容自动提取失败: {str(e)}"
        else:
            print(f"DEBUG: 不支持的文档格式，使用默认内容")
            content = "无法自动提取此格式文档的内容，请手动提供内容"
    elif content:
        print(f"DEBUG: 使用客户端提供的content，长度: {len(content)} 字符")
    else:
        content = "未提供文档内容"
    
    teaching_plan = TeachingPlan(
        title=title,
        content=content,
        file_file_id=document_file.id,
        image_file_id=image_file.id if image_file else None,
        uploader_id=request.current_user_id
    )

    db.session.add(teaching_plan)
    db.session.commit()

    return created_response('发布成功', {'teaching_plan': teaching_plan.to_dict(request.current_user_id)})

@teaching_bp.route('', methods=['GET'])
@teaching_bp.route('/', methods=['GET'])
@token_required
def list_teaching_plans():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    keyword = request.args.get('keyword', '')
    
    query = TeachingPlan.query
    
    if keyword:
        query = query.filter(
            (TeachingPlan.title.like(f'%{keyword}%')) |
            (TeachingPlan.content.like(f'%{keyword}%'))
        )
    
    query = query.order_by(TeachingPlan.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    teaching_plans = pagination.items
    
    return success_response('获取成功', {
        'teaching_plans': [t.to_dict(request.current_user_id) for t in teaching_plans],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })

@teaching_bp.route('/<int:teaching_plan_id>', methods=['GET'])
@token_required
def get_teaching_plan(teaching_plan_id):
    teaching_plan = TeachingPlan.query.get(teaching_plan_id)
    
    if not teaching_plan:
        return not_found_response('教学计划不存在')
    
    return success_response('获取成功', {'teaching_plan': teaching_plan.to_dict(request.current_user_id)})

@teaching_bp.route('/<int:teaching_plan_id>', methods=['PUT'])
@token_required
@role_required([1, 3, 4])  # 超级管理员、教师和管理员
def update_teaching_plan(teaching_plan_id):
    teaching_plan = TeachingPlan.query.get(teaching_plan_id)
    
    if not teaching_plan:
        return not_found_response('教学计划不存在')
    
    if teaching_plan.uploader_id != request.current_user_id and request.current_user_role != 1 and request.current_user_role != 4:
        return forbidden_response('无权限修改')
    
    data = request.get_json()
    
    if 'title' in data:
        teaching_plan.title = data['title']
    
    if 'content' in data:
        teaching_plan.content = data['content']
    
    teaching_plan.updated_at = datetime.utcnow()
    db.session.commit()
    
    return success_response('更新成功', {'teaching_plan': teaching_plan.to_dict(request.current_user_id)})

@teaching_bp.route('/<int:teaching_plan_id>', methods=['DELETE'])
@token_required
@role_required([1, 3, 4])  # 超级管理员、教师和管理员
def delete_teaching_plan(teaching_plan_id):
    teaching_plan = TeachingPlan.query.get(teaching_plan_id)
    
    if not teaching_plan:
        return not_found_response('教学计划不存在')
    
    if teaching_plan.uploader_id != request.current_user_id and request.current_user_role != 1 and request.current_user_role != 4:
        return forbidden_response('无权限删除')
    
    teaching_plan.is_active = False
    db.session.commit()
    
    return success_response('删除成功')

@teaching_bp.route('/<int:teaching_plan_id>/like', methods=['POST'])
@token_required
def toggle_like_teaching_plan(teaching_plan_id):
    try:
        print(f"[DEBUG] 教学计划点赞 - 用户ID: {request.current_user_id}, 教学计划ID: {teaching_plan_id}", flush=True)
        
        teaching_plan = TeachingPlan.query.get(teaching_plan_id)
        
        if not teaching_plan or not teaching_plan.is_active:
            return not_found_response('教学计划不存在')
        
        existing_like = Like.query.filter_by(
            teaching_plan_id=teaching_plan_id,
            user_id=request.current_user_id
        ).first()
        
        print(f"[DEBUG] 现有点赞记录: {existing_like is not None}", flush=True)
        
        if existing_like:
            print(f"[DEBUG] 取消点赞", flush=True)
            db.session.delete(existing_like)
            is_liked = False
        else:
            print(f"[DEBUG] 添加点赞", flush=True)
            new_like = Like(
                user_id=request.current_user_id,
                teaching_plan_id=teaching_plan_id
            )
            db.session.add(new_like)
            is_liked = True
        
        db.session.commit()
        print(f"[DEBUG] 数据库提交成功, is_liked: {is_liked}", flush=True)
        
        return success_response('操作成功', {
            'teaching_plan': teaching_plan.to_dict(request.current_user_id),
            'is_liked': is_liked
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error in toggle_like_teaching_plan: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        return error_response(f'操作失败: {str(e)}')

@teaching_bp.route('/favorites', methods=['GET'])
@token_required
def get_teaching_plan_favorites():
    """获取当前用户收藏的教学计划列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 12, type=int)
        
        print(f"[DEBUG] 教学计划收藏列表 - 用户ID: {request.current_user_id}, page: {page}", flush=True)
        
        # 查询用户收藏的教学计划，按收藏时间倒序，支持分页
        query = Like.query.filter(
            Like.user_id == request.current_user_id,
            Like.teaching_plan_id != None
        )
        likes = query.order_by(Like.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        print(f"[DEBUG] 查询到 {len(likes.items)} 条收藏记录", flush=True)
        
        # 构建结果列表
        result = []
        for like in likes.items:
            if like.teaching_plan_id:
                teaching_plan = TeachingPlan.query.get(like.teaching_plan_id)
                if teaching_plan:
                    item = teaching_plan.to_dict(request.current_user_id)
                    # 添加收藏时间
                    if like.created_at:
                        item['favorite_time'] = f"{like.created_at.year}.{like.created_at.month}.{like.created_at.day}"
                    else:
                        item['favorite_time'] = None
                    result.append(item)
        
        print(f"[DEBUG] 返回 {len(result)} 条教学计划收藏", flush=True)
        
        return success_response('获取收藏列表成功', {
            'teaching_plans': result,
            'total': likes.total,
            'page': page,
            'per_page': per_page,
            'pages': likes.pages
        })
    except Exception as e:
        print(f"Error in get_teaching_plan_favorites: {str(e)}", flush=True)
        return error_response(f'获取收藏列表失败: {str(e)}')
