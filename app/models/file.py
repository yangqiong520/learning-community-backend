import os
from libs.db import db
from datetime import datetime

class File(db.Model):
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    mime_type = db.Column(db.String(100), nullable=True)
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    pdf_file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=True)
    image_file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    pdf_file = db.relationship('File', remote_side=[id], foreign_keys=[pdf_file_id], backref='original_files')
    image_file = db.relationship('File', remote_side=[id], foreign_keys=[image_file_id], backref='preview_images')
    
    FILE_TYPE_IMAGE = 'image'
    FILE_TYPE_VIDEO = 'video'
    FILE_TYPE_DOCUMENT = 'document'
    FILE_TYPE_OTHER = 'other'
    
    FILE_TYPE_NAMES = {
        FILE_TYPE_IMAGE: '图片',
        FILE_TYPE_VIDEO: '视频',
        FILE_TYPE_DOCUMENT: '文档',
        FILE_TYPE_OTHER: '其他'
    }
    
    # 文件类型对应的扩展名
    FILE_EXTENSIONS = {
        FILE_TYPE_IMAGE: {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'ico', 'svg'},
        FILE_TYPE_VIDEO: {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm', '3gp'},
        FILE_TYPE_DOCUMENT: {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'rtf', 'md'},
        FILE_TYPE_OTHER: set()  # 空集合，任何未匹配的类型都归为other
    }

    @staticmethod
    def detect_file_type(filename):
        """
        根据文件扩展名自动判断文件类型
        支持的文件类型：
        - 图片：png, jpg, jpeg, gif, bmp, webp, ico, svg
        - 视频：mp4, avi, mov, wmv, flv, mkv, webm, 3gp
        - 文档：pdf, doc, docx, xls, xlsx, ppt, pptx, txt, rtf, md
        - 其他：其他所有文件类型
        """
        if not filename or '.' not in filename:
            return File.FILE_TYPE_OTHER

        ext = os.path.splitext(filename)[1].lower().lstrip('.')

        for file_type, extensions in File.FILE_EXTENSIONS.items():
            if ext in extensions:
                return file_type

        return File.FILE_TYPE_OTHER

    @staticmethod
    def is_office_document(file_path):
        """
        判断是否为Office文档
        """
        office_extensions = ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp']
        ext = os.path.splitext(file_path)[1].lower()
        return ext in office_extensions
    
    def __repr__(self):
        return f'<File {self.original_filename}>'
    
    def to_dict(self):
        result = {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_type_name': self.FILE_TYPE_NAMES.get(self.file_type),
            'file_size': self.file_size,
            'file_path': self.file_path,
            'mime_type': self.mime_type,
            'uploader_id': self.uploader_id,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
        
        # 添加PDF信息（如果有）
        if self.pdf_file_id:
            pdf_file = File.query.get(self.pdf_file_id)
            if pdf_file and pdf_file.is_active:
                result['pdf_file_id'] = pdf_file.id
                result['pdf_url'] = pdf_file.file_path
        
        # 添加预览图片信息（如果有）
        if self.image_file_id:
            image_file = File.query.get(self.image_file_id)
            if image_file and image_file.is_active:
                result['image_file_id'] = image_file.id
                result['image_url'] = f'/api/v2/files/serve-image/{image_file.id}'
        
        return result