import os
import subprocess
import platform
from datetime import datetime
from flask import current_app
import uuid

class OfficeToPDFConverter:
    """Office文档转PDF转换器"""

    def __init__(self):
        self.libreoffice_path = self._find_libreoffice()
        if not self.libreoffice_path:
            current_app.logger.warning("LibreOffice未找到，Office文档转换功能不可用")

    def _find_libreoffice(self):
        """查找LibreOffice可执行文件路径"""
        system = platform.system()

        if system == "Windows":
            # Windows常见安装路径
            possible_paths = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
                r"C:\Program Files\LibreOffice 7\program\soffice.exe",
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
        elif system == "Darwin":  # macOS
            possible_paths = [
                "/Applications/LibreOffice.app/Contents/MacOS/soffice",
                "/Applications/LibreOffice.app/Contents/program/soffice"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
        elif system == "Linux":
            # Linux尝试通过which命令查找
            try:
                result = subprocess.run(['which', 'libreoffice'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                if result.returncode == 0:
                    return result.stdout.strip()
            except:
                pass

        return None

    def convert_to_pdf(self, office_file_path, output_dir):
        """
        将Office文档转换为PDF

        Args:
            office_file_path: Office文档路径
            output_dir: PDF输出目录

        Returns:
            PDF文件路径，失败返回None
        """
        if not self.libreoffice_path:
            current_app.logger.error("LibreOffice未安装，无法转换文档")
            return None

        if not os.path.exists(office_file_path):
            current_app.logger.error(f"源文件不存在: {office_file_path}")
            return None

        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        try:
            # 构建命令
            # --headless: 无头模式
            # --convert-to pdf: 转换为PDF
            # --outdir: 输出目录
            command = [
                self.libreoffice_path,
                '--headless',
                '--convert-to', 'pdf',
                '--outdir', output_dir,
                office_file_path
            ]

            current_app.logger.info(f"开始转换: {office_file_path}")
            current_app.logger.info(f"命令: {' '.join(command)}")

            # 执行转换
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=30  # 30秒超时
            )

            if result.returncode == 0:
                # 转换成功，生成PDF文件名
                original_filename = os.path.basename(office_file_path)
                pdf_filename = os.path.splitext(original_filename)[0] + '.pdf'
                pdf_path = os.path.join(output_dir, pdf_filename)

                if os.path.exists(pdf_path):
                    current_app.logger.info(f"转换成功: {pdf_path}")
                    return pdf_path
                else:
                    current_app.logger.error("转换完成但找不到输出PDF文件")
                    return None
            else:
                current_app.logger.error(f"转换失败: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            current_app.logger.error("转换超时")
            return None
        except Exception as e:
            current_app.logger.error(f"转换异常: {str(e)}")
            return None

    def is_office_document(self, file_path):
        """
        判断是否为Office文档

        Args:
            file_path: 文件路径

        Returns:
            是否为Office文档
        """
        office_extensions = ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp']
        ext = os.path.splitext(file_path)[1].lower()
        return ext in office_extensions
