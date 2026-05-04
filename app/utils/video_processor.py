import os
import cv2
import uuid
from flask import current_app


class VideoProcessor:
    """视频处理器：提取缩略图和获取时长"""

    def __init__(self):
        pass

    def extract_thumbnail(self, video_path, output_dir, timestamp=0):
        """
        从视频中提取一帧作为缩略图

        Args:
            video_path: 视频文件路径
            output_dir: 缩略图输出目录
            timestamp: 提取的时间点（秒），默认为0（第一帧）

        Returns:
            缩略图文件路径，失败返回None
        """
        if not os.path.exists(video_path):
            current_app.logger.error(f"视频文件不存在: {video_path}")
            return None

        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        try:
            video = cv2.VideoCapture(video_path)

            if not video.isOpened():
                current_app.logger.error(f"无法打开视频文件: {video_path}")
                return None

            video.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)

            success, frame = video.read()

            if not success:
                current_app.logger.error(f"无法读取视频帧: {video_path}")
                video.release()
                return None

            thumbnail_filename = f"{uuid.uuid4().hex}_thumb.jpg"
            thumbnail_path = os.path.join(output_dir, thumbnail_filename)

            cv2.imwrite(thumbnail_path, frame)
            video.release()

            if os.path.exists(thumbnail_path):
                current_app.logger.info(f"缩略图提取成功: {thumbnail_path}")
                return thumbnail_path
            else:
                current_app.logger.error("缩略图文件未生成")
                return None

        except Exception as e:
            current_app.logger.error(f"提取缩略图异常: {str(e)}")
            return None

    def get_video_duration(self, video_path):
        """
        获取视频时长（秒）

        Args:
            video_path: 视频文件路径

        Returns:
            视频时长（秒），失败返回0
        """
        if not os.path.exists(video_path):
            current_app.logger.error(f"视频文件不存在: {video_path}")
            return 0

        try:
            video = cv2.VideoCapture(video_path)

            if not video.isOpened():
                current_app.logger.error(f"无法打开视频文件: {video_path}")
                return 0

            fps = video.get(cv2.CAP_PROP_FPS)
            frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

            video.release()

            if fps > 0:
                duration = frame_count / fps
                current_app.logger.info(f"视频时长: {duration:.2f}秒")
                return int(duration)
            else:
                current_app.logger.warning(f"视频FPS为0，无法计算时长")
                return 0

        except Exception as e:
            current_app.logger.error(f"获取视频时长异常: {str(e)}")
            return 0

    @staticmethod
    def format_duration(seconds):
        """
        格式化时长为 HH:MM:SS 格式

        Args:
            seconds: 秒数

        Returns:
            格式化后的时长字符串，如 "00:15:26"
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f'{hours:02d}:{minutes:02d}:{secs:02d}'

    @staticmethod
    def format_play_count(count):
        """
        格式化播放数，超过1万显示为"X万"

        Args:
            count: 播放次数

        Returns:
            格式化后的播放数，如 "1.2万"
        """
        if count >= 10000:
            return f'{count / 10000:.1f}万'
        return str(count)

    def is_valid_video(self, video_path):
        """
        验证视频文件是否有效

        Args:
            video_path: 视频文件路径

        Returns:
            是否为有效视频
        """
        if not os.path.exists(video_path):
            current_app.logger.error(f"视频文件不存在: {video_path}")
            return False

        try:
            video = cv2.VideoCapture(video_path)

            if not video.isOpened():
                current_app.logger.error(f"无法打开视频文件: {video_path}")
                return False

            success, frame = video.read()
            video.release()

            return success

        except Exception as e:
            current_app.logger.error(f"验证视频文件异常: {str(e)}")
            return False
