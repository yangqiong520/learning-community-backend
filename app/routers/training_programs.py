from flask import Blueprint, request, url_for
from libs.db import db
from app.models.training_program import TrainingProgram
from app.models.like import Like
from libs.jwt_auth import token_required, role_required
from libs.response import success_response, created_response, bad_request_response, not_found_response, forbidden_response
from app.models.file import File as FileModel
from app.utils.simple_document_extractor import extract_document_content_simple, is_supported_document
from app.utils.office_converter import OfficeToPDFConverter

training_bp = Blueprint('training_programs', __name__, url_prefix='/api/v2/training_programs')

UPLOAD_FOLDER = 'storage'
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

def save_file(file):
    if not file or file.filename == '':
        return None

    file_size = len(file.read()) if hasattr(file, 'read') else 0
    file.seek(0)

    if file_size > MAX_FILE_SIZE:
        return None

    file_type = FileModel.detect_file_type(file.filename)
    original_filename = file.filename

    if not original_filename or original_filename == '':
        return None

    file_ext = os.path.splitext(original_filename)[1].lower().lstrip('.')
    new_filename = f"{uuid.uuid4().hex}.{file_ext}"

    if file_type == FileModel.FILE_TYPE_IMAGE:
        upload_path = os.path.join(UPLOAD_FOLDER, 'images')
    elif file_type == FileModel.FILE_TYPE_VIDEO:
        upload_path = os.path.join(UPLOAD_FOLDER, 'videos')
    elif file_type == FileModel.FILE_TYPE_DOCUMENT:
        upload_path = os.path.join(UPLOAD_FOLDER, 'documents')
    else:
        upload_path = os.path.join(UPLOAD_FOLDER, 'others')

    file_path = os.path.join(upload_path, new_filename)

    file.save(file_path)
    file_size_saved = os.path.getsize(file_path)

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

    # 自动转换为 PDF
    if FileModel.is_office_document(file_path) and file_type == FileModel.FILE_TYPE_DOCUMENT:
        converter = OfficeToPDFConverter()
        if converter.libreoffice_path:
            try:
                print(f"[Office Conversion] Starting conversion for training program document")
                pdf_output_dir = os.path.join(UPLOAD_FOLDER, 'pdfs')
                os.makedirs(pdf_output_dir, exist_ok=True)
                pdf_path = converter.convert_to_pdf(file_path, pdf_output_dir)

                if pdf_path and os.path.exists(pdf_path):
                    print(f"[Office Conversion] Conversion successful {pdf_path}")

                    # 创建 PDF 文件记录
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

                    # 关联 PDF 到文档
                    file_record.pdf_file_id = pdf_file_record.id
                    db.session.commit()

                    print(f"[Office Conversion] PDF linked: doc_file_id={file_record.id}, pdf_file_id={pdf_file_record.id}")
                else:
                    print(f"[Office Conversion] Conversion failed: {original_filename}")
            except Exception as e:
                print(f"[Office Conversion] Error during conversion: {str(e)}")
                # 转换失败不影响上传，只记录日志
        else:
            print("[Office Conversion] LibreOffice not available, skipping conversion")

    return file_record

@training_bp.route('/upload', methods=['POST'])
@token_required
def create_training_program():
    if 'title' not in request.form:
        return bad_request_response('标题不能为空')

    if 'document' not in request.files:
        return bad_request_response('请上传文档文件')

    if 'image' not in request.files:
        return bad_request_response('请上传图片文件')

    title = request.form.get('title')
    content = request.form.get('content')  # 可选，客户端不提供时会自动提取

    document = request.files.get('document')
    image = request.files.get('image')

    if not document or not image or document.filename == '' or image.filename == '':
        return bad_request_response('文件不能为空')

    document_filename = document.filename
    image_filename = image.filename

    document_type = FileModel.detect_file_type(document_filename)
    image_type = FileModel.detect_file_type(image_filename)

    if document_type != FileModel.FILE_TYPE_DOCUMENT:
        return bad_request_response('文档格式不支持')

    if image_type != FileModel.FILE_TYPE_IMAGE:
        return bad_request_response('图片格式不支持')

    # 保存图片文件
    file_ext = os.path.splitext(image_filename)[1].lower().lstrip('.')
    new_image_filename = f"{uuid.uuid4().hex}.{file_ext}"
    upload_image_path = os.path.join(UPLOAD_FOLDER, 'images')
    os.makedirs(upload_image_path, exist_ok=True)
    image_file_path = os.path.join(upload_image_path, new_image_filename)

    image.save(image_file_path)
    image_size = os.path.getsize(image_file_path)

    image_file_record = FileModel(
        filename=new_image_filename,
        original_filename=image_filename,
        file_type=image_type,
        file_size=image_size,
        file_path=image_file_path,
        mime_type=image.content_type,
        uploader_id=request.current_user_id
    )

    db.session.add(image_file)
    db.session.commit()
    print(f"[File Upload] Image saved with ID: {image_file_record.id}")

    # 保存文档文件
    file_ext = os.path.splitext(document_filename)[1].lower().lstrip('.')
    new_document_filename = f"{uuid.uuid4().hex}.{file_ext}"
    upload_document_path = os.path.join(UPLOAD_FOLDER, 'documents')
    os.makedirs(upload_document_path, exist_ok=True)
    document_file_path = os.path.join(upload_document_path, new_document_filename)

    document.save(document_file_path)
    document_size = os.path.getsize(document_file_path)

    document_file_record = FileModel(
        filename=new_document_filename,
        original_filename=document_filename,
        file_type=document_type,
        file_size=document_size,
        file_path=document_file_path,
        mime_type=document.content_type,
        uploader_id=request.current_user_id
    )

    db.session.add(document_file_record)
    db.session.commit()
    print(f"[File Upload] Document saved with ID: {document_file_record.id}")

    # 自动转换为 PDF
    if FileModel.is_office_document(document_file_path):
        converter = OfficeToPDFConverter()
        if converter.libreoffice_path:
            try:
                print(f"[Office Conversion] Starting conversion for training program document")
                pdf_output_dir = os.path.join(UPLOAD_FOLDER, 'pdfs')
                os.makedirs(pdf_output_dir, exist_ok=True)
                pdf_path = converter.convert_to_pdf(document_file_path, pdf_output_dir)

                if pdf_path and os.path.exists(pdf_path):
                    print(f"[Office Conversion] Conversion successful {pdf_path}")

                    # 创建 PDF 文件记录
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

                    # 关联 PDF 到文档
                    document_file_record.pdf_file_id = pdf_file_record.id
                    db.session.commit()

                    print(f"[Office Conversion] PDF linked: doc_file_id={document_file_record.id}, pdf_file_id={pdf_file_record.id}")
                else:
                    print(f"[Office Conversion] Conversion failed: {document_filename}")
            except Exception as e:
                print(f"[Office Conversion] Error during conversion: {str(e)}")
                # 转换失败不影响上传，只记录日志
        else:
            print("[Office Conversion] LibreOffice not available, skipping conversion")

    # 如果没有提供content，自动提取文档内容
    if not content and is_supported_document(document_filename):
        try:
            content = extract_document_content_simple(document_file_path)
            print(f"[Document Extraction] Auto-extracted content length: {len(content)} chars")
        except Exception as e:
            print(f"[Document Extraction] Error: {str(e)}")
            content = f"文档内容自动提取失败: {str(e)}"

    # 创建培训计划
    training_program = TrainingProgram(
        title=title,
        content=content,
        document_file_id=document_file_record.id,
        image_file_id=image_file_record.id,
        uploader_id=request.current_user_id
    )

    db.session.add(training_program)
    db.session.commit()

    print(f"[Training Program] Created with ID: {training_program.id}")

    return created_response('发布成功', {'training_program': training_program.to_dict(request.current_user_id)})

@training_bp.route('', methods=['GET'])
@training_bp.route('/', methods=['GET'])
@token_required
def list_training_programs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    keyword = request.args.get('keyword', '')

    query = TrainingProgram.query

    if keyword:
        query = query.filter(
            (TrainingProgram.title.like(f'%{keyword}%')) |
            (TrainingProgram.content.like(f'%{keyword}%'))
        )

    query = query.order_by(TrainingProgram.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    training_programs = pagination.items

    return success_response('获取成功', {
        'training_programs': [tp.to_dict(request.current_user_id) for tp in training_programs],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    })

@training_bp.route('/<int:training_program_id>', methods=['GET'])
@token_required
def get_training_program(training_program_id):
    training_program = TrainingProgram.query.get(training_program_id)

    if not training_program:
        return not_found_response('培训计划不存在')

    return success_response('获取成功', {'training_program': training_program.to_dict(request.current_user_id)})

@training_bp.route('/<int:training_program_id>', methods=['PUT'])
@token_required
def update_training_program(training_program_id):
    training_program = TrainingProgram.query.get(training_program_id)

    if not training_program:
        return not_found_response('培训计划不存在')

    if training_program.uploader_id != request.current_user_id:
        return forbidden_response('无权更新此培训计划')

    data = request.get_json() if request.is_json else request.form.to_dict()

    if 'title' in data:
        training_program.title = data['title']

    if 'content' in data:
        training_program.content = data['content']

    db.session.commit()

    return success_response('更新成功', {'training_program': training_program.to_dict(request.current_user_id)})

@training_bp.route('/<int:training_program_id>', methods=['DELETE'])
@token_required
def delete_training_program(training_program_id):
    training_program = TrainingProgram.query.get(training_program_id)

    if not training_program:
        return not_found_response('培训计划不存在')

    if training_program.uploader_id != request.current_user_id:
        return forbidden_response('无权删除此培训计划')

    # 删除文件
    if training_program.document_file_id:
        from app.models.file import File as FileModel
        document_file = FileModel.query.get(training_program.document_file_id)
        if document_file and os.path.exists(document_file.file_path):
            os.remove(document_file.file_path)

    if training_program.image_file_id:
        from app.models.file import File as FileModel
        image_file = FileModel.query.get(training_program.image_file_id)
        if image_file and os.path.exists(image_file.file_path):
            os.remove(image_file.file_path)

    # 删除PDF文件
    if document_file and document_file.pdf_file_id:
        from app.models.file import File as FileModel
        pdf_file = FileModel.query.get(document_file.pdf_file_id)
        if pdf_file and os.path.exists(pdf_file.file_path):
            os.remove(pdf_file.file_path)

    # 删除培训计划记录
    db.session.delete(training_program)

    # 删除关联的PDF文件
    if document_file and document_file.pdf_file_id:
        db.session.delete(pdf_file)

    db.session.commit()

    return success_response('删除成功')

@training_bp.route('/<int:training_program_id>/collect', methods=['POST'])
@token_required
def toggle_collect(training_program_id):
    training_program = TrainingProgram.query.get(training_program_id)

    if not training_program:
        return not_found_response('培训计划不存在')

    existing_like = Like.query.filter_by(
        training_program_id=training_program_id,
        user_id=request.current_user_id
    ).first()

    if existing_like:
        db.session.delete(existing_like)
        is_liked = False
    else:
        new_like = Like(
            training_program_id=training_program_id,
            user_id=request.current_user_id
        )
        db.session.add(new_like)
        is_liked = True

    db.session.commit()

    return success_response('操作成功', {'like': is_liked})