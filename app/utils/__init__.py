"""
utils包初始化文件
"""

from app.utils.document_extractor import (
    extract_pdf_content,
    extract_word_content, 
    extract_document_content,
    is_supported_document
)

__all__ = [
    'extract_pdf_content',
    'extract_word_content',
    'extract_document_content',
    'is_supported_document'
]
