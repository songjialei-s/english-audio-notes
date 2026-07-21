# English Audio Notes — 文档朗读助手

> 微信小程序 + FastAPI 后端。PDF 朗读 / 录音转文字 / 视频转文字。

## 架构

```
miniprogram/ (微信小程序前端)
    │  wx.uploadFile
    ▼
backend/main.py (FastAPI, 8 routes)
    ├── pdf_module.py    → PyMuPDF → RapidOCR → LLM纠错
    ├── pdf_parser.py    → 文本分段
    ├── tts.py           → edge-tts 语音合成
    ├── stt.py           → FFmpeg处理 → StepFun ASR → DeepSeek纠错
    ├── volcano_llm.py   → DeepSeek LLM (OCR纠错专用Prompt)
    ├── volcano_ocr.py   → 火山引擎 OCR (备用)
    └── text_corrector.py → 本地纠错 (备用)
```

## 环境变量

| 变量 | 用途 |
|------|------|
| `STEP_API_KEY` | StepFun ASR 语音识别 |
| `DEEPSEEK_API_KEY` | DeepSeek LLM 纠错 |
| `VOLCENGINE_API_KEY` | 火山引擎 OCR（备用） |

配置定义在 `backend/config.py`，从项目根 `.env` 加载。

## 代码规则

1. **每个模块独立可调试** — 保留 `if __name__ == "__main__"` 入口
2. **降级不崩溃** — 外部服务失败返回哨兵字符串（`[ASR返回为空]`、`[LLM Error: ...]`），不抛异常
3. **LLM 调用统一参数** — `temperature=0.1`，有 timeout，catch 所有 Exception
4. **中文注释解释"为什么"**
5. **文件操作有清理** — 临时分片、FFmpeg 中间产物用完即删
6. **小程序后端接口精简** — 不分页、不鉴权、不统一响应包装（只有小程序自己调）

## 红线

- **不能** 把 `[ASR返回为空]` 等哨兵字符串改成抛异常（前端依赖字符串判断）
- **不能** 删 `_run_async` 的逻辑（edge-tts 在已运行的事件循环里会死锁）
- **不能** 把 FFmpeg 路径硬编码（通过 `imageio_ffmpeg` 获取，失败则跳过 FFmpeg 相关功能）
- **不能** 在 TTS 文本清洗前移除正则（中英文字间空格是发音需要）
- **不能** 给 `/upload` 和 `/transcribe` 加鉴权（小程序直连，无登录体系）

## 常用命令

```bash
# 启动后端
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 单独测试 PDF 提取
python -m backend.pdf_module test.pdf

# Docker 部署
docker build -t english-audio-notes .
docker run -p 8000:8000 --env-file .env english-audio-notes
```

## 前端

- 小程序入口：`miniprogram/app.js`（`baseUrl` 指向后端）
- 页面：`pages/index/`（听文档）、`pages/player/`（播放器）、`pages/record/`（录音转文字）
- 数据存储：`wx.getStorageSync`（笔记列表 + 转写历史，上限 100 条）
- 无数据库——不需要。

## 第三方服务

| 服务 | 调用位置 | 备注 |
|------|---------|------|
| StepFun ASR | `stt.py:_step_asr` | SSE 流式响应，需解析 `transcript.text.done` |
| DeepSeek | `stt.py:_deepseek_correct` + `volcano_llm.py:correct_with_llm` | 两个不同 Prompt，OCR纠错给示例，ASR纠错不给 |
| edge-tts | `tts.py:_generate_async` | 异步，需 `_run_async` 处理事件循环 |
| RapidOCR | `pdf_module.py:ocr_pdf` | 离线 OCR，模块级单例 |
