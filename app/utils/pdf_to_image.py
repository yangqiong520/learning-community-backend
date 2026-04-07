import os
import platform
import subprocess
from flask import current_app
import uuid

class PDFToImageConverter:
    """PDF转图片转换器（用于生成预览图）"""
    
    def __init__(self):
        self.imagick_path = self._find_imagemagick()
        if not self.imagick_path:
            current_app.logger.warning("ImageMagick未找到，PDF转图片功能不可用")
    
    def _find_imagemagick(self):
        """查找ImageMagick可执行文件路径"""
        system = platform.system()
        
        if system == "Windows":
            # Windows常见安装路径
            possible_paths = [
                r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe",
                r"C:\Program Files\ImageMagick-7.1.0-Q16-HDRI\magick.exe",
                r"C:\Program Files\ImageMagick-7.0.10-Q16-HDRI\magick.exe",
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    return path
            
            # 也尝试使用 which 查找
            try:
                result = subprocess.run(['where', 'magick'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                if result.returncode == 0:
                    return result.stdout.strip().split('\n')[0]
            except:
                pass
                
        elif system == "Darwin":  # macOS
            try:
                result = subprocess.run(['which', 'convert'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                if result.returncode == 0:
                    return result.stdout.strip()
            except:
                pass
        elif system == "Linux":
            try:
                result = subprocess.run(['which', 'convert'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                if result.returncode == 0:
                    return result.stdout.strip()
            except:
                pass
        
        return None
    
    def pdf_to_image(self, pdf_path, output_dir, page_num=1):
        """
        将PDF转换为图片（默认第一页）
        
        Args:
            pdf_path: PDF文件路径
            output_dir: 图片输出目录
            page_num: 要转换的页码，默认为1（第一页）
        
        Returns:
            图片文件路径，失败返回None
        """
        if not self.imagick_path:
            current_app.logger.error("ImageMagick未安装，无法转换PDF为图片")
            return None
        
        if not os.path.exists(pdf_path):
            current_app.logger.error(f"PDF文件不存在: {pdf_path}")
            return None
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        try:
            # 构建命令
            # convert: ImageMagick命令
            # -density 300: 设置DPI为300（提高质量）
            # -quality 90: 设置JPEG质量
            # [0]: 只处理第一页
            image_filename = f"{uuid.uuid4().hex}.jpg"
            image_path = os.path.join(output_dir, image_filename)
            
            command = [
                self.imagick_path,
                '-density', '300',
                '-quality', '90',
                f'{pdf_path}[{page_num - 1}]',  # ImageMagick页码从0开始
                image_path
            ]
            
            current_app.logger.info(f"开始转换PDF为图片: {pdf_path}")
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
                if os.path.exists(image_path):
                    current_app.logger.info(f"转换成功: {image_path}")
                    return image_path
                else:
                    current_app.logger.error("转换完成但找不到输出图片文件")
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
    
    def pdf_to_thumbnail(self, pdf_path, output_dir, width=400, height=300):
        """
        将PDF转换为缩略图
        
        Args:
            pdf_path: PDF文件路径
            output_dir: 图片输出目录
            width: 缩略图宽度
            height: 缩略图高度
        
        Returns:
            缩略图文件路径，失败返回None
        """
        if not self.imagick_path:
            current_app.logger.error("ImageMagick未安装，无法转换PDF为缩略图")
            return None
        
        if not os.path.exists(pdf_path):
            current_app.logger.error(f"PDF文件不存在: {pdf_path}")
            return None
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        try:
            # 构建命令
            thumbnail_filename = f"{uuid.uuid4().hex}_thumb.jpg"
            thumbnail_path = os.path.join(output_dir, thumbnail_filename)
            
            # 使用更简单的命令格式
            # 先设置density为72（标准屏幕密度）
            # 使用白色背景
            command = [
                self.imagick_path,
                '-density', '72',
                f'{pdf_path}[0]',
                '-background', 'white',
                '-flatten',
                '-thumbnail', f'{width}x{height}',
                '-quality', '85',
                thumbnail_path
            ]
            
            current_app.logger.info(f"开始转换PDF为缩略图: {pdf_path}")
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
                if os.path.exists(thumbnail_path):
                    # 检查文件大小，如果太小说明转换失败
                    file_size = os.path.getsize(thumbnail_path)
                    if file_size < 1000:  # 小于1KB可能有问题
                        current_app.logger.warning(f"生成的图片文件太小 ({file_size} bytes)，可能转换失败")
                        # 尝试使用备用方法
                        return self._pdf_to_thumbnail_fallback(pdf_path, output_dir, width, height)
                    
                    current_app.logger.info(f"缩略图转换成功: {thumbnail_path}, 大小: {file_size} bytes")
                    return thumbnail_path
                else:
                    current_app.logger.error("转换完成但找不到输出缩略图文件")
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
    
    def _pdf_to_thumbnail_fallback(self, pdf_path, output_dir, width=400, height=300):
        """
        备用方法：使用Ghostscript直接转换
        """
        import platform
        
        try:
            # 查找Ghostscript可执行文件
            gs_cmd = 'gswin64c.exe' if platform.system() == 'Windows' else 'gs'
            
            thumbnail_filename = f"{uuid.uuid4().hex}_fallback.jpg"
            thumbnail_path = os.path.join(output_dir, thumbnail_filename)
            
            # Ghostscript命令
            command = [
                gs_cmd,
                '-dNOPAUSE',
                '-dBATCH',
                '-dQUIET',
                '-dFirstPage=1',
                '-dLastPage=1',
                '-r72',
                f'-sDEVICE=jpeg',
                f'-sOutputFile={thumbnail_path}',
                pdf_path
            ]
            
            current_app.logger.info(f"使用Ghostscript转换: {' '.join(command)}")
            
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=30
            )
            
            if result.returncode == 0 and os.path.exists(thumbnail_path):
                # 调整大小
                resize_cmd = [
                    self.imagick_path,
                    thumbnail_path,
                    '-thumbnail', f'{width}x{height}',
                    thumbnail_path
                ]
                subprocess.run(resize_cmd, timeout=10)
                
                current_app.logger.info(f"备用方法转换成功: {thumbnail_path}")
                return thumbnail_path
            
            return None
        
        except Exception as e:
            current_app.logger.error(f"备用方法失败: {str(e)}")
            return None
