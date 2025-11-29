"""
Pixiv API Server 测试脚本
"""
import requests

BASE_URL = "http://localhost:6523"
AUTH_TOKEN = "Adm1n_PixivPY3"

headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

def test_health():
    """测试健康检查"""
    print("\n=== 健康检查 ===")
    r = requests.get(f"{BASE_URL}/health")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
    return r.status_code == 200

def test_pool_status():
    """测试账号池状态"""
    print("\n=== 账号池状态 ===")
    r = requests.get(f"{BASE_URL}/api/pool/status", headers=headers)
    print(f"Status: {r.status_code}")
    data = r.json()
    print(f"Strategy: {data.get('strategy')}")
    print(f"Accounts: {len(data.get('accounts', []))}")
    for acc in data.get('accounts', []):
        print(f"  - {acc['name']}: {'Active' if acc['authenticated'] else 'Inactive'}, requests: {acc['request_count']}")
    return r.status_code == 200

def test_proxy_status():
    """测试代理状态"""
    print("\n=== 代理状态 ===")
    r = requests.get(f"{BASE_URL}/api/proxy/status", headers=headers)
    print(f"Status: {r.status_code}")
    data = r.json()
    print(f"Enabled: {data.get('enabled')}")
    print(f"HTTP: {data.get('http')}")
    return r.status_code == 200

def test_ranking():
    """测试获取排行榜"""
    print("\n=== 排行榜 (前3) ===")
    r = requests.get(f"{BASE_URL}/api/ranking?mode=day", headers=headers)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Account used: {data.get('_account')}")
        for i, illust in enumerate(data.get('illusts', [])[:3]):
            print(f"  {i+1}. {illust['title']} - {illust['user']['name']}")
    else:
        print(f"Error: {r.json()}")
    return r.status_code == 200


def test_search():
    """测试搜索"""
    print("\n=== 搜索 '原神' (前3) ===")
    r = requests.get(f"{BASE_URL}/api/search?word=原神", headers=headers)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Account used: {data.get('_account')}")
        for i, illust in enumerate(data.get('illusts', [])[:3]):
            print(f"  {i+1}. {illust['title']} - {illust['user']['name']}")
    else:
        print(f"Error: {r.json()}")
    return r.status_code == 200

def test_illust_detail():
    """测试获取插画详情"""
    print("\n=== 插画详情 ===")
    # 使用一个已知的插画ID
    illust_id = 137915162
    r = requests.get(f"{BASE_URL}/api/illust/{illust_id}", headers=headers)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        illust = data.get('illust', {})
        print(f"Title: {illust.get('title')}")
        print(f"Author: {illust.get('user', {}).get('name')}")
        print(f"Views: {illust.get('total_view')}")
        print(f"Bookmarks: {illust.get('total_bookmarks')}")
    else:
        print(f"Error: {r.json()}")
    return r.status_code == 200

def test_set_proxy():
    """测试设置代理"""
    print("\n=== 设置代理 ===")
    r = requests.post(f"{BASE_URL}/api/proxy/set", headers=headers, json={
        "enabled": True,
        "http": "http://127.0.0.1:7890"
    })
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
    return r.status_code == 200

def test_add_account_token():
    """测试添加账号 (refresh_token)"""
    print("\n=== 添加账号 (需要有效token) ===")
    # 这里需要替换为有效的 refresh_token
    token = "your_refresh_token_here"
    r = requests.post(f"{BASE_URL}/api/pool/add", headers=headers, json={
        "name": "test_account",
        "refresh_token": token
    })
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
    return r.status_code == 200

def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("Pixiv API Server 测试")
    print("=" * 50)
    
    results = []
    
    # 基础测试
    results.append(("健康检查", test_health()))
    results.append(("账号池状态", test_pool_status()))
    results.append(("代理状态", test_proxy_status()))
    
    # API 测试 (需要有账号)
    results.append(("排行榜", test_ranking()))
    results.append(("搜索", test_search()))
    results.append(("插画详情", test_illust_detail()))
    
    # 打印结果
    print("\n" + "=" * 50)
    print("测试结果")
    print("=" * 50)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {name}")
    
    passed_count = sum(1 for _, p in results if p)
    print(f"\n总计: {passed_count}/{len(results)} 通过")

if __name__ == "__main__":
    run_all_tests()
