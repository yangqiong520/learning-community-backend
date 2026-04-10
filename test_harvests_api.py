import requests
import json

BASE_URL = "http://127.0.0.1:5000/api/v2"

def test_harvests_api():
    print("=" * 60)
    print("Start testing Harvest API")
    print("=" * 60)
    
    token = None
    
    try:
        print("\n1. Login to get token...")
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "phone": "17326500773",
                "password": "123456"
            }
        )
        
        print(f"Status code: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get('data', {}).get('token')
            print(f"[OK] Login success, got token: {token[:20]}...")
        else:
            print(f"[FAIL] Login failed: {login_response.text}")
            return
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        print("\n2. 测试获取收获列表（空列表）...")
        list_response = requests.get(
            f"{BASE_URL}/harvests?page=1&per_page=12",
            headers=headers
        )
        print(f"状态码: {list_response.status_code}")
        print(f"响应: {json.dumps(list_response.json(), ensure_ascii=False, indent=2)}")
        
        print("\n3. 测试创建收获...")
        create_response = requests.post(
            f"{BASE_URL}/harvests",
            headers=headers,
            json={
                "title": "测试收获标题",
                "content": "这是一条测试的收获内容，通过这周的学习，我深刻理解了数据库设计的重要性。SQL优化、索引设计等知识让我受益匪浅。"
            }
        )
        print(f"状态码: {create_response.status_code}")
        print(f"响应: {json.dumps(create_response.json(), ensure_ascii=False, indent=2)}")
        
        if create_response.status_code == 201:
            harvest_id = create_response.json().get('data', {}).get('harvest', {}).get('id')
            print(f"[OK] Create success, harvest ID: {harvest_id}")
            
            print(f"\n4. 测试获取收获列表（有数据）...")
            list_response2 = requests.get(
                f"{BASE_URL}/harvests?page=1&per_page=12",
                headers=headers
            )
            print(f"状态码: {list_response2.status_code}")
            print(f"响应: {json.dumps(list_response2.json(), ensure_ascii=False, indent=2)}")
            
            print(f"\n5. 测试获取收获详情...")
            detail_response = requests.get(
                f"{BASE_URL}/harvests/{harvest_id}",
                headers=headers
            )
            print(f"状态码: {detail_response.status_code}")
            print(f"响应: {json.dumps(detail_response.json(), ensure_ascii=False, indent=2)}")
            
            print(f"\n6. 测试删除收获...")
            delete_response = requests.delete(
                f"{BASE_URL}/harvests/{harvest_id}",
                headers=headers
            )
            print(f"状态码: {delete_response.status_code}")
            print(f"响应: {json.dumps(delete_response.json(), ensure_ascii=False, indent=2)}")
            
            print(f"\n7. 测试获取收获列表（删除后）...")
            list_response3 = requests.get(
                f"{BASE_URL}/harvests?page=1&per_page=12",
                headers=headers
            )
            print(f"状态码: {list_response3.status_code}")
            print(f"响应: {json.dumps(list_response3.json(), ensure_ascii=False, indent=2)}")
            
            print("\n8. 测试参数验证 - 标题为空...")
            invalid_response1 = requests.post(
                f"{BASE_URL}/harvests",
                headers=headers,
                json={
                    "title": "",
                    "content": "测试内容"
                }
            )
            print(f"状态码: {invalid_response1.status_code}")
            print(f"响应: {json.dumps(invalid_response1.json(), ensure_ascii=False, indent=2)}")
            
            print("\n9. 测试参数验证 - 内容为空...")
            invalid_response2 = requests.post(
                f"{BASE_URL}/harvests",
                headers=headers,
                json={
                    "title": "测试标题",
                    "content": ""
                }
            )
            print(f"状态码: {invalid_response2.status_code}")
            print(f"响应: {json.dumps(invalid_response2.json(), ensure_ascii=False, indent=2)}")
            
            print("\n10. 测试参数验证 - 标题超过255字符...")
            invalid_response3 = requests.post(
                f"{BASE_URL}/harvests",
                headers=headers,
                json={
                    "title": "x" * 256,
                    "content": "测试内容"
                }
            )
            print(f"状态码: {invalid_response3.status_code}")
            print(f"响应: {json.dumps(invalid_response3.json(), ensure_ascii=False, indent=2)}")
            
            print("\n11. 测试参数验证 - 内容超过50000字符...")
            invalid_response4 = requests.post(
                f"{BASE_URL}/harvests",
                headers=headers,
                json={
                    "title": "测试标题",
                    "content": "x" * 50001
                }
            )
            print(f"状态码: {invalid_response4.status_code}")
            print(f"响应: {json.dumps(invalid_response4.json(), ensure_ascii=False, indent=2)}")
        
            print("\n" + "=" * 60)
            print("Test completed!")
            print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_harvests_api()
