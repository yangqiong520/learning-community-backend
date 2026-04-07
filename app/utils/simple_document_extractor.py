"""
简单的PDF和Word文档内容提取
使用最基础可靠的方法
"""

import os
import re


def extract_pdf_content_simple(file_path):
    """
    使用最简单的方法提取PDF内容
    
    Args:
        file_path: PDF文件路径
        
    Returns:
        str: 提取的文本内容
    """
    try:
        import PyPDF2
        
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    # 页面之间添加换行符
                    text += page_text + "\n"
        
        # 清理多余的空行
        text = re.sub(r'\n\n+', '\n\n', text.strip())
        
        return text
        
    except Exception as e:
        print(f"PDF内容提取失败: {e}")
        return f"PDF内容提取失败: {str(e)}"


def extract_word_content_simple(file_path):
    """
    使用最简单的方法提取Word内容
    
    Args:
        file_path: Word文档路径 (.docx格式)
        
    Returns:
        str: 提取的文本内容
    """
    try:
        import zipfile
        import xml.etree.ElementTree as ET
        
        # Word文档实际上是一个ZIP文件
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            # 读取document.xml
            xml_content = zip_ref.read('word/document.xml')
        
        # 解析XML
        root = ET.fromstring(xml_content)
        
        # Word文档的命名空间
        namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        }
        
        texts = []
        
        # 遍历所有段落
        for paragraph in root.findall('.//w:p', namespaces):
            paragraph_text = ""
            
            # 遍历段落中的所有文本元素
            for text_elem in paragraph.findall('.//w:t', namespaces):
                if text_elem.text:
                    paragraph_text += text_elem.text
            
            # 如果段落有内容，添加到结果
            if paragraph_text:
                texts.append(paragraph_text)
        
        # 段落之间添加换行
        full_text = '\n\n'.join(texts)
        
        # 清理多余的空行
        full_text = re.sub(r'\n\n+', '\n\n', full_text.strip())
        
        return full_text
        
    except Exception as e:
        print(f"Word内容提取失败: {e}")
        return f"Word内容提取失败: {str(e)}"


def extract_document_content_simple(file_path, file_extension=None):
    """
    使用最简单的方法自动识别文档类型并提取内容
    
    Args:
        file_path: 文档文件路径
        file_extension: 文件扩展名（可选，会自动识别）
        
    Returns:
        str: 提取的文本内容，或错误消息
    """
    if not file_extension:
        # 从文件路径自动识别扩展名
        file_extension = os.path.splitext(file_path)[1].lower()
    
    print(f"开始提取文档内容: {file_path} (扩展名: {file_extension})")
    
    # 根据文件类型调用相应的提取函数
    if file_extension == '.pdf':
        content = extract_pdf_content_simple(file_path)
    elif file_extension in ['.docx', '.doc']:
        # 注意：.doc格式需要额外库，目前只支持.docx
        if file_extension == '.doc':
            return "暂不支持.doc格式，请使用.docx格式"
        content = extract_word_content_simple(file_path)
    else:
        return f"不支持的文档格式: {file_extension}"
    
    # 验证提取的内容
    if content and not content.startswith("失败") and not content.startswith("暂不支持"):
        print(f"文档内容提取成功: {len(content)} 字符")
        print(f"包含换行符数量: {content.count(chr(10))}")
    else:
        print(f"文档内容提取失败: {content}")
    
    return content


def is_supported_document(file_path):
    """
    检查文件是否为支持的文档格式
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 是否为支持的文档格式
    """
    if not file_path:
        return False
        
    file_extension = os.path.splitext(file_path)[1].lower()
    supported_extensions = ['.pdf', '.docx']
    
    return file_extension in supported_extensions
