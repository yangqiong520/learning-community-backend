"""
测试文件服务路由是否正确
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

app = create_app()

with app.app_context():
    # 获取所有路由
    rules = []
    for rule in app.url_map.iter_rules():
        if rule.rule.startswith('/api/v2/files'):
            rules.append({
                'endpoint': rule.endpoint,
                'rule': rule.rule,
                'methods': list(rule.methods)
            })

    print("Files API 路由列表:")
    print("=" * 80)
    for rule in sorted(rules, key=lambda x: x['rule']):
        print(f"路由: {rule['rule']:<50} 方法: {rule['methods']}")
        print(f"      端点: {rule['endpoint']}")
        print()
