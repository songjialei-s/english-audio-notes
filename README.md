# 文档朗读助手

导入PDF听文档，录音转文字。

## 功能

- **听文档**：上传PDF → 自动提取文字 → TTS语音朗读
- **录音转文字**：录音 → 语音识别 → 显示文字
- 支持扫描件PDF（OCR识别）
- 小程序后台播放

## 版本记录

### v1.0 - 基础版
- PDF文字提取（PyMuPDF）
- 文字分段处理
- TTS语音合成（pyttsx3）
- 微信小程序播放器（上一段/下一段/播放暂停）

### v1.1 - 录音转文字
- 录音功能（录音/暂停/继续/停止）
- 录音转文字（SpeechRecognition多语言支持）
- 底部TabBar导航

### v1.2 - 扫描件支持
- RapidOCR扫描件PDF识别
- 上传取消按钮
- README版本记录

### v1.3 - LLM纠错
- DeepSeek API智能纠错（手写英文识别修正）
- 词组格式优化（correlate with sth等保持完整）
- 本地纠错模块（备用方案）

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 启动后端
cd D:\english-audio-notes
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

小程序用微信开发者工具打开 `miniprogram/` 文件夹。

## 技术栈

| 模块 | 技术 |
|------|------|
| 前端 | 微信小程序 |
| 后端 | Python FastAPI |
| PDF提取 | PyMuPDF + RapidOCR |
| LLM纠错 | DeepSeek API |
| TTS | pyttsx3 |
| STT | SpeechRecognition |

## 项目结构

```
english-audio-notes/
├── pdf模块.py              # PDF提取（文字+OCR+LLM纠错）
├── backend/
│   ├── main.py             # API服务
│   ├── pdf_parser.py       # 文字分段
│   ├── volcano_llm.py      # DeepSeek LLM纠错
│   ├── text_corrector.py   # 本地纠错（备用）
│   ├── tts.py              # 文字转语音
│   └── stt.py              # 语音转文字
├── miniprogram/
│   ├── pages/index/        # 听文档
│   ├── pages/player/       # 播放器
│   └── pages/record/       # 录音转文字
└── requirements.txt
```
