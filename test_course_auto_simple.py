"""
测试课程自动检测功能（简化版）
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:5000"

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
    print(f"响应内容: {json.dumps(response1.json(), ensure_ascii=False, indent=2)}")

    if response1.status_code == 200:
        result1 = response1.json()
        print(f"[OK] 创建成功")
        print(f"  作业类型ID: {result1['data']['id']}")
        print(f"  课程ID: {result1['data']['course_id']}")
        print(f"  课程名称: {result1['data']['course_name']}")
        course_id_1 = result1['data']['course_id']
    else:
        print(f"[ERROR] 创建失败")
        return None

    # 测试2：第二次使用相同课程名称，应该复用课程
    print("\n=== 测试2：再次使用课程名称'数字特效' ===")
    data2 = {
        "course_name": "数字特效",
        "name": "平时作业2",
        "content": "这是第二次发布的平时作业，系统应该复用已存在的课程"
    }
    response2 = requests.post(url, json=data2, headers=headers)
    print(f"响应状态码: {response2.status_code}")
    print(f"响应内容: {json.dumps(response2.json(), ensure_ascii=False, indent=2)}")

    if response2.status_code == 200:
        result2 = response2.json()
        print(f"[OK] 创建成功")
        print(f"  作业类型ID: {result2['data']['id']}")
        print(f"  课程ID: {result2['data']['course_id']}")
        print(f"  课程名称: {result2['data']['course_name']}")

        # 验证课程ID是否相同
        if result2['data']['course_id'] == course_id_1:
            print(f"[OK] 课程复用成功！两次使用同一个课程ID: {course_id_1}")
            return course_id_1
        else:
            print(f"[ERROR] 课程ID不一致！第一次: {course_id_1}, 第二次: {result2['data']['course_id']}")
            return None
    else:
        print(f"[ERROR] 创建失败")
        return None

def test_with_course_id(token, course_id):
    """测试使用课程ID创建作业类型"""
    url = f"{BASE_URL}/api/v2/homeworks/types"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    print("\n=== 测试3：使用课程ID创建作业类型 ===")
    data = {
        "course_id": course_id,
        "name": "平时作业3",
        "content": "这是使用课程ID创建的作业"
    }
    response = requests.post(url, json=data, headers=headers)
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")

    if response.status_code == 200:
        print(f"[OK] 使用课程ID创建成功")
    else:
        print(f"[ERROR] 创建失败")

if __name__ == "__main__":
    print("=" * 60)
    print("课程自动检测功能测试")
    print("=" * 60)

    # 提示用户输入 token
    print("\n请先登录获取 JWT Token:")
    print("1. 访问 http://localhost:5000/api/v2/auth/login")
    print("2. 使用以下账号登录:")
    print("   - 手机号: (您的手机号)")
    print("   - 密码: (您的密码)")
    print("3. 复制返回的 token")

    token = input("\n请输入您的 JWT Token: ").strip()

    if not token:
        print("[ERROR] Token 不能为空")
        exit(1)

    # 运行测试
    course_id = test_create_homework_with_course_name(token)

    if course_id:
        test_with_course_id(token, course_id)

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
