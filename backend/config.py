"""配置文件 - 从 .env 加载环境变量"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv(Path(__file__).parent.parent / ".env")

# StepFun ASR
STEP_API_KEY = os.getenv("STEP_API_KEY", "")
STEP_BASE_URL = "https://api.stepfun.com"

# DeepSeek
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# 火山引擎 OCR
VOLCENGINE_API_KEY = os.getenv("VOLCENGINE_API_KEY", "")
VOLCENGINE_BASE_URL = "https://ark.cn-beijing.volces.com/api/coding/v3"

# 存储目录
BASE_DIR = Path(__file__).parent.parent
STORAGE_DIR = BASE_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
AUDIO_DIR = STORAGE_DIR / "audio"
RECORD_DIR = STORAGE_DIR / "records"
TEMP_DIR = STORAGE_DIR / "temp_chunks"

# 确保目录存在
for d in [UPLOAD_DIR, AUDIO_DIR, RECORD_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 音频处理参数
MAX_BASE64_SIZE = 10 * 1024 * 1024  # base64 最大大小 10MB
CHUNK_SECONDS = 10 * 60  # 分片时长 10 分钟

# 视频格式
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.m4v', '.3gp'}

# TTS 声音映射
VOICES = {
    "zh-female": "zh-CN-XiaoxiaoNeural",
    "zh-male": "zh-CN-YunxiNeural",
    "en-us-female": "en-US-JennyNeural",
    "en-us-male": "en-US-GuyNeural",
    "en-gb-female": "en-GB-SoniaNeural",
    "en-gb-male": "en-GB-RyanNeural",
}
