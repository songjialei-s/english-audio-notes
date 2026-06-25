# 项目说明 - 英语文档朗读助手

## 项目概述
一个微信小程序 + Python后端的项目，实现两个核心功能：
1. **听文档**：导入PDF → 提取文字 → TTS朗读
2. **录音转文字**：录音 → STT识别 → 显示文字

## 技术栈
- **前端**：微信小程序（WXML/WXSS/JS）
- **后端**：Python FastAPI
- **PDF提取**：PyMuPDF + RapidOCR（扫描件OCR）
- **TTS**：pyttsx3（本地离线）
- **STT**：MiMo V2.5-ASR + DeepSeek纠错

## 已完成的功能
- [x] PDF上传和文字提取（支持扫描件OCR）
- [x] 文字分段处理
- [x] TTS语音合成（pyttsx3）
- [x] 小程序播放器（上一段/下一段/播放暂停）
- [x] 录音功能（录音/暂停/继续/停止）
- [x] 录音转文字（MiMo V2.5-ASR + DeepSeek纠错）
- [x] 底部TabBar导航
- [x] AppID已配置：wxb73282644760b541

## 启动命令
```bash
# 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 启动后端
cd D:\english-audio-notes
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## 项目结构
```
english-audio-notes/
├── pdf模块.py              # PDF提取（文字+OCR）
├── requirements.txt
├── backend/
│   ├── main.py             # FastAPI 3个接口：/upload /transcribe /tts
│   ├── pdf_parser.py       # 文字分段
│   ├── volcano_llm.py      # DeepSeek LLM纠错
│   ├── tts.py              # pyttsx3语音合成
│   └── stt.py              # MiMo V2.5-ASR语音识别
├── miniprogram/
│   ├── pages/index/        # 听文档页
│   ├── pages/player/       # 播放页
│   └── pages/record/       # 录音转文字页
└── storage/                # 临时文件（不用备份）
```

## 已知问题
- pyttsx3在Windows上使用SAPI5引擎，音质一般
- OCR处理大PDF较慢（已限制为前1页）
- MiMo ASR API需要网络连接
- 需要开启代理/VPN才能推送到GitHub

## GitHub
- 仓库：https://github.com/songjialei-s/english-audio-notes
- 用户名：songjialei-s
