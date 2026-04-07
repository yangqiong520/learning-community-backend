import requests
import time

BASE_URL = 'http://127.0.0.1:5000'

# 登录获取token
def login():
    response = requests.post(f'{BASE_URL}/api/v2/auth/login', json={
        'phone': '13800138000',
        'password': '123456'
    })
    data = response.json()
    if data['code'] == 200:
        return data['data']['token']
    else:
        raise Exception(f"Login failed: {data['message']}")

# 测试上传Office文档
def test_upload_office_document(token):
    print("\n" + "="*50)
    print("Testing Office document upload with auto-conversion")
    print("="*50)
    
    test_file_path = 'E:\\nodejs-project\\learning-community-backend\\img\\test_all.docx'
    
    if not os.path.exists(test_file_path):
        print(f"Test file not found: {test_file_path}")
        return None
    
    print(f"Uploading: {test_file_path}")
    start_time = time.time()
    
    with open(test_file_path, 'rb') as f:
        files = {'file': ('test_all.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.post(f'{BASE_URL}/api/v2/files/upload', files=files, headers=headers)
    
    upload_time = time.time() - start_time
    print(f"Upload completed in {upload_time:.2f} seconds")
    
    data = response.json()
    if data['code'] == 201:
        file_data = data['data']['file']
        print(f"[OK] File uploaded successfully!")
        print(f"File ID: {file_data['id']}")
        print(f"Original filename: {file_data['original_filename']}")
        print(f"File type: {file_data['file_type']}")
        
        if 'pdf_file_id' in file_data:
            print(f"PDF file ID: {file_data['pdf_file_id']}")
            print(f"PDF URL: {file_data.get('pdf_url')}")
        else:
            print("[WARNING] No PDF file ID in response")
        
        return file_data['id']
    else:
        print(f"[ERROR] Upload failed: {data['message']}")
        return None

# 测试预览接口
def test_preview(token, file_id):
    print("\n" + "="*50)
    print("Testing preview endpoint")
    print("="*50)
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{BASE_URL}/api/v2/files/{file_id}/preview', headers=headers)
    
    data = response.json()
    if data['code'] == 200:
        preview_data = data['data']
        print(f"[OK] Preview URL retrieved successfully!")
        print(f"File ID: {preview_data['file_id']}")
        print(f"Preview type: {preview_data['preview_type']}")
        print(f"Preview URL: {preview_data['preview_url']}")
        
        # 测试PDF是否可访问
        print("\nTesting PDF accessibility...")
        pdf_response = requests.get(preview_data['preview_url'])
        if pdf_response.status_code == 200:
            print(f"[OK] PDF is accessible")
            print(f"PDF content length: {len(pdf_response.content)} bytes")
        else:
            print(f"[ERROR] PDF not accessible (Status: {pdf_response.status_code})")
    else:
        print(f"[ERROR] Preview failed: {data['message']}")

# 测试手动转换接口（deprecated）
def test_manual_conversion(token, file_id):
    print("\n" + "="*50)
    print("Testing manual conversion endpoint (deprecated)")
    print("="*50)
    
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.post(f'{BASE_URL}/api/v2/files/{file_id}/convert-to-pdf', headers=headers)
    
    print(f"Response headers: {response.headers}")
    
    data = response.json()
    if data['code'] == 200:
        print(f"[OK] Manual conversion successful")
        print(f"PDF file ID: {data['data']['pdf_file_id']}")
        print(f"PDF URL: {data['data']['pdf_url']}")
    else:
        print(f"[INFO] Manual conversion: {data['message']}")

if __name__ == '__main__':
    import os
    
    try:
        # 登录
        print("Logging in...")
        token = login()
        print(f"[OK] Login successful, token: {token[:20]}...")
        
        # 测试上传Office文档
        file_id = test_upload_office_document(token)
        
        if file_id:
            # 等待一段时间确保转换完成
            print("\nWaiting 5 seconds for conversion to complete...")
            time.sleep(5)
            
            # 测试预览
            test_preview(token, file_id)
            
            # 测试手动转换接口
            test_manual_conversion(token, file_id)
        
        print("\n" + "="*50)
        print("All tests completed!")
        print("="*50)
        
    except Exception as e:
        print(f"[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
