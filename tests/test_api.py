"""
Pixiv API Server 测试脚本
适配新版本：Token 用于管理接口，API Key 用于 API 调用

使用前请确保：
1. config.yaml 中已配置 api_keys
2. 修改下方 API_KEY 为你配置的 key 值
"""
import requests

BASE_URL = "http://localhost:6523"

# Token 用于管理接口（账号池、代理、API Key 管理）
AUTH_TOKEN = "Adm1n_PixivPY3"

# API Key 用于 API 调用 - 请修改为你在 config.yaml 中配置的 key
API_KEY = ""

token_headers = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}

api_headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


def test_health():
    """测试健康检查（无需认证）"""
    print("\n=== 健康检查 ===")
    r = requests.get(f"{BASE_URL}/health")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.json()}")
    return r.status_code == 200


def test_pool_status():
    """测试账号池状态（Token 认证）"""
    print("\n=== 账号池状态 ===")
    r = requests.get(f"{BASE_URL}/api/pool/status", headers=token_headers)
    print(f"Status: {r.status_code}")
    data = r.json()
    print(f"Strategy: {data.get('strategy')}")
    print(f"Accounts: {len(data.get('accounts', []))}")
    for acc in data.get('accounts', []):
        status = 'Active' if acc['authenticated'] else 'Inactive'
        print(f"  - {acc['name']}: {status}, requests: {acc['request_count']}")
    return r.status_code == 200


def test_proxy_status():
    """测试代理状态（Token 认证）"""
    print("\n=== 代理状态 ===")
    r = requests.get(f"{BASE_URL}/api/proxy/status", headers=token_headers)
    print(f"Status: {r.status_code}")
    data = r.json()
    print(f"Enabled: {data.get('enabled')}")
    print(f"HTTP: {data.get('http')}")
    return r.status_code == 200


def test_list_keys():
    """测试列出 API Keys（Token 认证）"""
    print("\n=== API Keys 列表 ===")
    r = requests.get(f"{BASE_URL}/api/keys", headers=token_headers)
    print(f"Status: {r.status_code}")
    data = r.json()
    keys = data.get('keys', [])
    print(f"Total keys: {len(keys)}")
    for k in keys:
        print(f"  - {k['name']}: {k['key']} ({k['access_mode']})")
        if k['denied_endpoints']:
            print(f"    denied: {k['denied_endpoints']}")
        if k['allowed_endpoints']:
            print(f"    allowed: {k['allowed_endpoints']}")
    return r.status_code == 200


# ===== API 调用测试（API Key 认证）=====

def test_ranking():
    """测试获取排行榜（API Key 认证）"""
    print("\n=== 排行榜 (前3) ===")
    if not API_KEY:
        print("跳过: API_KEY 未设置")
        return None
    r = requests.get(f"{BASE_URL}/api/ranking?mode=day", headers=api_headers)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Account used: {data.get('_account')}")
        for i, illust in enumerate(data.get('illusts', [])[:3]):
            print(f"  {i+1}. {illust['title']} - {illust['user']['name']}")
    elif r.status_code == 403:
        print("访问被拒绝 (该 key 的 denied_endpoints 包含此端点)")
    else:
        print(f"Error: {r.json()}")
    return r.status_code in (200, 403)


def test_search():
    """测试搜索（API Key 认证）"""
    print("\n=== 搜索 '原神' (前3) ===")
    if not API_KEY:
        print("跳过: API_KEY 未设置")
        return None
    r = requests.get(f"{BASE_URL}/api/search?word=原神", headers=api_headers)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Account used: {data.get('_account')}")
        for i, illust in enumerate(data.get('illusts', [])[:3]):
            print(f"  {i+1}. {illust['title']} - {illust['user']['name']}")
    elif r.status_code == 403:
        print("访问被拒绝 (该 key 的 denied_endpoints 包含此端点)")
    else:
        print(f"Error: {r.json()}")
    return r.status_code in (200, 403)


def test_illust_detail():
    """测试获取插画详情（API Key 认证）"""
    print("\n=== 插画详情 ===")
    if not API_KEY:
        print("跳过: API_KEY 未设置")
        return None
    illust_id = 137915162
    r = requests.get(f"{BASE_URL}/api/illust/{illust_id}", headers=api_headers)
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        illust = data.get('illust', {})
        print(f"Title: {illust.get('title')}")
        print(f"Author: {illust.get('user', {}).get('name')}")
        print(f"Views: {illust.get('total_view')}")
        print(f"Bookmarks: {illust.get('total_bookmarks')}")
    elif r.status_code == 403:
        print("访问被拒绝 (该 key 的 denied_endpoints 包含此端点)")
    else:
        print(f"Error: {r.json()}")
    return r.status_code in (200, 403)


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("Pixiv API Server 测试")
    print("=" * 50)
    
    if not API_KEY:
        print("\n警告: API_KEY 未设置!")
        print("请修改 tests/test_api.py 中的 API_KEY 变量")
        print("设置为你在 config.yaml 中配置的 key 值\n")
    
    results = []
    
    # 基础测试（无需认证）
    results.append(("健康检查", test_health()))
    
    # 管理接口测试（Token 认证）
    results.append(("账号池状态", test_pool_status()))
    results.append(("代理状态", test_proxy_status()))
    results.append(("API Keys 列表", test_list_keys()))
    
    # API 调用测试（API Key 认证）
    result = test_ranking()
    if result is not None:
        results.append(("排行榜", result))
    
    result = test_search()
    if result is not None:
        results.append(("搜索", result))
    
    result = test_illust_detail()
    if result is not None:
        results.append(("插画详情", result))
    
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
