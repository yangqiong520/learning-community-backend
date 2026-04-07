import requests

BASE_URL = 'http://127.0.0.1:5000'

# 使用PDF文档创建制度记录
DOCUMENT_PATH = r'E:\nodejs-project\learning-community-backend\img\traning_two.pdf'
IMAGE_PATH = r'E:\nodejs-project\learning-community-backend\img\traning_test.png'

print("=" * 50)
print("创建新的制度记录（使用PDF文档）")
print("=" * 50)

print("1. 登录中...")
r = requests.post(BASE_URL + '/api/v2/auth/login', json={'phone':'13800138000','password':'123456'})
token = r.json()['data']['token']
headers = {'Authorization': f'Bearer {token}'}
print("登录成功")

print("\n2. 上传PDF文档和图片（后端自动提取内容）...")
with open(DOCUMENT_PATH, 'rb') as doc_file, open(IMAGE_PATH, 'rb') as img_file:
    files = {
        'document': ('traning_two.pdf', doc_file, 'application/pdf'),
        'image': ('traning_test.png', img_file, 'image/png')
    }
    
    # 不提供content字段，让后端自动提取
    regulation_data = {
        'title': '数字媒体艺术平面设计师的培养方案（制度表）'
    }
    
    print(f"发送的数据（注意：没有content字段）：{regulation_data}")
    print(f"文档：{DOCUMENT_PATH}")
    print(f"图片：{IMAGE_PATH}")
    
    r = requests.post(BASE_URL + '/api/v2/regulations/upload', headers=headers, data=regulation_data, files=files)
    
    if r.status_code == 201:
        regulation_id = r.json()['data']['regulation']['id']
        print(f"\n制度创建成功，ID: {regulation_id}")
        print("后端自动提取PDF内容功能正常！")
    else:
        print(f"\n制度创建失败: {r.text}")
        print(f"状态码: {r.status_code}")

print("\n" + "=" * 50)
print("操作完成！")
print("=" * 50)
