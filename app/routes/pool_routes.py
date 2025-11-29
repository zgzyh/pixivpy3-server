from flask import request, jsonify
from app.routes import api_bp
from app.auth import require_auth
from app.pool import pool
from app.config import config

@api_bp.route("/pool/status", methods=["GET"])
@require_auth
def pool_status():
    """查看账号池状态"""
    return jsonify({
        "strategy": config.lb_strategy,
        "accounts": pool.status()
    })

@api_bp.route("/pool/add", methods=["POST"])
@require_auth
def add_account():
    """动态添加账号"""
    data = request.get_json() or {}
    token = data.get("refresh_token")
    name = data.get("name")
    if not token:
        return jsonify({"error": "refresh_token required"}), 400
    if pool.add_account(token, name):
        return jsonify({"success": True, "total": len(pool.accounts)})
    return jsonify({"error": "auth failed"}), 400

@api_bp.route("/pool/remove", methods=["POST"])
@require_auth
def remove_account():
    """移除账号"""
    data = request.get_json() or {}
    name = data.get("name")
    if not name:
        return jsonify({"error": "name required"}), 400
    pool.remove_account(name)
    return jsonify({"success": True, "total": len(pool.accounts)})

@api_bp.route("/config/reload", methods=["POST"])
@require_auth
def reload_config():
    """重新加载配置"""
    try:
        config.reload()
        # 更新代理设置
        pool.update_proxy()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route("/proxy/update", methods=["POST"])
@require_auth
def update_proxy():
    """更新代理设置"""
    try:
        pool.update_proxy()
        proxy_cfg = config._data.get("proxy", {})
        return jsonify({
            "success": True,
            "enabled": proxy_cfg.get("enabled", False),
            "http": proxy_cfg.get("http", ""),
            "https": proxy_cfg.get("https", "")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route("/proxy/status", methods=["GET"])
@require_auth
def proxy_status():
    """查看代理状态"""
    proxy_cfg = config._data.get("proxy", {})
    return jsonify({
        "enabled": proxy_cfg.get("enabled", False),
        "http": proxy_cfg.get("http", ""),
        "https": proxy_cfg.get("https", "")
    })

@api_bp.route("/proxy/set", methods=["POST"])
@require_auth
def set_proxy():
    """设置代理并保存到 config.yaml"""
    data = request.get_json() or {}
    enabled = data.get("enabled", False)
    http_proxy = data.get("http", "")
    https_proxy = data.get("https", "") or http_proxy
    
    # 保存到 config.yaml
    config.set_proxy(enabled, http_proxy, https_proxy)
    
    # 更新所有账号的代理
    pool.update_proxy()
    
    return jsonify({
        "success": True,
        "enabled": enabled,
        "http": http_proxy,
        "https": https_proxy
    })

@api_bp.route("/pool/refresh/<name>", methods=["POST"])
@require_auth
def refresh_account(name):
    """刷新指定账号的 token"""
    if pool.refresh_account(name):
        return jsonify({"success": True})
    return jsonify({"error": "refresh failed"}), 400

@api_bp.route("/pool/login", methods=["POST"])
@require_auth
def gppt_login():
    """
    交互式 GPPT 登录 - 打开浏览器让用户直接在 Pixiv 页面登录
    不需要填写账号密码，自动使用全局代理
    若用户未填写 Account Name，使用登录后的账户名
    """
    from app.gppt_auth import gppt_auth, GPPT_AVAILABLE
    if not GPPT_AVAILABLE:
        return jsonify({"error": "gppt not installed, run: pip install gppt"}), 400
    
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    
    # 自动使用全局代理设置
    proxy_cfg = config._data.get("proxy", {})
    proxy = None
    if proxy_cfg.get("enabled") and proxy_cfg.get("http"):
        proxy = {"server": proxy_cfg.get("http")}
    
    print(f"[GPPT] Starting interactive login, proxy: {proxy}")
    
    try:
        # 调用交互式登录，打开浏览器让用户登录
        result = gppt_auth.login_interactive(proxy=proxy)
        
        # 解包返回值（token, error, user_account）
        if len(result) == 3:
            token, err, user_account = result
        else:
            token, err = result
            user_account = None
        
        print(f"[GPPT] Login result - token: {'obtained' if token else 'none'}, error: {err}, user: {user_account}")
        
        if token:
            # 优先使用用户填写的名称，否则使用登录账户名
            account_name = name or user_account or f"account_{len(pool.accounts)}"
            if pool.add_account(refresh_token=token, name=account_name):
                return jsonify({"success": True, "total": len(pool.accounts), "name": account_name})
            return jsonify({"error": "pixiv auth failed after gppt login"}), 400
        
        return jsonify({"error": err or "Login cancelled or failed"}), 400
    except Exception as e:
        print(f"[GPPT] Exception: {e}")
        return jsonify({"error": str(e)}), 400
