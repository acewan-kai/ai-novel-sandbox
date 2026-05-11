"""
配置文件 - PoC 沙盒引擎配置
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 从 .env 文件加载环境变量
_env_file = PROJECT_ROOT / ".env"
if _env_file.exists():
    with open(_env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())

# API配置
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = os.environ.get("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

# 启用模拟模式（当没有API密钥时自动启用）
MOCK_MODE = not bool(DEEPSEEK_API_KEY)

# LLM配置
LLM_CONFIG = {
    "temperature": 0.8,  # 创意性较高
    "max_tokens": 300,
    "top_p": 0.9,
}

# 模拟配置
SIMULATION_CONFIG = {
    "total_turns": 100,  # 运行回合数
    "turns_per_day": 12,  # 12回合 = 1天（每回合模拟6小时）
    "concurrent_npcs": True,  # 是否并发执行NPC动作
    "max_retry": 3,  # API调用最大重试次数
    "retry_delay": 2,  # 重试延迟（秒）
}

# 世界定义路径
WORLD_CONFIG_PATH = PROJECT_ROOT / "world" / "world.yaml"
NPC_CONFIG_PATH = PROJECT_ROOT / "world" / "npcs.yaml"

# 日志配置
LOG_DIR = PROJECT_ROOT / "logs"
EVENT_LOG_FILE = LOG_DIR / "events.jsonl"
METRICS_FILE = LOG_DIR / "metrics.json"

# 验收标准
VALIDATION_CRITERIA = {
    "required": {
        "all_npcs_survived_100_turns": True,  # 10个NPC全部存活运行100回合
        "at_least_3_unscripted_interactions": True,  # 至少3个非预设的跨角色互动
        "at_least_1_storylike_moment": True,  # 至少1个互动具有故事感
    },
    "optional": {
        "single_turn_delay_under_15s": 15.0,  # 单回合延迟 < 15秒
    }
}

def ensure_dirs():
    """确保必要的目录存在"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
