import yaml
import os

class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config_path = os.getenv("CONFIG_PATH", "config.yaml")
            cls._instance._load()
        return cls._instance
    
    def _load(self):
        with open(self._config_path, "r", encoding="utf-8") as f:
            self._data = yaml.safe_load(f)
    
    def save(self):
        """保存配置到文件"""
        with open(self._config_path, "w", encoding="utf-8") as f:
            yaml.dump(self._data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"[Config] Saved to {self._config_path}")
    
    def reload(self):
        self._load()
    
    @property
    def server(self):
        return self._data.get("server", {})
    
    @property
    def auth_token(self):
        return self._data.get("auth", {}).get("token", "")
    
    @property
    def lb_strategy(self):
        return self._data.get("load_balance", {}).get("strategy", "round_robin")
    
    @property
    def pixiv_accounts(self):
        return self._data.get("pixiv_accounts", []) or []
    
    def add_account(self, name, refresh_token, username=None):
        """添加账号到配置"""
        if "pixiv_accounts" not in self._data or self._data["pixiv_accounts"] is None:
            self._data["pixiv_accounts"] = []
        
        # 检查是否已存在
        for acc in self._data["pixiv_accounts"]:
            if acc.get("name") == name:
                acc["refresh_token"] = refresh_token
                if username:
                    acc["username"] = username
                self.save()
                return
        
        # 添加新账号
        self._data["pixiv_accounts"].append({
            "name": name,
            "refresh_token": refresh_token,
            "enabled": True
        })
        self.save()
    
    def remove_account(self, name):
        """从配置删除账号"""
        if "pixiv_accounts" not in self._data or self._data["pixiv_accounts"] is None:
            return
        self._data["pixiv_accounts"] = [
            acc for acc in self._data["pixiv_accounts"] if acc.get("name") != name
        ]
        self.save()
    
    def set_proxy(self, enabled, http_proxy, https_proxy=None):
        """设置代理配置"""
        if "proxy" not in self._data:
            self._data["proxy"] = {}
        self._data["proxy"]["enabled"] = enabled
        self._data["proxy"]["http"] = http_proxy
        self._data["proxy"]["https"] = https_proxy or http_proxy
        self.save()

config = Config()
