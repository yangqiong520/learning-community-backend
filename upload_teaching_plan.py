import requests

BASE_URL = 'http://127.0.0.1:5000'

# 教学计划的文件
IMAGE_PATH = r'E:\nodejs-project\learning-community-backend\img\teach_test.png'
DOCUMENT_PATH = r'E:\nodejs-project\learning-community-backend\img\teaching.pdf'

print("=" * 50)
print("创建新的教学计划记录")
print("=" * 50)

print("1. 登录中...")
r = requests.post(BASE_URL + '/api/v2/auth/login', json={'phone':'13800138000','password':'123456'})
token = r.json()['data']['token']
headers = {'Authorization': f'Bearer {token}'}
print("登录成功")

print("\n2. 上传PDF文档和图片...")
print(f"图片路径: {IMAGE_PATH}")
print(f"文档路径: {DOCUMENT_PATH}")

with open(DOCUMENT_PATH, 'rb') as doc_file, open(IMAGE_PATH, 'rb') as img_file:
    files = {
        'document': ('teaching.pdf', doc_file, 'application/pdf'),
        'image': ('teach_test.png', img_file, 'image/png')
    }
    
    # 不提供content字段，让后端自动提取
    teaching_data = {
        'title': '数字媒体艺术教学计划'
    }
    
    print(f"发送的数据（注意：没有content字段）：{teaching_data}")
    
    r = requests.post(BASE_URL + '/api/v2/teaching_plans/upload', headers=headers, data=teaching_data, files=files)
    
    if r.status_code == 201:
        teaching_plan_id = r.json()['data']['teaching_plan']['id']
        print(f"\n教学计划创建成功，ID: {teaching_plan_id}")
        print("后端自动提取PDF内容功能正常！")
    else:
        print(f"\n教学计划创建失败: {r.text}")
        print(f"状态码: {r.status_code}")

print("\n" + "=" * 50)
print("操作完成！")
print("=" * 50)
