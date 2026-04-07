import pymysql

try:
    conn = pymysql.connect(
        host='127.0.0.1',
        port=3306,
        user='root',
        password='123456',
        database='learning_community'
    )
    
    cursor = conn.cursor()
    
    # 查询教学计划数据
    cursor.execute("SELECT id, title, created_at, is_active FROM teaching_plans ORDER BY id DESC LIMIT 5")
    plans = cursor.fetchall()
    
    print("教学计划表中的数据（最新5条）：")
    for plan in plans:
        print(f"ID: {plan[0]}, 标题: {plan[1]}, 时间: {plan[2]}, 状态: {plan[3]}")
    
    cursor.close()
    
except Exception as e:
    print(f"查询失败: {e}")
