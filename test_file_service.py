"""
测试文件服务是否正常工作
"""
import requests
import json

# 测试基础URL
base_url = "http://localhost:5000"

# 测试health端点
print("1. 测试健康检查端点...")
try:
    response = requests.get(f"{base_url}/health")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")
except Exception as e:
    print(f"   错误: {e}")

print("\n2. 测试文件服务路由（无认证，应该失败）...")
try:
    response = requests.get(f"{base_url}/api/v2/files/serve/72")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.text[:200]}")
except Exception as e:
    print(f"   错误: {e}")

print("\n3. 测试文件信息端点（无认证，应该失败）...")
try:
    response = requests.get(f"{base_url}/api/v2/files/72")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.text[:200]}")
except Exception as e:
    print(f"   错误: {e}")

print("\n4. 测试认证登录...")
try:
    # 尝试用手机号登录
    response = requests.post(
        f"{base_url}/api/v2/auth/login",
        json={
            "phone": "13800138000",
            "password": "admin123"
        }
    )
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        token = data.get('data', {}).get('token')
        print(f"   获取到Token: {token[:50]}..." if token else "   未获取到Token")
        
        if token:
            print("\n5. 使用Token测试文件信息端点...")
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{base_url}/api/v2/files/72", headers=headers)
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   文件信息: {json.dumps(data.get('data', {}), indent=2, ensure_ascii=False)}")
            else:
                print(f"   响应: {response.text}")
            
            print("\n6. 使用Token测试文件服务端点...")
            response = requests.get(f"{base_url}/api/v2/files/serve/72", headers=headers)
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                print(f"   文件类型: {response.headers.get('Content-Type')}")
                print(f"   文件大小: {len(response.content)} bytes")
            else:
                print(f"   响应: {response.text}")
    else:
        print(f"   响应: {response.text}")
except Exception as e:
    print(f"   错误: {e}")
