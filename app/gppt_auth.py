"""
GPPT (get-pixiv-token) 集成模块
用于自动获取和刷新 Pixiv refresh_token
"""
import json
import os
import re
import secrets
import hashlib
import base64
import urllib.parse
from pathlib import Path

try:
    from gppt import GetPixivToken
    GPPT_AVAILABLE = True
except ImportError:
    GPPT_AVAILABLE = False
    print("[GPPT] gppt not installed, run: pip install gppt")

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("[GPPT] playwright not installed, run: pip install playwright && playwright install chromium")


def get_proxy_config():
    """从配置获取代理设置"""
    try:
        from app.config import config
        proxy_cfg = config._data.get("proxy", {})
        if not proxy_cfg.get("enabled", False):
            return None
        
        http_proxy = proxy_cfg.get("http", "")
        https_proxy = proxy_cfg.get("https", "") or http_proxy
        
        if http_proxy:
            return {"server": http_proxy}
        return None
    except:
        return None


class GPPTAuth:
    """GPPT 认证管理"""
    
    def __init__(self, token_cache_dir="./tokens"):
        self.cache_dir = Path(token_cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _cache_path(self, username):
        return self.cache_dir / f"{username}.json"
    
    def _save_token(self, username, token_data):
        """缓存 token"""
        with open(self._cache_path(username), "w") as f:
            json.dump(token_data, f)
    
    def _load_token(self, username):
        """加载缓存的 token"""
        path = self._cache_path(username)
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
        return None
    
    def _set_proxy_env(self, proxy):
        """设置代理环境变量"""
        if proxy and proxy.get("server"):
            proxy_url = proxy["server"]
            os.environ["HTTP_PROXY"] = proxy_url
            os.environ["HTTPS_PROXY"] = proxy_url
            os.environ["http_proxy"] = proxy_url
            os.environ["https_proxy"] = proxy_url
            print(f"[GPPT] Proxy env set: {proxy_url}")
    
    def _clear_proxy_env(self):
        """清除代理环境变量"""
        for key in ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]:
            os.environ.pop(key, None)

    def login_interactive(self, proxy=None, timeout_seconds=600):
        """
        交互式登录 - 使用原生 gppt login，打开浏览器让用户登录
        timeout_seconds: 超时时间（秒），默认10分钟
        """
        if not GPPT_AVAILABLE:
            return None, "gppt not installed"
        
        proxy = proxy or get_proxy_config()
        print(f"[GPPT] Starting interactive login with gppt, proxy: {proxy}, timeout: {timeout_seconds}s")
        
        try:
            # 直接修改 gppt.utils.PROXIES 来设置代理
            import gppt.utils
            if proxy:
                proxy_url = proxy["server"]
                gppt.utils.PROXIES = {"http": proxy_url, "https": proxy_url, "all": proxy_url}
                print(f"[GPPT] Set gppt.utils.PROXIES: {gppt.utils.PROXIES}")
            else:
                gppt.utils.PROXIES = {}
            
            # Monkey patch gppt 的 __wait_for_redirect 方法来延长超时
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.common.exceptions import TimeoutException
            from gppt.consts import REDIRECT_URI
            
            def patched_wait_for_redirect(self_gppt):
                try:
                    WebDriverWait(self_gppt.driver, timeout_seconds).until(
                        EC.url_matches(f"^{REDIRECT_URI}")
                    )
                except TimeoutException as err:
                    self_gppt.driver.close()
                    msg = "Login timeout. Please try again."
                    raise ValueError(msg) from err
            
            # 应用 monkey patch
            GetPixivToken._GetPixivToken__wait_for_redirect = patched_wait_for_redirect
            
            g = GetPixivToken()
            # 原生调用 gppt login，不传用户名密码，让用户在浏览器中登录
            res = g.login(headless=False)
            print(f"[GPPT] Login response: {res}")
            
            if res and "refresh_token" in res:
                # 获取用户账户名（邮箱/用户名）
                user_account = res.get("user", {}).get("account", "")
                self._save_token(user_account or "interactive_user", res)
                # 返回 token 和用户账户名
                return res["refresh_token"], None, user_account
            return None, f"Login failed: {res}", None
        except Exception as e:
            print(f"[GPPT] Login exception: {e}")
            return None, str(e), None

    def login_with_credentials(self, username, password, proxy=None):
        """使用用户名密码登录（显示浏览器，需要人机验证）"""
        if not GPPT_AVAILABLE:
            return None, "gppt not installed"
        try:
            proxy = proxy or get_proxy_config()
            print(f"[GPPT] Starting browser login for {username}, proxy: {proxy}")
            self._set_proxy_env(proxy)
            g = GetPixivToken()
            res = g.login(headless=False, username=username, password=password)
            print(f"[GPPT] Login response: {res}")
            if res and "refresh_token" in res:
                self._save_token(username, res)
                return res["refresh_token"], None
            return None, f"Login failed: {res}"
        except Exception as e:
            print(f"[GPPT] Login exception: {e}")
            return None, str(e)
        finally:
            self._clear_proxy_env()

    def login_headless(self, username, password, proxy=None):
        """无头浏览器登录"""
        if not GPPT_AVAILABLE:
            return None, "gppt not installed"
        try:
            proxy = proxy or get_proxy_config()
            print(f"[GPPT] Starting headless login for {username}, proxy: {proxy}")
            self._set_proxy_env(proxy)
            g = GetPixivToken()
            res = g.login(headless=True, username=username, password=password)
            print(f"[GPPT] Headless login response: {res}")
            if res and "refresh_token" in res:
                self._save_token(username, res)
                return res["refresh_token"], None
            return None, f"Headless login failed: {res}"
        except Exception as e:
            print(f"[GPPT] Headless login exception: {e}")
            return None, str(e)
        finally:
            self._clear_proxy_env()
    
    def refresh_token(self, refresh_token):
        """刷新 token"""
        if not GPPT_AVAILABLE:
            return None, "gppt not installed"
        try:
            g = GetPixivToken()
            res = g.refresh(refresh_token)
            if res and "refresh_token" in res:
                return res["refresh_token"], None
            return None, "Refresh failed"
        except Exception as e:
            return None, str(e)
    
    def get_cached_token(self, username):
        """获取缓存的 token"""
        data = self._load_token(username)
        if data:
            return data.get("refresh_token")
        return None

gppt_auth = GPPTAuth()
