import pymysql

try:
    # 测试连接
    conn = pymysql.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='123456',
        database='learning_community'
    )
    print("MySQL连接成功！")
    
    # 查询数据库版本
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()
    print(f"MySQL版本: {version[0]}")
    
    # 检查表
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"\n数据库中的表:")
    for table in tables:
        print(f"  - {table[0]}")
    
    conn.close()
    
except Exception as e:
    print(f"连接失败: {e}")
    print(f"\n错误类型: {type(e).__name__}")
    print(f"错误详情: {str(e)}")
