"""火山引擎 OCR 识别模块"""
import base64
import requests

from backend.config import VOLCENGINE_API_KEY, VOLCENGINE_BASE_URL


def ocr_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    headers = {
        "Authorization": f"Bearer {VOLCENGINE_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-v4-pro",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请识别这张图片中的所有文字，保持原始格式和换行。如果是手写英文笔记，保留单词之间的/分隔符。只输出识别到的文字，不要添加任何解释。"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 4096
    }

    try:
        resp = requests.post(
            f"{VOLCENGINE_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[OCR Error: {e}]"
