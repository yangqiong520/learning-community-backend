from app import create_app
from app.models.file import File
import os

app = create_app()

with app.app_context():
    # 检查文件72
    file = File.query.get(72)
    if file:
        print(f'File 72: {file.to_dict()}')
        print(f'文件路径: {file.file_path}')
        print(f'文件存在: {os.path.exists(file.file_path)}')
    else:
        print('File 72: 不存在')
    
    # 检查文件69
    file = File.query.get(69)
    if file:
        print(f'File 69: {file.to_dict()}')
        print(f'文件路径: {file.file_path}')
        print(f'文件存在: {os.path.exists(file.file_path)}')
    else:
        print('File 69: 不存在')
    
    # 检查文件72的image_file_id
    file = File.query.get(72)
    if file and file.image_file_id:
        image = File.query.get(file.image_file_id)
        if image:
            print(f'File 72的预览图: {image.to_dict()}')
            print(f'预览图路径: {image.file_path}')
            print(f'预览图存在: {os.path.exists(image.file_path)}')
    
    # 检查文件69的image_file_id
    file = File.query.get(69)
    if file and file.image_file_id:
        image = File.query.get(file.image_file_id)
        if image:
            print(f'File 69的预览图: {image.to_dict()}')
            print(f'预览图路径: {image.file_path}')
            print(f'预览图存在: {os.path.exists(image.file_path)}')
