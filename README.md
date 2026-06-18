# English Audio Notes

将英语笔记PDF转为语音，随时随地听。

## 使用

```bash
# 安装依赖
pip install -r requirements.txt

# 启动后端
uvicorn backend.main:app --reload

# 上传PDF测试
curl -X POST -F "file=@笔记.pdf" http://localhost:8000/upload
```

## 项目结构

```
├── pdf模块.py        # PDF文字提取
├── backend/
│   ├── main.py       # API服务
│   ├── pdf_parser.py # 分段处理
│   └── tts.py        # 语音合成
├── storage/          # 上传PDF + 生成音频
└── requirements.txt
```
