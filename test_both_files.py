"""
测试文件69和72是否都能正常服务
"""
import requests

base_url = "http://localhost:5000"

# 登录获取Token
print("登录获取Token...")
response = requests.post(
    f"{base_url}/api/v2/auth/login",
    json={
        "phone": "13800138000",
        "password": "admin123"
    }
)

if response.status_code == 200:
    token = response.json().get('data', {}).get('token')
    headers = {"Authorization": f"Bearer {token}"}
    
    # 测试文件72
    print("\n测试文件72...")
    response = requests.get(f"{base_url}/api/v2/files/serve/72", headers=headers)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print(f"文件类型: {response.headers.get('Content-Type')}")
        print(f"文件大小: {len(response.content)} bytes")
        print("[OK] 文件72服务正常")
    else:
        print(f"[FAIL] 文件72服务失败: {response.text}")
    
    # 测试文件69
    print("\n测试文件69...")
    response = requests.get(f"{base_url}/api/v2/files/serve/69", headers=headers)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print(f"文件类型: {response.headers.get('Content-Type')}")
        print(f"文件大小: {len(response.content)} bytes")
        print("[OK] 文件69服务正常")
    else:
        print(f"[FAIL] 文件69服务失败: {response.text}")
    
    # 获取文件信息
    print("\n获取文件69的信息...")
    response = requests.get(f"{base_url}/api/v2/files/69", headers=headers)
    if response.status_code == 200:
        data = response.json()
        file_info = data.get('data', {}).get('file', {})
        print(f"文件ID: {file_info.get('id')}")
        print(f"文件名: {file_info.get('original_filename')}")
        print(f"文件类型: {file_info.get('file_type_name')}")
        print(f"文件路径: {file_info.get('file_path')}")
        print(f"预览图ID: {file_info.get('image_file_id')}")
        
        # 如果有预览图，测试预览图
        if file_info.get('image_file_id'):
            print(f"\n测试预览图(ID: {file_info.get('image_file_id')})...")
            response = requests.get(f"{base_url}/api/v2/files/serve/{file_info.get('image_file_id')}", headers=headers)
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                print(f"预览图类型: {response.headers.get('Content-Type')}")
                print(f"预览图大小: {len(response.content)} bytes")
                print("[OK] 预览图服务正常")
            else:
                print(f"[FAIL] 预览图服务失败: {response.text}")
else:
    print(f"[FAIL] 登录失败: {response.text}")
