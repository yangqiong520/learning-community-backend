import os
import subprocess
from PIL import Image
from pdf2image import convert_from_path
from app.models.file import File
from libs.db import db

def convert_office_to_pdf(file_path, output_dir):
    """
    将Office文档转换为PDF
    :param file_path: Office文件路径
    :param output_dir: 输出目录
    :return: PDF文件路径，失败返回None
    """
    try:
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        
        if ext.lower() not in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp']:
            return None
        
        pdf_filename = f"{name}.pdf"
        pdf_path = os.path.join(output_dir, pdf_filename)
        
        subprocess.run([
            'soffice',
            '--headless',
            '--convert-to',
            'pdf',
            '--outdir',
            output_dir,
            file_path
        ], check=True, capture_output=True)
        
        if os.path.exists(pdf_path):
            return pdf_path
        
        return None
    except Exception as e:
        print(f"Office转PDF失败: {e}")
        return None

def generate_pdf_thumbnail(pdf_path, output_dir, max_size=(800, 800)):
    """
    生成PDF封面图
    :param pdf_path: PDF文件路径
    :param output_dir: 输出目录
    :param max_size: 最大尺寸
    :return: 图片文件路径，失败返回None
    """
    try:
        images = convert_from_path(pdf_path, first_page=1)
        if not images:
            return None
        
        img = images[0]
        img.thumbnail(max_size, Image.LANCZOS)
        
        filename = os.path.basename(pdf_path)
        name, _ = os.path.splitext(filename)
        img_filename = f"{name}_thumb.png"
        img_path = os.path.join(output_dir, img_filename)
        
        img.save(img_path, 'PNG')
        
        if os.path.exists(img_path):
            return img_path
        
        return None
    except Exception as e:
        print(f"生成PDF封面图失败: {e}")
        return None

def process_homework_file(file_id, upload_dir):
    """
    处理作业文件：Office转PDF，生成封面图
    :param file_id: 文件ID
    :param upload_dir: 上传目录
    :return: (pdf_file_id, img_file_id)
    """
    pdf_file_id = None
    img_file_id = None
    
    file = File.query.get(file_id)
    if not file:
        return None, None
    
    file_path = file.file_path
    
    if file.is_office_document(file_path):
        pdf_path = convert_office_to_pdf(file_path, upload_dir)
        if pdf_path:
            import uuid
            pdf_filename = os.path.basename(pdf_path)
            pdf_filename = f"{uuid.uuid4()}_{pdf_filename}"
            pdf_final_path = os.path.join(upload_dir, pdf_filename)
            os.rename(pdf_path, pdf_final_path)
            
            pdf_file = File(
                filename=pdf_filename,
                original_filename=f"{os.path.splitext(file.original_filename)[0]}.pdf",
                file_type=File.FILE_TYPE_DOCUMENT,
                file_size=os.path.getsize(pdf_final_path),
                file_path=pdf_final_path,
                mime_type='application/pdf',
                uploader_id=file.uploader_id
            )
            db.session.add(pdf_file)
            db.session.flush()
            pdf_file_id = pdf_file.id
            
            img_path = generate_pdf_thumbnail(pdf_final_path, upload_dir)
            if img_path:
                import uuid
                img_filename = os.path.basename(img_path)
                img_filename = f"{uuid.uuid4()}_{img_filename}"
                img_final_path = os.path.join(upload_dir, img_filename)
                os.rename(img_path, img_final_path)
                
                img_file = File(
                    filename=img_filename,
                    original_filename=img_filename,
                    file_type=File.FILE_TYPE_IMAGE,
                    file_size=os.path.getsize(img_final_path),
                    file_path=img_final_path,
                    mime_type='image/png',
                    uploader_id=file.uploader_id
                )
                db.session.add(img_file)
                db.session.flush()
                img_file_id = img_file.id
            
            file.pdf_file_id = pdf_file_id
            db.session.commit()
    
    return pdf_file_id, img_file_id
