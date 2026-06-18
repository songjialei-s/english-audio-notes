import requests

API_KEY = "sk-6d156d535c3c467a8b1cb40859b0dfc5"
BASE_URL = "https://api.deepseek.com"


def correct_with_llm(raw_text: str) -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""你是英语笔记纠错助手。OCR识别了手写英语笔记。

【核心规则】
1. 同义词用 / 连接在同一行：triumph/victory 胜利
2. 词组必须完整保留，包括with/sth/to等搭配词：
   - correlate with sth 与...相互关联
   - spur to sth 对...的激励
   - amount to sth 等同于
   - tangle with 与...争论
   - even though 尽管
   - by chance 偶然
3. sth = something, sb = somebody, 保留不翻译
4. 纠正拼写：victoru→victory, lawver→lawyer
5. 删除乱码
6. 格式："英文 中文意思"

【示例】
输入：correlate with sth 与..相关
输出：correlate with sth 与..相互关联

输入：victoru胜利 triumph/u
输出：triumph/victory 胜利

【OCR内容】
{raw_text}

【输出】"""

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 4096,
        "temperature": 0.1
    }

    try:
        resp = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[LLM Error: {e}]"
