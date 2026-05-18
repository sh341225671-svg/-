"""配置管理"""
import json, os

DEEPSEEK_AUTH_PATH = os.path.expanduser(
    "~/.local/share/opencode/auth.json"
)

def get_deepseek_key() -> str:
    """读取 DeepSeek API key"""
    if os.path.exists(DEEPSEEK_AUTH_PATH):
        try:
            with open(DEEPSEEK_AUTH_PATH) as f:
                auth = json.load(f)
            for key, val in auth.items():
                if "deepseek" in key and isinstance(val, dict) and val.get("key"):
                    return val["key"]
        except Exception:
            pass
    return os.environ.get("DEEPSEEK_API_KEY", "")

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
