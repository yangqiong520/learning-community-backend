"""
测试课程自动检测功能
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:5000"
USERNAME = "teacher1"
PASSWORD = "123456"

def login():
    """登录获取 token"""
    url = f"{BASE_URL}/api/v2/auth/login"
    data = {
        "phone": "13800138001",
        "password": PASSWORD
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        result = response.json()
        token = result['data']['token']
        print(f"[OK] 登录成功，Token: {token[:50]}...")
        return token
    else:
        print(f"[ERROR] 登录失败: {response.text}")
        return None

def test_create_homework_with_course_name(token):
    """测试使用课程名称创建作业类型"""
    url = f"{BASE_URL}/api/v2/homeworks/types"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    # 测试1：第一次创建，应该自动创建课程
    print("\n=== 测试1：首次使用课程名称'数字特效' ===")
    data1 = {
        "course_name": "数字特效",
        "name": "平时作业1",
        "content": "这是第一次发布的平时作业，系统应该自动创建课程"
    }
    response1 = requests.post(url, json=data1, headers=headers)
    print(f"响应状态码: {response1.status_code}")
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"[OK] 创建成功")
        print(f"  作业类型ID: {result1['data']['id']}")
        print(f"  课程ID: {result1['data']['course_id']}")
        print(f"  课程名称: {result1['data']['course_name']}")
        course_id_1 = result1['data']['course_id']
    else:
        print(f"[ERROR] 创建失败: {response1.text}")
        return

    # 测试2：第二次使用相同课程名称，应该复用课程
    print("\n=== 测试2：再次使用课程名称'数字特效' ===")
    data2 = {
        "course_name": "数字特效",
        "name": "平时作业2",
        "content": "这是第二次发布的平时作业，系统应该复用已存在的课程"
    }
    response2 = requests.post(url, json=data2, headers=headers)
    print(f"响应状态码: {response2.status_code}")
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"[OK] 创建成功")
        print(f"  作业类型ID: {result2['data']['id']}")
        print(f"  课程ID: {result2['data']['course_id']}")
        print(f"  课程名称: {result2['data']['course_name']}")

        # 验证课程ID是否相同
        if result2['data']['course_id'] == course_id_1:
            print(f"[OK] 课程复用成功！两次使用同一个课程ID: {course_id_1}")
        else:
            print(f"[ERROR] 课程ID不一致！第一次: {course_id_1}, 第二次: {result2['data']['course_id']}")
    else:
        print(f"[ERROR] 创建失败: {response2.text}")

    # 测试3：使用不同的课程名称，应该创建新课程
    print("\n=== 测试3：使用新的课程名称'数字媒体' ===")
    data3 = {
        "course_name": "数字媒体",
        "name": "期末作业",
        "content": "这是新课程的作业类型"
    }
    response3 = requests.post(url, json=data3, headers=headers)
    print(f"响应状态码: {response3.status_code}")
    if response3.status_code == 200:
        result3 = response3.json()
        print(f"[OK] 创建成功")
        print(f"  作业类型ID: {result3['data']['id']}")
        print(f"  课程ID: {result3['data']['course_id']}")
        print(f"  课程名称: {result3['data']['course_name']}")

        # 验证课程ID是否不同
        if result3['data']['course_id'] != course_id_1:
            print(f"[OK] 创建了新课程！新课程ID: {result3['data']['course_id']}")
        else:
            print(f"[ERROR] 课程ID不应该相同！")
    else:
        print(f"[ERROR] 创建失败: {response3.text}")

def test_get_homework_types(token, course_id=None):
    """测试获取作业类型列表"""
    url = f"{BASE_URL}/api/v2/homeworks/types"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {}
    if course_id:
        params['course_id'] = course_id

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        result = response.json()
        print(f"\n=== 获取作业类型列表 ===")
        print(f"[OK] 获取成功，共 {len(result['data'])} 个作业类型")
        for hw in result['data']:
            print(f"  - {hw['name']} (课程: {hw['course_name']})")
    else:
        print(f"[ERROR] 获取失败: {response.text}")

if __name__ == "__main__":
    token = login()
    if token:
        test_create_homework_with_course_name(token)
        print("\n" + "="*60)
        print("测试完成！")
